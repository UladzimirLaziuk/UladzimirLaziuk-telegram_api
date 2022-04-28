from django.urls import path

from . import views

urlpatterns = [
    path('telegramwebhook/', views.telegram_api, name='telegram_api'),
]