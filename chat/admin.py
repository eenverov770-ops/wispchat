from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import ChatRoom, Message, Friend, FriendRequest, Sticker, UserProfile, Activity

# --- КАСТОМНЫЙ ADMIN SITE ---
class WispAdminSite(admin.AdminSite):
    site_header = 'WispChat — Админ-панель'
    site_title = 'WispChat Admin'
    index_title = '📊 Панель управления'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        return urls

    def each_context(self, request):
        context = super().each_context(request)
        context['theme'] = 'dark'
        return context

# Создаём экземпляр кастомной админки
admin_site = WispAdminSite(name='wispadmin')

# --- РЕГИСТРИРУЕМ МОДЕЛИ ---
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email')

admin_site.register(User, CustomUserAdmin)
admin_site.register(UserProfile)
admin_site.register(ChatRoom)
admin_site.register(Message)
admin_site.register(Friend)
admin_site.register(FriendRequest)
admin_site.register(Sticker)
admin_site.register(Activity)