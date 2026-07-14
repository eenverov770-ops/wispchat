from django.db import models
from django.contrib.auth.models import User

class ChatRoom(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    avatar = models.ImageField(upload_to='chat_avatars/', blank=True, null=True, verbose_name="Аватар")
    description = models.CharField(max_length=255, blank=True, default='', verbose_name="Описание")
    is_group = models.BooleanField(default=False, verbose_name="Группа?")
    members = models.ManyToManyField(User, related_name='chat_rooms', verbose_name="Участники")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_chats', verbose_name="Создатель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    slow_mode = models.IntegerField(default=0, verbose_name="Задержка между сообщениями (сек)")

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name="Чат")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    content = models.TextField(verbose_name="Текст")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано?")
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name="Ответ на")
    likes = models.ManyToManyField(User, related_name='liked_messages', blank=True, verbose_name="Лайки")
    # Исчезающие сообщения
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Исчезает в")
    # Реакции
    reactions = models.JSONField(default=dict, blank=True, verbose_name="Реакции")

    def __str__(self):
        return f"{self.author.username}: {self.content[:30]}"

class Friend(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends')
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_of')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'friend')

    def __str__(self):
        return f"{self.user.username} - {self.friend.username}"

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.from_user} → {self.to_user}"

class Sticker(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    image = models.ImageField(upload_to='stickers/', verbose_name="Изображение")
    pack = models.CharField(max_length=50, default='default', verbose_name="Пак")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_stickers', verbose_name="Создатель")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    status = models.CharField(max_length=100, blank=True, default='', verbose_name="Статус")
    last_seen = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False)
    is_creator = models.BooleanField(default=False, verbose_name="Основатель")
    status_emoji = models.CharField(max_length=10, default='🟢', verbose_name="Эмодзи-статус")
    qr_code = models.TextField(blank=True, null=True, verbose_name="QR-код")

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"

class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.action} ({self.timestamp})"

class Game(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='games')
    game_type = models.CharField(max_length=50, default='tic_tac_toe')
    state = models.JSONField(default=dict)
    players = models.ManyToManyField(User, related_name='games')
    current_turn = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='current_games')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_games')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.game_type} - {self.chat_room.name}"