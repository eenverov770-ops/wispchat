from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from .models import ChatRoom, Message, Friend, Sticker, Activity
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

class WispAdminSite(AdminSite):
    site_header = 'WispChat — Админ-панель'
    site_title = 'WispChat Admin'
    index_title = '📊 Панель управления'
    
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        # Добавляем кастомный дашборд
        return app_list
    
    def index(self, request, extra_context=None):
        # Статистика
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        blocked_users = total_users - active_users
        
        total_chats = ChatRoom.objects.count()
        group_chats = ChatRoom.objects.filter(is_group=True).count()
        private_chats = total_chats - group_chats
        
        total_messages = Message.objects.count()
        messages_today = Message.objects.filter(timestamp__date=timezone.now().date()).count()
        
        total_friends = Friend.objects.count()
        total_stickers = Sticker.objects.count()
        
        # Последние активности
        recent_activities = Activity.objects.order_by('-timestamp')[:10]
        
        # Активные пользователи (за последние 24 часа)
        yesterday = timezone.now() - timedelta(days=1)
        active_users_24h = Activity.objects.filter(timestamp__gte=yesterday).values('user').distinct().count()
        
        extra_context = {
            'total_users': total_users,
            'active_users': active_users,
            'blocked_users': blocked_users,
            'total_chats': total_chats,
            'group_chats': group_chats,
            'private_chats': private_chats,
            'total_messages': total_messages,
            'messages_today': messages_today,
            'total_friends': total_friends,
            'total_stickers': total_stickers,
            'active_users_24h': active_users_24h,
            'recent_activities': recent_activities,
        }
        return super().index(request, extra_context=extra_context)

# Заменяем стандартную админку
admin_site = WispAdminSite()