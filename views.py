from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import hashlib
import json
from .models import Friend, ChatRoom, Message, Sticker, FriendRequest, UserProfile, Activity, Game
from .forms import ChatRoomForm

def log_activity(user, action):
    Activity.objects.create(user=user, action=action)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            log_activity(user, 'Зарегистрировался')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'chat/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_online = True
            profile.save()
            login(request, user)
            log_activity(user, 'Вошёл в систему')
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'chat/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.is_online = False
        profile.save()
        log_activity(request.user, 'Вышел из системы')
    logout(request)
    return redirect('login')

@login_required
def home_view(request):
    friends = Friend.objects.filter(user=request.user)
    chats = ChatRoom.objects.filter(members=request.user)
    
    for chat in chats:
        chat.unread_count = Message.objects.filter(
            room=chat,
            is_read=False
        ).exclude(author=request.user).count()
        
        if not chat.is_group:
            chat.other_user = chat.members.exclude(id=request.user.id).first()
        else:
            chat.other_user = None
    
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/home.html', {
        'friends': friends,
        'chats': chats,
        'theme': theme,
    })

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        username = request.POST.get('username')
        status = request.POST.get('status')
        avatar = request.FILES.get('avatar')
        status_emoji = request.POST.get('status_emoji')
        
        if username:
            request.user.username = username
            request.user.save()
        if status is not None:
            profile.status = status
        if avatar:
            profile.avatar = avatar
        if status_emoji:
            profile.status_emoji = status_emoji
        profile.save()
        log_activity(request.user, 'Обновил профиль')
        messages.success(request, 'Профиль обновлён!')
        return redirect('profile')
    
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/profile.html', {'profile': profile, 'theme': theme})

@login_required
def user_profile_view(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=profile_user)
    is_friend = Friend.objects.filter(user=request.user, friend=profile_user).exists()
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/user_profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'is_friend': is_friend,
        'theme': theme,
    })

@login_required
def search_users_view(request):
    query = request.GET.get('q', '')
    users = []
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).exclude(id=request.user.id)
    friends = Friend.objects.filter(user=request.user)
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/search.html', {
        'users': users,
        'query': query,
        'friends': friends,
        'theme': theme,
    })

@login_required
def add_friend_view(request, user_id):
    friend_user = get_object_or_404(User, id=user_id)
    if friend_user != request.user:
        Friend.objects.get_or_create(user=request.user, friend=friend_user)
        Friend.objects.get_or_create(user=friend_user, friend=request.user)
        log_activity(request.user, f'Добавил друга {friend_user.username}')
    return redirect('search')

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    if to_user != request.user:
        FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
        log_activity(request.user, f'Отправил заявку дружбы {to_user.username}')
    return redirect('search')

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.is_accepted = True
    friend_request.save()
    Friend.objects.get_or_create(user=request.user, friend=friend_request.from_user)
    Friend.objects.get_or_create(user=friend_request.from_user, friend=request.user)
    log_activity(request.user, f'Принял заявку дружбы от {friend_request.from_user.username}')
    return redirect('friend_requests')

@login_required
def friend_requests_view(request):
    requests = FriendRequest.objects.filter(to_user=request.user, is_accepted=False)
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/friend_requests.html', {'requests': requests, 'theme': theme})

@login_required
def create_chat_view(request):
    if request.method == 'POST':
        form = ChatRoomForm(request.POST, request.FILES)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.created_by = request.user
            chat.save()
            form.save_m2m()
            log_activity(request.user, f'Создал чат "{chat.name}"')
            return redirect('home')
    else:
        form = ChatRoomForm()
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/create_chat.html', {'form': form, 'theme': theme})

