import logging
from urllib.parse import urlparse

from django.apps import AppConfig
from django.conf import settings
from django.urls import reverse_lazy

import requests
from pyngrok import ngrok

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot.logger')


class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot'

    if settings.LOCAL_DEVELOPMENT:
        # create tunnel from somewhere to local server
        https_tunnel = ngrok.connect(
            addr='8000',
            bind_tls=True
        )
        public_url = https_tunnel.public_url
        # add new temporary host to allowed hosts
        settings.ALLOWED_HOSTS.append(urlparse(public_url).netloc)
        public_url += '/telegramwebhook/'
    else:
        public_url = settings.TELEGRAM_WEBHOOK_URL

    print(public_url)
    response = requests.post(
        url=settings.TELEGRAM_API_URL + 'setWebhook',
        json={
            'url': public_url,  # settings.TELEGRAM_WEBHOOK_URL,
        },
    )
    if settings.DEBUG:
        logger.info(f'Telegram setWebhook response {response}')
