import json
import logging

import bleach
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.utils import timezone

from eshop_app import models

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.token = await self.extract_and_validate_token()
        self.user = self.scope.get("user", None)

        if not self.token or self.user.is_anonymous:
            logger.warning(f"Unauthorized websocket connection attempt to room {self.room_name}")
            await self.close(code=4003)
            return

        try:
            has_permission = await self.check_room_permission()
            if not has_permission:
                logger.warning(
                    f"User {self.user.username} attempted to access unauthorized room {self.room_name}"
                )
                await self.close(code=4004)
                return
        except Exception as e:
            logger.error(f"Error checking room permission: {str(e)}")
            await self.close(code=4000)
            return

        self.room_group_name = f"chat_online_{self.room_name}"

        self.room_details = await self.get_room_details()
        if not self.room_details:
            await self.close(code=4002)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.send_chat_history()

        logger.info(f"WebSocket connected: {self.user.username} to room {self.room_name}")

    async def extract_and_validate_token(self):
        """Extract and validate the token from query parameters"""
        try:
            query_string = self.scope["query_string"].decode("utf-8")
            params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            token = params.get('token', '')

            cache_key = f"token_valid_{self.room_name}_{token}"
            is_valid = cache.get(cache_key)

            if is_valid is None:
                is_valid = await self.is_valid_token(token)
                cache.set(cache_key, is_valid, 300)

            return token if is_valid else None
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None

    @database_sync_to_async
    def is_valid_token(self, token):
        """Validate the room token"""
        try:
            room = models.Room.objects.get(slug=self.room_name)
            return room.token == token
        except ObjectDoesNotExist:
            return False

    @database_sync_to_async
    def check_room_permission(self):
        """Check if the user has permission to access this room"""
        try:
            room = models.Room.objects.get(slug=self.room_name)
            return room.user_started_id == self.user.id or room.user_opponent_id == self.user.id
        except ObjectDoesNotExist:
            raise Http404("Room does not exist")

    @database_sync_to_async
    def get_room_details(self):
        """Get room details to avoid repeated database queries"""
        try:
            room = models.Room.objects.select_related('user_started', 'user_opponent').get(
                slug=self.room_name
            )

            first_avatar = '/static/media/png/user.png'
            second_avatar = '/static/media/png/user.png'

            try:
                if hasattr(room.user_started, 'profile'):
                    user_started_profile = room.user_started.profile
                    if hasattr(user_started_profile, 'get_avatar_url'):
                        avatar_url = user_started_profile.get_avatar_url()
                        if avatar_url:
                            first_avatar = avatar_url
            except Exception as e:
                logger.error(f"Error getting first user avatar: {str(e)}")

            try:
                if hasattr(room.user_opponent, 'profile'):
                    user_opponent_profile = room.user_opponent.profile
                    if hasattr(user_opponent_profile, 'get_avatar_url'):
                        avatar_url = user_opponent_profile.get_avatar_url()
                        if avatar_url:
                            second_avatar = avatar_url
            except Exception as e:
                logger.error(f"Error getting second user avatar: {str(e)}")

            return {
                'room_id': room.id,
                'first_user_id': room.user_started_id,
                'first_username': room.user_started.username,
                'second_user_id': room.user_opponent_id,
                'second_username': room.user_opponent.username,
                'first_avatar': first_avatar,
                'second_avatar': second_avatar,
            }
        except ObjectDoesNotExist:
            logger.error(f"Room {self.room_name} does not exist")
            return None

    async def send_chat_history(self, limit=20):
        """Send recent chat history to newly connected user"""
        try:
            messages = await self.get_recent_messages(limit)
            if messages:
                await self.send(
                    text_data=json.dumps(
                        {
                            'type': 'history',
                            'messages': messages,
                        }
                    )
                )
        except Exception as e:
            logger.error(f"Error sending chat history: {str(e)}")

    @database_sync_to_async
    def get_recent_messages(self, limit=20):
        """Get recent messages for this room"""
        try:
            room = models.Room.objects.get(slug=self.room_name)
            messages = models.Message.objects.filter(room=room).order_by('-date_added')[:limit]

            result = []
            for message in reversed(list(messages)):
                local_time = timezone.localtime(message.date_added)
                formatted_time = local_time.strftime("%H:%M")

                result.append(
                    {
                        'message': message.content,
                        'username': message.user.username,
                        'timestamp': formatted_time,
                        'avafiruser': self.room_details.get('first_avatar', ''),
                        'avasecuser': self.room_details.get('second_avatar', ''),
                        'firusername': self.room_details.get('first_username', ''),
                        'secusername': self.room_details.get('second_username', ''),
                    }
                )
            return result
        except Exception as e:
            logger.error(f"Error getting recent messages: {str(e)}")
            return []

    async def disconnect(self, code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info(f"WebSocket disconnected: {getattr(self, 'user', 'Unknown')}, code: {code}")

    async def receive(self, text_data):
        """Handle received message from WebSocket"""
        rate_limit_key = f"chat_rate_limit_{self.user.id}"
        rate_limit = cache.get(rate_limit_key, 0)

        if rate_limit >= 5:
            await self.send(
                text_data=json.dumps(
                    {
                        'error': 'Rate limit exceeded. Please wait before sending more messages.',
                        'type': 'rate_limit',
                    }
                )
            )
            return

        cache.set(rate_limit_key, rate_limit + 1, 3)

        try:
            data = json.loads(text_data)

            required_fields = ['username', 'room', 'message']
            if not all(field in data for field in required_fields):
                logger.warning(f"Message missing required fields from {self.user.username}")
                return

            if data['username'] != self.user.username:
                logger.warning(
                    f"User {self.user.username} attempted to send message as {data['username']}"
                )
                return

            if data['room'] != self.room_name:
                logger.warning(f"Room mismatch in message: {data['room']} vs {self.room_name}")
                return

            message = bleach.clean(data["message"].strip())
            if not message:
                return

            if len(message) > 4000:
                message = message[:4000] + "..."

            message_time = await self.save_message(self.user.username, self.room_name, message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "username": self.user.username,
                    "room": self.room_name,
                    "avafiruser": self.room_details.get('first_avatar', ''),
                    "avasecuser": self.room_details.get('second_avatar', ''),
                    "firusername": self.room_details.get('first_username', ''),
                    "secusername": self.room_details.get('second_username', ''),
                    "timestamp": message_time,
                },
            )
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {self.user.username}")
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")

    async def chat_message(self, event):
        """Send message to WebSocket"""
        message_data = {k: v for k, v in event.items() if k != 'type'}

        await self.send(text_data=json.dumps(message_data))

    @sync_to_async
    def save_message(self, username, room_slug, message):
        """Save message to database and return formatted timestamp"""
        try:
            room_id = self.room_details.get('room_id')

            user_id = self.user.id

            message_obj = models.Message.objects.create(
                user_id=user_id, room_id=room_id, content=message
            )

            local_time = timezone.localtime(message_obj.date_added)
            formatted_time = local_time.strftime("%H:%M")
            return formatted_time

        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            now = timezone.localtime(timezone.now())
            return now.strftime("%H:%M")
