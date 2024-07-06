import discord
import os
import threading
import asyncio
import time
from dotenv import load_dotenv, find_dotenv
from random import uniform

from llm import start_llm

load_dotenv(find_dotenv())
TOKEN = os.environ.get("DISCORD_TOKEN")


class ChatBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = None
        self.users_whitelist = ["392004509968236554"]
        self.track_messages = False
        self.pause = False
        self.delay = 5

    def print_bot_info(self):
        print(f"Bot name: {self.user}")
        print(f"Bot ID: {self.user.id}")
        print(f"Bot channel: {self.channel}")
        print(f"Bot delay: {self.delay}s")
        print(f"Bot tracking messages: {self.track_messages}")

    def print_bot_commands(self):
        print("Bot commands:")
        print("stop - stop the bot")
        print("send <message> - send a message to the channel")
        print("channel <channel_id> - set the channel to send messages")
        print("track - toggle tracking messages")
        print("delay <seconds> - set the delay for sending messages")
        print("help - print the bot commands")
        print("adduser <user_id> - add user to whitelist")
        print("removeuser <user_id> - remove user from whitelist")

    def delay_counter(self):
        self.pause = True
        time.sleep(self.delay)
        self.pause = False

    def reply_forbidden(self, msg):
        return self.user.mentioned_in(msg) and \
               not self.pause and \
               str(msg.author.id) in self.users_whitelist
        
    def execute_async_in_thread(self, coro, args):
        loop = asyncio.run_coroutine_threadsafe(coro(*args), self.loop)
        loop.result()
    
    async def execute_stop_cmd(self):
        print("Stopping bot...")
        await self.close()

    async def send_message_cmd(self, msg):
        if not self.channel or not msg.strip():
            print("Unable to send message")
            return
        print(f"Sending message: {msg}")
        channel = self.get_channel(int(self.channel))
        async with channel.typing():
            await asyncio.sleep(uniform(1, 2))
            await channel.send(msg)

    def set_channel_cmd(self, channel):
        if not channel.isdigit():
            print("Unable to set channel")
            return
        self.channel = channel
        print(f"Channel set to {self.channel}")

    def set_delay_cmd(self, delay):
        if not delay.isdigit():
            print("Unable to set delay")
            return
        self.delay = int(delay)
        print(f"Delay set to {self.delay}s")

    def add_user_to_whitelist(self, user_id):
        if not user_id.isdigit():
            print("Unable to add user to whitelist")
            return
        self.users_whitelist.append(user_id)
        print(f"User {user_id} added to whitelist")

    def remove_user_from_whitelist(self, user_id):
        if not user_id.isdigit() or user_id not in self.users_whitelist:
            print("Unable to remove user from whitelist")
            return
        self.users_whitelist.remove(user_id)
        print(f"User {user_id} removed from whitelist")

    def track_messages_cmd(self):
        self.track_messages = not self.track_messages
        print(f"Tracking messages: {self.track_messages}")
    
    def execute_command(self):
        print("Bot is ready to receive commands")
        while not self.is_closed():
            cmd = input(">>> ").split()
            if not cmd:
                continue
            if cmd[0] == "stop":
                self.execute_async_in_thread(self.execute_stop_cmd, ())
            elif cmd[0] == "help":
                self.print_bot_commands()
            elif cmd[0] == "send":
                self.execute_async_in_thread(self.send_message_cmd, (" ".join(cmd[1:]),))
            elif cmd[0] == "channel":
                self.set_channel_cmd("".join(cmd[1:]))
            elif cmd[0] == "track":
                self.track_messages_cmd()
            elif cmd[0] == "delay":
                self.set_delay_cmd("".join(cmd[1:]))
            elif cmd[0] == "adduser":
                self.add_user_to_whitelist("".join(cmd[1:]))
            elif cmd[0] == "removeuser":
                self.remove_user_from_whitelist("".join(cmd[1:]))
            else:
                print("Unknown command")

    async def when_mentioned(self, msg):
        query = msg.content
        print(f"Query: {query}")
        response = start_llm(query)
        print(f"Response: {response}\n>>> ", end="")
        await msg.channel.send(response, reference=msg)

    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")
        self.print_bot_info()
        threading.Thread(target=self.execute_command).start()

    async def on_message(self, msg):
        if msg.author == self.user or str(msg.channel.id) != self.channel:
            return
        if self.track_messages:
            print(f"Message from {msg.author}: {msg.content}\n>>> ", end="")
        if self.reply_forbidden(msg):
            threading.Thread(target=self.delay_counter).start()
            await asyncio.sleep(2)
            async with msg.channel.typing():
                await asyncio.sleep(uniform(10, 15))
                await self.when_mentioned(msg)


def main():
    bot = ChatBot()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()