@login_required
def chat_detail_view(request, chat_id):
    chat = get_object_or_404(ChatRoom, id=chat_id)
    if request.user not in chat.members.all():
        return redirect('home')
    
    now = timezone.now()
    Message.objects.filter(room=chat, expires_at__lte=now).delete()
    Message.objects.filter(room=chat, is_read=False).exclude(author=request.user).update(is_read=True)
    
    messages = chat.messages.all().order_by('timestamp')
    stickers = Sticker.objects.filter(Q(created_by=request.user) | Q(created_by__isnull=True))
    
    # Разбираем JSON для медиа-сообщений
    for msg in messages:
        try:
            content_data = json.loads(msg.content)
            if isinstance(content_data, dict) and content_data.get('type') == 'media':
                msg.parsed_content = content_data
                msg.is_media = True
            else:
                msg.parsed_content = msg.content
                msg.is_media = False
        except (json.JSONDecodeError, TypeError):
            msg.parsed_content = msg.content
            msg.is_media = False
    
    if not chat.is_group:
        other_user = chat.members.exclude(id=request.user.id).first()
    else:
        other_user = None
    
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/chat_detail.html', {
        'chat': chat,
        'messages': messages,
        'stickers': stickers,
        'other_user': other_user,
        'friends': Friend.objects.filter(user=request.user),
        'theme': theme,
    })

@login_required
def send_message_view(request, chat_id):
    chat = get_object_or_404(ChatRoom, id=chat_id)
    if request.user not in chat.members.all():
        return redirect('home')
    
    if chat.slow_mode > 0:
        last_msg = Message.objects.filter(room=chat, author=request.user).order_by('-timestamp').first()
        if last_msg:
            diff = (timezone.now() - last_msg.timestamp).total_seconds()
            if diff < chat.slow_mode:
                messages.error(request, f'Подождите {int(chat.slow_mode - diff)} секунд')
                return redirect('chat_detail', chat_id=chat.id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        reply_to_id = request.POST.get('reply_to')
        expiry_seconds = request.POST.get('expiry')
        
        if content:
            msg = Message.objects.create(
                room=chat,
                author=request.user,
                content=content,
                reply_to_id=reply_to_id if reply_to_id else None
            )
            if expiry_seconds:
                try:
                    expiry_seconds = int(expiry_seconds)
                    if 5 <= expiry_seconds <= 3600:
                        msg.expires_at = timezone.now() + timezone.timedelta(seconds=expiry_seconds)
                        msg.save()
                except ValueError:
                    pass
            
            log_activity(request.user, f'Отправил сообщение в чате "{chat.name}"')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'message_id': msg.id})
    return redirect('chat_detail', chat_id=chat.id)

@login_required
def get_new_messages(request, chat_id):
    last_id = request.GET.get('last_id', 0)
    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0

    chat = get_object_or_404(ChatRoom, id=chat_id)
    if request.user not in chat.members.all():
        return JsonResponse({'error': 'Access denied'}, status=403)

    now = timezone.now()
    Message.objects.filter(room=chat, expires_at__lte=now).delete()

    messages = chat.messages.filter(id__gt=last_id).order_by('timestamp')

    data = {
        'messages': [
            {
                'id': msg.id,
                'content': msg.content,
                'time': msg.timestamp.strftime('%H:%M'),
                'is_me': msg.author == request.user,
                'username': msg.author.username,
                'is_creator': msg.author.profile.is_creator,
                'avatar_url': msg.author.profile.avatar.url if msg.author.profile.avatar else '',
                'is_read': msg.is_read,
                'likes_count': msg.likes.count(),
                'has_liked': request.user in msg.likes.all(),
                'reply_to': msg.reply_to.id if msg.reply_to else None,
                'reply_content': msg.reply_to.content[:50] if msg.reply_to else None,
                'reply_author': msg.reply_to.author.username if msg.reply_to else None,
                'author_id': msg.author.id,
                'reactions': msg.reactions,
                'is_media': False,
            }
            for msg in messages
        ]
    }
    return JsonResponse(data)

@login_required
def start_private_chat(request, friend_id):
    friend = get_object_or_404(User, id=friend_id)
    existing_chat = ChatRoom.objects.filter(
        is_group=False,
        members=request.user
    ).filter(members=friend).first()
    
    if existing_chat:
        return redirect('chat_detail', chat_id=existing_chat.id)
    
    chat = ChatRoom.objects.create(
        name=f"{request.user.username} & {friend.username}",
        is_group=False,
        created_by=request.user
    )
    chat.members.add(request.user, friend)
    log_activity(request.user, f'Начал личный чат с {friend.username}')
    return redirect('chat_detail', chat_id=chat.id)

