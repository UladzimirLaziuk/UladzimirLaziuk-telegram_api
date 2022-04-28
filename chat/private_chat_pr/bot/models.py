import requests
import uuid as uuid
import json

from django.conf import settings
from django.db import models
from base64 import urlsafe_b64encode

from .apps import logger



class Chat(models.Model):
    title = models.CharField(max_length=200)

    def __str__(self):
        return f'Chat {self.id}: {self.title}'


    class Meta:
        verbose_name = "чат"
        verbose_name_plural = "чаты"


class Client(models.Model):
    username = models.CharField(max_length=200)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    ID_CRM = models.CharField(max_length=200, unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    tg_chat_id = models.PositiveIntegerField(unique=True)
    tg_user_id = models.PositiveIntegerField(unique=True)
    chats = models.ManyToManyField(Chat, related_name="clients")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    current_chat = models.ForeignKey(Chat, on_delete=models.CASCADE)

    CHANGE_CHAT_LABEL = "Выбор чата"

    class Keyboard(models.IntegerChoices):
        NO_KBD = 0
        CHANGE_CHAT = 1
        CHATS_LIST = 2

    keyboard_status = models.IntegerField(choices=Keyboard.choices, default=Keyboard.CHANGE_CHAT)

    class Meta:
        verbose_name = "клиент"
        verbose_name_plural = "клиенты"

    def __str__(self):
        return f'{self.username} ({self.first_name} {self.last_name})'

    def get_keyboard(self):
        if self.keyboard_status == Client.Keyboard.NO_KBD:
            return None
        elif self.keyboard_status == Client.Keyboard.CHANGE_CHAT:
            payload = {
                'new_keyboard_status': Client.Keyboard.CHATS_LIST,
            }
            kbd_btn1 = {
                'text': Client.CHANGE_CHAT_LABEL,
                'callback_data': json.dumps(payload),
            }
            kbd_row1 = [kbd_btn1]
            kbd = [kbd_row1]
            inline_kbd = {'inline_keyboard': kbd}
            return json.dumps(inline_kbd)
        elif self.keyboard_status == Client.Keyboard.CHATS_LIST:
            kbd = []
            for chat in self.chats.all():
                payload = {
                    'new_keyboard_status': Client.Keyboard.CHANGE_CHAT,
                    'new_chat_id': chat.id
                }
                kbd_btn = {
                    'text': str(chat),
                    'callback_data': json.dumps(payload),
                }
                kbd_row = [kbd_btn]
                kbd.append(kbd_row)
            inline_kbd = {'inline_keyboard': kbd}
            return json.dumps(inline_kbd)


class Message(models.Model):
    """if sender == receiver then this message is incoming, otherwise it is outgoing"""
    tg_msg_id = models.PositiveIntegerField(null=True, blank=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='sender')
    receiver = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='receiver')
    date = models.DateTimeField()
    text = models.TextField(max_length=4096)
    raw_data = models.JSONField(default=dict)

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"
        ordering = ['-date']

    def __str__(self):
        return self.text[:16]

    def save(self, *args, **kwargs):
        self.send_message()
        super().save(*args, **kwargs)

    def send_message(self):
        if not self.tg_msg_id:
            message_text = [
                '<pre>Chat:</pre> <b><i>' + self.chat.title + '</i></b>',
                '<pre>From:</pre> <b><i>' + self.sender.username + '</i></b>',
                '',
                self.text
            ]
            param = {'chat_id': str(self.receiver.tg_chat_id),
                     'parse_mode': 'HTML',
                     'text': '\n'.join(message_text)
                     }
            keyboard = self.sender.get_keyboard()
            if keyboard is not None:
                param['reply_markup'] = keyboard
            response = requests.post(settings.TELEGRAM_API_URL + 'sendMessage', json=param)
            logger.info(response.json())
            result = response.json()['ok']
            if result:
                self.tg_msg_id = response.json()['result']['message_id']


class Obscenity(models.Model):
    item = models.CharField(max_length=20)
    
    def __str__(self):
        return f'{self.item}'
