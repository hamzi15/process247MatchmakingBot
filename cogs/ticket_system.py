import datetime
import json
import os
import sys
from random import randint

import asyncio
import discord
# import asyncio

from discord.ext import commands
from discord.utils import get

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)

intents = discord.Intents.all()
client = commands.Bot(command_prefix=config["bot_prefix"], intents=intents)
client.ticket_configs = {}
ticket_channel = config["channelids"]["ticket-channel"]
msg_id = config["ticket-msg-id"]


class TicketSystem(commands.Cog, name="ticket_system"):
    def __init__(self, bot):
        self.bot = bot

    # async def add_reactions(self, msg):
    #     tasks = [asyncio.ensure_future(msg.add_reaction('🚩')), asyncio.ensure_future(msg.add_reaction('🎫'))]
    #     await asyncio.wait(tasks)
    #
    # async def remove_reactions(self, msg):
    #     tasks = [asyncio.ensure_future(msg.remove_reaction('🚩', self.user)),
    #              asyncio.ensure_future(msg.remove_reaction('🎫', self.user))]
    #     await asyncio.wait(tasks)

    @commands.command(name="close", description="Closes a ticket")
    async def close(self, context):
        channel = context.channel
        await channel.delete()

    async def create_channel(self, name, payload):
        if type(payload) == 'discord.RawReactionEvent':
            member = self.bot.get_user(payload.user_id)
            guild = payload.member.guild
            admin_role = get(guild.roles, name="ADMIN")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
            config['ticket-id'] += 1
            with open('config.json', "w") as file:
                json.dump(config, file)
                file.close()
            channel = await guild.create_text_channel(name, overwrites=overwrites)
            return channel
        elif type(payload) == "discord.ext.commands.Context":
            member = self.bot.get_user(payload.author.id)
            guild = payload.guild
            admin_role = get(guild.roles, name="ADMIN")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True),
                admin_role: discord.PermissionOverwrite(read_messages=True)
            }
            config['ticket-id'] += 1
            with open('config.json', "w") as file:
                json.dump(config, file)
                file.close()
            channel = await guild.create_text_channel(name, overwrites=overwrites)
            return channel

    async def report(self, payload):
        name = f"report-{config['ticket-id']}-{payload.member.name}"
        channel = await self.create_channel(name, payload)
        guild = payload.member.guild
        embed = discord.Embed(color=randint(0, 0xffff),
                              description="**Report a Player**\n"
                                          "Thanks for opening a report ticket! Please provide us with "
                                          "the following information to create a report:\n\n "
                                          "**1. The player you wish to report.**\n"
                                          "**2. The server and team the player is on**\n"
                                          "**3. The rules they are breaking**\n"
                                          "**4. Proof (Screenshots/Video)**\n\n"
                                          "Once you have made the report you may "
                                          f"notify active admins by typing {(discord.utils.get(guild.roles, id=811086680576622622)).mention} to mention them.\n\n"
                                          "**Note:** Evidence for minor violations can be uploaded directly to Discord."
                                          "\n\n"
                                          f"You can type `{config['bot_prefix']}close` to close this ticket.\n\n"
                                          "*If you want a transcript once the report is closed,"
                                          " you will need to allow DMs from server members in your "
                                          "Discord privacy settings.*")
        embed.timestamp = datetime.datetime.now()
        await channel.send(content=(self.bot.get_user(payload.user_id)).mention, embed=embed)

    @commands.command(name="ticket", description="Creates a new General Ticket.")
    async def ticket(self, payload):
        print("Type of Payload: ", type(payload))
        if type(payload) == "discord.RawReactionEvent":
            name_of_channel = f"general-{config['ticket-id']}-{payload.member.name}"
            channel = await self.create_channel(name_of_channel, payload=payload)
            guild = payload.member.guild
            embed = discord.Embed(color=randint(0, 0xffff),
                                  description="What do you need help with? (Please wait for the reactions to complete before using them)\n\n"
                                              "**React with one of the choices below: **\n "
                                              "**1️⃣ Report a Player**\n"
                                              "**2️⃣ Appeal Ban**\n"
                                              "**3️⃣ Whitelist VPN/ISP**\n"
                                              "**4️⃣ When is Wipe/Server Information**\n"
                                              "**5️⃣ Server or Connection Problems**\n"
                                              "**6️⃣ VIP/Store Problems**\n"
                                              "**7️⃣ I have a suggestion**\n"
                                              "**8️⃣ I would like a custom skin added**\n"
                                              "**9️⃣ Other**\n")
            embed.timestamp = "Type `!cancel` to abort this ticket at any time."
            await asyncio.gather(channel.send(color=randint(0, 0xffff), embed=discord.Embed(description=f"Ticket **#{config['ticket-id']}** has been assigned. Please follow the instructions and menus below. Wait for the bot to complete the reactions before using them, and please select the most appropriate category for your issue or your ticket may be rejected.")))
            msg = await channel.send(content=(self.bot.get_user(payload.user_id)).mention, embed=embed)
            await msg.add_reaction("1️⃣")
            await msg.add_reaction("2️⃣")
            await msg.add_reaction("3️⃣")
            await msg.add_reaction("4️⃣")
            await msg.add_reaction("5️⃣")
            await msg.add_reaction("6️⃣")
            await msg.add_reaction("7️⃣")
            await msg.add_reaction("8️⃣")
            await msg.add_reaction("9️⃣")
            return
        elif type(payload) == "discord.ext.commands.Context":
            name_of_channel = f"general-{config['ticket-id']}-{payload.author.name}"
            channel = await self.create_channel(name_of_channel, payload=payload)
            embed = discord.Embed(color=randint(0, 0xffff),
                                  description="What do you need help with? (Please wait for the reactions to complete before using them)\n\n"
                                              "**React with one of the choices below: **\n "
                                              "**1️⃣ Report a Player**\n"
                                              "**2️⃣ Appeal Ban**\n"
                                              "**3️⃣ Whitelist VPN/ISP**\n"
                                              "**4️⃣ When is Wipe/Server Information**\n"
                                              "**5️⃣ Server or Connection Problems**\n"
                                              "**6️⃣ VIP/Store Problems**\n"
                                              "**7️⃣ I have a suggestion**\n"
                                              "**8️⃣ I would like a custom skin added**\n"
                                              "**9️⃣ Other**\n")
            embed.timestamp = "Type `!cancel` to abort this ticket at any time."
            await asyncio.gather(channel.send(color=randint(0, 0xffff), embed=discord.Embed(
                description=f"Ticket **#{config['ticket-id']}** has been assigned. Please follow the instructions and menus below. Wait for the bot to complete the reactions before using them, and please select the most appropriate category for your issue or your ticket may be rejected.")))
            msg = await channel.send(content=payload.author.mention, embed=embed)
            await msg.add_reaction("1️⃣")
            await msg.add_reaction("2️⃣")
            await msg.add_reaction("3️⃣")
            await msg.add_reaction("4️⃣")
            await msg.add_reaction("5️⃣")
            await msg.add_reaction("6️⃣")
            await msg.add_reaction("7️⃣")
            await msg.add_reaction("8️⃣")
            await msg.add_reaction("9️⃣")
            return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not (self.bot.get_user(payload.user_id)).bot and payload.channel_id == config["channelids"][
            "ticket-channel"]:  # and payload.message_id == msg_id
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            user = self.bot.get_user(payload.user_id)
            if not user:
                user = await self.bot.fetch_user(payload.user_id)
            await message.remove_reaction(payload.emoji, user)
            if payload.emoji.name == "🚩":
                await self.report(payload)
            elif payload.emoji.name == "🎫":
                await self.ticket(payload)
        elif not (self.bot.get_user(payload.user_id)).bot:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            user = self.bot.get_user(payload.user_id)
            guild = payload.member.guild
            if not user:
                user = await self.bot.fetch_user(payload.user_id)
            await message.remove_reaction(payload.emoji, user)

            if payload.emoji.name == "1️⃣":
                await channel.send(content=(discord.utils.get(guild.roles, id=811086680576622622)).mention,
                                   embed=discord.Embed(color=randint(0, 0xffff), description=f"{user.mention} wants to **Report a Player**"))
            elif payload.emoji.name == "2️⃣":
                await channel.send(content=(discord.utils.get(guild.roles, id=811086680576622622)).mention,
                                   embed=discord.Embed(color=randint(0, 0xffff),
                                                       description=f"{user.mention} wants to **Appeal Ban**"))
            elif payload.emoji.name == "3️⃣":
                await channel.send(content=(discord.utils.get(guild.roles, id=811086680576622622)).mention,
                                   embed=discord.Embed(color=randint(0, 0xffff),
                                                       description=f"{user.mention} wants to **Whitelist VPN/ISP**"))
            elif payload.emoji.name == "4️⃣":
                await channel.send(content=(discord.utils.get(guild.roles, id=811086680576622622)).mention,
                                   embed=discord.Embed(color=randint(0, 0xffff),
                                                       description=f"{user.mention} wants to know when is **Wipe/ Server Information**"))
            elif payload.emoji.name == "5️⃣":
                await channel.send(content=(discord.utils.get(guild.roles, id=811086680576622622)).mention,
                                   embed=discord.Embed(color=randint(0, 0xffff),
                                                       description=f"{user.mention} has **Server/Connection Problems**"))
            elif payload.emoji.name == "6️⃣":
                await channel.send(content=(discord.utils.get(guild.roles, id=811086680576622622)).mention,
                                   embed=discord.Embed(color=randint(0, 0xffff),
                                                       description=f"{user.mention} has **VIP/Store Problems**"))
            elif payload.emoji.name == "7️⃣":
                await channel.send(content=(discord.utils.get(guild.roles, id=811086680576622622)).mention,
                                   embed=discord.Embed(color=randint(0, 0xffff),
                                                       description=f"{user.mention} has a **Suggestion**"))
            elif payload.emoji.name == "8️⃣":
                await channel.send(content=(discord.utils.get(guild.roles, id=811086680576622622)).mention,
                                   embed=discord.Embed(color=randint(0, 0xffff),
                                                       description=f"{user.mention} wants to **Add a Custom Skin**"))
            elif payload.emoji.name == "9️⃣":
                await channel.send(content=(discord.utils.get(guild.roles, id=811086680576622622)).mention,
                                   embed=discord.Embed(color=randint(0, 0xffff),
                                                       description=f"**{user.mention}'s problem is not in the list!**"))


def setup(bot):
    bot.add_cog(TicketSystem(bot))

# import asyncio
# import logging
# from threading import Timer
#
# import discord
# from configobj import ConfigObj
#
# logging.basicConfig(level=logging.INFO)
# prefix = "?"
#
#
# class SupportClient(discord.Client):

#
#
# client = SupportClient()
# client.run(client.cfg['Token'])
