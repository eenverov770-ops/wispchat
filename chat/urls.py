from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from chat.admin import admin_site 

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('search/', views.search_users_view, name='search'),
    path('profile/', views.profile_view, name='profile'),
    path('user/<int:user_id>/', views.user_profile_view, name='user_profile'),
    path('add_friend/<int:user_id>/', views.add_friend_view, name='add_friend'),
    path('send_request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('accept_request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend_requests/', views.friend_requests_view, name='friend_requests'),
    path('create_chat/', views.create_chat_view, name='create_chat'),
    path('chat/<int:chat_id>/', views.chat_detail_view, name='chat_detail'),
    path('send_message/<int:chat_id>/', views.send_message_view, name='send_message'),
    path('get_new_messages/<int:chat_id>/', views.get_new_messages, name='get_new_messages'),
    path('start_chat/<int:friend_id>/', views.start_private_chat, name='start_private_chat'),
    path('delete_friend/<int:friend_id>/', views.delete_friend, name='delete_friend'),
    path('delete_chat/<int:chat_id>/', views.delete_chat, name='delete_chat'),
    path('activity/', views.activity_view, name='activity'),
    path('clear_activity/', views.clear_activity, name='clear_activity'),
    path('forward/<int:message_id>/', views.forward_message_view, name='forward_message'),
    path('like/<int:message_id>/', views.like_message, name='like_message'),
    path('delete_message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('add_reaction/<int:message_id>/', views.add_reaction, name='add_reaction'),
    path('start_game/<int:chat_id>/', views.start_game, name='start_game'),
    path('make_move/<int:game_id>/', views.make_move, name='make_move'),
    path('game_status/<int:game_id>/', views.game_status, name='game_status'),
    path('qr_code/', views.qr_code_view, name='qr_code'),
    path('add_by_qr/', views.add_by_qr, name='add_by_qr'),
    path('create_sticker/', views.create_sticker_pack_view, name='create_sticker_pack'),
    path('typing/<int:chat_id>/', views.typing_view, name='typing'),
    path('stop_typing/<int:chat_id>/', views.stop_typing_view, name='stop_typing'),
    # Групповые чаты
    path('add_member/<int:chat_id>/', views.add_member, name='add_member'),
    path('remove_member/<int:chat_id>/<int:user_id>/', views.remove_member, name='remove_member'),
    path('chat_settings/<int:chat_id>/', views.chat_settings_view, name='chat_settings'),
    path('', views.home_view, name='home'),
    path('upload_file/<int:chat_id>/', views.upload_file, name='upload_file'),
    path('get_online_members/<int:chat_id>/', views.get_online_members, name='get_online_members'),
path('admin/', admin_site.urls),  # <-- кастомная админка
    path('', include('chat.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)