@login_required
def delete_friend(request, friend_id):
    friend = get_object_or_404(User, id=friend_id)
    Friend.objects.filter(user=request.user, friend=friend).delete()
    Friend.objects.filter(user=friend, friend=request.user).delete()
    log_activity(request.user, f'Удалил друга {friend.username}')
    return redirect('search')

@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(ChatRoom, id=chat_id)
    if request.user in chat.members.all():
        log_activity(request.user, f'Удалил чат "{chat.name}"')
        chat.delete()
    return redirect('home')

@login_required
def activity_view(request):
    hours = request.GET.get('hours', 24)
    try:
        hours = int(hours)
    except ValueError:
        hours = 24
    
    if hours == 0:
        activities = Activity.objects.filter(user=request.user)
    else:
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        activities = Activity.objects.filter(user=request.user, timestamp__gte=cutoff)
    
    activities = activities.order_by('-timestamp')
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/activity.html', {
        'activities': activities,
        'hours': hours,
        'theme': theme,
    })

@login_required
def clear_activity(request):
    Activity.objects.filter(user=request.user).delete()
    log_activity(request.user, 'Очистил историю действий')
    return redirect('activity')

@login_required
def forward_message_view(request, message_id):
    original = get_object_or_404(Message, id=message_id)
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        chat = get_object_or_404(ChatRoom, id=chat_id)
        if request.user in chat.members.all():
            # Проверяем, если исходное сообщение — медиа
            try:
                import json
                content_data = json.loads(original.content)
                if isinstance(content_data, dict) and content_data.get('type') == 'media':
                    new_content = json.dumps(content_data)
                else:
                    new_content = f"📩 Переслано от {original.author.username}: {original.content}"
            except:
                new_content = f"📩 Переслано от {original.author.username}: {original.content}"
            
            Message.objects.create(
                room=chat,
                author=request.user,
                content=new_content
            )
            log_activity(request.user, f'Переслал сообщение в чат "{chat.name}"')
        return redirect('chat_detail', chat_id=chat.id)
    chats = ChatRoom.objects.filter(members=request.user)
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/forward_message.html', {
        'message': original,
        'chats': chats,
        'theme': theme,
    })

@login_required
def like_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user in message.likes.all():
        message.likes.remove(request.user)
    else:
        message.likes.add(request.user)
    return redirect('chat_detail', chat_id=message.room.id)

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if message.author == request.user:
        message.delete()
        log_activity(request.user, 'Удалил сообщение')
    return redirect('chat_detail', chat_id=message.room.id)

