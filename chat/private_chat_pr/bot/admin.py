from django.contrib import admin

from .models import Chat, Client, Message, Obscenity


class ChatAdmin(admin.ModelAdmin):
    list_display = ['title']


class ClientAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name')


class MessageAdmin(admin.ModelAdmin):
    list_display = ('date', 'chat', 'sender', 'receiver', 'text')
    list_filter = ('date', 'chat', 'sender')


admin.site.register(Client, ClientAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Obscenity)
