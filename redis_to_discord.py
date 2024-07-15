#! /usr/bin/env python3

import sys
import discord
import redis
import config
from discord.ext import tasks, commands
import re
from markdownify import markdownify as md


class Redis():
    def __init__(self):
        self._redis = redis.StrictRedis(host='localhost', port=6379, db=0)

        # create discord_sync_id if not exists
        self._create_discord_sync_id()
        
    def _get_discord_sync_id(self):
        return int(self._redis.get("discord_sync_id"))
    
    def _create_discord_sync_id(self):
        if self._redis.get("discord_sync_id") is None:
            self._redis.set("discord_sync_id", 0)

    def _get_max_id(self):
        return int(self._redis.get("max_id"))
    
    def get_new_messages(self):
        discord_sync_id = self._get_discord_sync_id()
        max_id = self._get_max_id()
        if discord_sync_id < max_id:
            messages = []
            for i in range(discord_sync_id + 1, max_id + 1):
                messages.append(self._redis.get(i))
            # set discord_sync_id
            self._redis.set("discord_sync_id", max_id)
            return messages
        if discord_sync_id > max_id:
            # something is wrong
            self._redis.set("discord_sync_id", max_id)
        return None
    

class Discord(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        channel = bot.get_channel(config.discord_channel_id)
        await self.send_new_messages.start(channel)

    @tasks.loop(seconds=2)
    async def send_new_messages(self, channel):
        redis = Redis()
        # send new messages to discord channel World
        messages = redis.get_new_messages()
        if messages:
            for message in messages:
                try:
                    message = message.decode('utf-8')
                except:
                    continue
                # convert html to markdown
                try:
                    message = md(message)
                except:
                    pass
                await channel.send(message)

intents = discord.Intents.default()
bot = Discord(intents=intents)
bot.run(config.discord_token)