import json
from eshop_app import models
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.token = await self.extract_and_validate_token()

        if not self.token:
            await self.close()
            return

        self.room_group_name = f"chat_online_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        # print("WebSocket connected")

    async def extract_and_validate_token(self):
        try:
            query_string = self.scope["query_string"].decode("utf-8")
            token_param = query_string.split("=")
            if len(token_param) == 2:
                token = token_param[1]
                if await self.is_valid_token(token):
                    return token
        except IndexError:
            pass
        return None

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # print("WebSocket disconnected with code:", code)

    async def receive(self, text_data: str):
        data = json.loads(text_data)
        username = data["username"]
        room = data["room"]
        message = data["message"]
        avafiruser = data.get("avafiruser", "")
        avasecuser = data.get("avasecuser", "")
        firusername = data.get("firusername", "")
        secusername = data.get("secusername", "")

        await self.save_message(username, room, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": username,
                "room": room,
                "avafiruser": avafiruser,
                "avasecuser": avasecuser,
                "firusername": firusername,
                "secusername": secusername,
            },
        )

    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]
        room = event["room"]
        avafiruser = event["avafiruser"]
        avasecuser = event["avasecuser"]
        firusername = event["firusername"]
        secusername = event["secusername"]

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "username": username,
                    "room": room,
                    "avafiruser": avafiruser,
                    "avasecuser": avasecuser,
                    "firusername": firusername,
                    "secusername": secusername,
                }
            )
        )

    @database_sync_to_async
    def is_valid_token(self, token):
        try:
            room = models.Room.objects.get(slug=self.room_name)
            return room.token == token
        except ObjectDoesNotExist:
            return False

    @sync_to_async
    def save_message(self, username, room, message):
        user = User.objects.get(username=username)
        room = models.Room.objects.get(slug=room)

        models.Message.objects.create(user=user, room=room, content=str(message))
