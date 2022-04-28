#!/bin/bash

gunicorn --env DJANGO_SETTINGS_MODULE=private_chat_pr.settings private_chat_pr.wsgi
