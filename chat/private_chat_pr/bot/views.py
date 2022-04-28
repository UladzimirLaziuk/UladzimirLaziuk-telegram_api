from datetime import datetime
import json
import requests
from typing import Optional
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Message, Client, Chat
from .apps import logger


def get_client_by_tg_user_id(tg_user_id: int) -> Optional[Client]:
    """Return the Client corresponding to the Telegram User ID, or None if such Client does not exist

    User object in Telegram API https://core.telegram.org/bots/api#user"""

    try:
        client = Client.objects.get(tg_user_id=tg_user_id)
    except Client.DoesNotExist:
        return None
    except Client.MultipleObjectsReturned:
        # TODO Internal error in base - multiple clients with same tg_user_id
        raise
    else:
        return client


def first_message_from_new_client(request, tg_message):
    message_text: str = tg_message.get('text')
    tg_user = tg_message.get('from')
    tg_user_id: int = tg_user.get('id')
    if message_text.startswith('/start'):  # if command /start then check hash link
        uuid = message_text[len('/start '):]
        try:
            client = Client.objects.get(uuid=uuid)
        except Client.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        client.tg_user_id = tg_user_id
        client.tg_chat_id = tg_user_id
        client.save()
        return Response(status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


def process_message(request, tg_message):
    """Process Message object from Telegram API

    tg_message is Message object in Telegram API https://core.telegram.org/bots/api#message"""

    # tg_user is User object in Telegram API https://core.telegram.org/bots/api#user
    tg_user = tg_message.get('from')
    if tg_user is None:
        # TODO We received bad Message without User
        return Response(status=status.HTTP_400_BAD_REQUEST)
    tg_user_id: int = tg_user.get('id')
    sender = get_client_by_tg_user_id(tg_user_id)
    if sender is None:
        # first message from new client, we have to create new Client
        return first_message_from_new_client(request, tg_message)

    # we received text message from `old` client
    message_text: str = tg_message.get('text')

    # we parse Telegram Message
    tg_message_id: int = tg_message.get('message_id')
    tg_message_date: int = tg_message.get('date')  # Unix-time
    message_date = datetime.fromtimestamp(tg_message_date)

    received_message = Message.objects.create(
        tg_msg_id=tg_message_id,
        chat=sender.current_chat,
        sender=sender,
        receiver=sender,
        date=message_date,
        text=message_text
    )
    receiver_array = sender.current_chat.client_set.exclude(tg_user_id=tg_user_id)
    for receiver in receiver_array:
        posted_message = Message(
            tg_msg_id=None,
            chat=received_message.chat,
            sender=received_message.sender,
            receiver=receiver,
            date=received_message.date,
            text=received_message.text
        )
        posted_message.save()
    return Response(status=status.HTTP_201_CREATED)


def process_callback_query(request, tg_callback_query):
    """Process CallbackQuery object from Telegram API

    tg_callback_query is CallbackQuery https://core.telegram.org/bots/api#callbackquery"""

    # tg_user is User object in Telegram API https://core.telegram.org/bots/api#user
    tg_user = tg_callback_query.get('from')
    if tg_user is None:
        # We received bad CallbackQuery without User
        return Response(status=status.HTTP_400_BAD_REQUEST)
    tg_user_id: int = tg_user.get('id')
    sender = get_client_by_tg_user_id(tg_user_id)
    if sender is None:
        # We received bad CallbackQuery from new User
        return Response(status=status.HTTP_400_BAD_REQUEST)
    data: Optional[str] = tg_callback_query.get('data')
    if data is None:
        # We received bad CallbackQuery without data
        return Response(status=status.HTTP_400_BAD_REQUEST)

    payload = json.loads(data)
    # in payload can be different information

    # we have to change curren chat
    new_chat_id = payload.get('new_chat_id')
    if new_chat_id is not None:
        chat = Chat.objects.get(id=new_chat_id)
        sender.current_chat = chat
        sender.save()

    # we have to change inline keyboard
    new_keyboard_status = payload.get('new_keyboard_status')
    if new_keyboard_status is not None:
        sender.keyboard_status = new_keyboard_status
        sender.save()
        param = {'chat_id': str(sender.tg_chat_id),
                 'reply_markup': sender.get_keyboard(),
                 }
        # use editMessageReplyMarkup call to Telegram
        # https://core.telegram.org/bots/api#editmessagereplymarkup
        response = requests.post(settings.TELEGRAM_API_URL + 'editMessageReplyMarkup', json=param)

    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def telegram_api(request):
    """Process Update object from Telegram API"""

    if request.method == "POST":
        logger.info(request.data)
        # request.data is Update object in Telegram API https://core.telegram.org/bots/api#update
        # At most one of the optional parameters can be present in any given update.

        # At this moment we process only CallbackQuery and Message

        # CallbackQuery https://core.telegram.org/bots/api#callbackquery
        # button in inline keyboard was pressed
        tg_callback_query = request.data.get('callback_query')
        if tg_callback_query is not None:
            return process_callback_query(request, tg_callback_query)

        # Message https://core.telegram.org/bots/api#message
        # user send some text or command
        tg_message = request.data.get('message')
        if tg_message is not None:
            return process_message(request, tg_message)

        # TODO in Update is no suitable information
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