@login_required
def add_reaction(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.method == 'POST':
        reaction = request.POST.get('reaction')
        if reaction in ['👍', '❤️', '😂', '😮', '😢', '😡']:
            reactions = message.reactions or {}
            user_reactions = reactions.get(str(request.user.id), [])
            if reaction in user_reactions:
                user_reactions.remove(reaction)
            else:
                user_reactions.append(reaction)
            reactions[str(request.user.id)] = user_reactions
            message.reactions = reactions
            message.save()
    return redirect('chat_detail', chat_id=message.room.id)

@login_required
def start_game(request, chat_id):
    chat = get_object_or_404(ChatRoom, id=chat_id)
    if request.user not in chat.members.all():
        return redirect('home')
    
    existing_game = Game.objects.filter(chat_room=chat, is_active=True).first()
    if existing_game:
        return redirect('chat_detail', chat_id=chat.id)
    
    game = Game.objects.create(
        chat_room=chat,
        game_type='tic_tac_toe',
        state={'board': [['' for _ in range(3)] for _ in range(3)], 'turn': 'X'}
    )
    game.players.add(request.user)
    other = chat.members.exclude(id=request.user.id).first()
    if other:
        game.players.add(other)
        game.current_turn = other
    else:
        game.current_turn = request.user
    game.save()
    
    return redirect('chat_detail', chat_id=chat.id)

@login_required
def make_move(request, game_id):
    game = get_object_or_404(Game, id=game_id, is_active=True)
    if request.user != game.current_turn:
        return JsonResponse({'error': 'Not your turn'}, status=403)
    
    if request.method == 'POST':
        row = int(request.POST.get('row'))
        col = int(request.POST.get('col'))
        board = game.state.get('board', [['' for _ in range(3)] for _ in range(3)])
        turn = game.state.get('turn', 'X')
        
        if board[row][col] != '':
            return JsonResponse({'error': 'Cell already taken'}, status=400)
        
        board[row][col] = turn
        
        winner = None
        for r in range(3):
            if board[r][0] == board[r][1] == board[r][2] != '':
                winner = board[r][0]
        for c in range(3):
            if board[0][c] == board[1][c] == board[2][c] != '':
                winner = board[0][c]
        if board[0][0] == board[1][1] == board[2][2] != '':
            winner = board[0][0]
        if board[0][2] == board[1][1] == board[2][0] != '':
            winner = board[0][2]
        
        if winner:
            game.is_active = False
            winner_user = game.players.filter(username=winner).first()
            game.winner = winner_user
            game.save()
            return JsonResponse({'winner': winner, 'board': board})
        
        if all(board[r][c] != '' for r in range(3) for c in range(3)):
            game.is_active = False
            game.save()
            return JsonResponse({'draw': True, 'board': board})
        
        next_turn = 'O' if turn == 'X' else 'X'
        game.state = {'board': board, 'turn': next_turn}
        for player in game.players.all():
            if player != request.user:
                game.current_turn = player
                break
        game.save()
        
        return JsonResponse({'board': board, 'turn': next_turn, 'current_turn': game.current_turn.username})
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def game_status(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    board = game.state.get('board', [['' for _ in range(3)] for _ in range(3)])
    return JsonResponse({
        'board': board,
        'is_active': game.is_active,
        'winner': game.winner.username if game.winner else None,
        'current_turn': game.current_turn.username if game.current_turn else None,
    })

@login_required
def qr_code_view(request):
    user = request.user
    qr_text = f"WispChat:AddFriend:{user.id}:{user.username}:{hashlib.md5(user.username.encode()).hexdigest()[:8]}"
    return render(request, 'chat/qr_code.html', {
        'qr_text': qr_text,
        'user': user,
    })

@login_required
def add_by_qr(request):
    if request.method == 'POST':
        qr_text = request.POST.get('qr_text')
        if qr_text and qr_text.startswith('WispChat:AddFriend:'):
            try:
                parts = qr_text.split(':')
                user_id = int(parts[2])
                friend_user = get_object_or_404(User, id=user_id)
                if friend_user != request.user:
                    Friend.objects.get_or_create(user=request.user, friend=friend_user)
                    Friend.objects.get_or_create(user=friend_user, friend=request.user)
                    messages.success(request, f'Вы добавили {friend_user.username} в друзья!')
                else:
                    messages.error(request, 'Нельзя добавить самого себя')
            except (ValueError, IndexError):
                messages.error(request, 'Неверный QR-код')
        else:
            messages.error(request, 'Неверный QR-код')
        return redirect('home')
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/add_by_qr.html', {'theme': theme})

@login_required
def create_sticker_pack_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        pack = request.POST.get('pack')
        if name and image and pack:
            Sticker.objects.create(
                name=name,
                image=image,
                pack=pack,
                created_by=request.user
            )
            messages.success(request, 'Стикер добавлен!')
            return redirect('create_sticker_pack')
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/create_sticker.html', {'theme': theme})

typing_users = {}

@csrf_exempt
@login_required
def typing_view(request, chat_id):
    if request.method == 'POST':
        chat_id_str = str(chat_id)
        if chat_id_str not in typing_users:
            typing_users[chat_id_str] = []
        if request.user.username not in typing_users[chat_id_str]:
            typing_users[chat_id_str].append(request.user.username)
        return JsonResponse({'status': 'typing'})
    chat_id_str = str(chat_id)
    typing_list = typing_users.get(chat_id_str, [])
    return JsonResponse({'typing': typing_list})

@csrf_exempt
@login_required
def stop_typing_view(request, chat_id):
    chat_id_str = str(chat_id)
    if chat_id_str in typing_users:
        if request.user.username in typing_users[chat_id_str]:
            typing_users[chat_id_str].remove(request.user.username)
    return JsonResponse({'status': 'stopped'})

@login_required
def add_member(request, chat_id):
    chat = get_object_or_404(ChatRoom, id=chat_id, is_group=True)
    if request.user != chat.created_by:
        messages.error(request, 'Только создатель может добавлять участников')
        return redirect('chat_detail', chat_id=chat.id)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_to_add = get_object_or_404(User, id=user_id)
        if user_to_add in chat.members.all():
            messages.error(request, 'Пользователь уже в чате')
        else:
            chat.members.add(user_to_add)
            log_activity(request.user, f'Добавил {user_to_add.username} в чат "{chat.name}"')
            messages.success(request, f'{user_to_add.username} добавлен в чат')
        return redirect('chat_detail', chat_id=chat.id)
    
    friends = Friend.objects.filter(user=request.user)
    theme = request.COOKIES.get('theme', 'light')
    return render(request, 'chat/add_member.html', {
        'chat': chat,
        'friends': friends,
        'theme': theme,
    })

@login_required
def remove_member(request, chat_id, user_id):
    chat = get_object_or_404(ChatRoom, id=chat_id, is_group=True)
    if request.user != chat.created_by:
        messages.error(request, 'Только создатель может исключать участников')
        return redirect('chat_detail', chat_id=chat.id)
    
    user_to_remove = get_object_or_404(User, id=user_id)
    if user_to_remove == chat.created_by:
        messages.error(request, 'Нельзя исключить создателя чата')
        return redirect('chat_detail', chat_id=chat.id)
    
    if user_to_remove in chat.members.all():
        chat.members.remove(user_to_remove)
        log_activity(request.user, f'Исключил {user_to_remove.username} из чата "{chat.name}"')
        messages.success(request, f'{user_to_remove.username} исключён из чата')
    return redirect('chat_detail', chat_id=chat.id)

@login_required
def chat_settings_view(request, chat_id):
    chat = get_object_or_404(ChatRoom, id=chat_id, is_group=True)
    if request.user != chat.created_by:
        return redirect('chat_detail', chat_id=chat.id)
    
    if request.method == 'POST':
        slow_mode = request.POST.get('slow_mode', 0)
        try:
            chat.slow_mode = int(slow_mode)
            chat.save()
            messages.success(request, f'Тайминг установлен: {chat.slow_mode} сек')
            log_activity(request.user, f'Изменил тайминг в чате "{chat.name}" на {chat.slow_mode} сек')
        except ValueError:
            messages.error(request, 'Введите число')
        return redirect('chat_detail', chat_id=chat.id)
    
    theme = request.COOKIES.get('theme', 'light')
    friends = Friend.objects.filter(user=request.user)
    return render(request, 'chat/chat_settings.html', {
        'chat': chat,
        'friends': friends,
        'theme': theme,
    })

@login_required
def upload_file(request, chat_id):
    chat = get_object_or_404(ChatRoom, id=chat_id)
    if request.user not in chat.members.all():
        return redirect('home')
    
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')
        file_urls = []
        
        for file in files[:5]:
            filename = default_storage.save(f'uploads/{file.name}', ContentFile(file.read()))
            file_url = default_storage.url(filename)
            file_urls.append(file_url)
        
        # Сохраняем как JSON-строку
        Message.objects.create(
            room=chat,
            author=request.user,
            content=json.dumps({'type': 'media', 'urls': file_urls})
        )
        log_activity(request.user, f'Отправил {len(file_urls)} файлов в чат "{chat.name}"')
    
    return redirect('chat_detail', chat_id=chat.id)

@login_required
def get_online_members(request, chat_id):
    chat = get_object_or_404(ChatRoom, id=chat_id)
    if request.user not in chat.members.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    online_count = chat.members.filter(profile__is_online=True).count()
    return JsonResponse({'online_count': online_count})