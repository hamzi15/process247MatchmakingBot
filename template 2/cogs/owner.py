import asyncio
import discord
from discord.ext import commands
import json
import os
import sys

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)

with open('invites.json', 'r') as o:
    invite_uses = json.load(o)

def has_roles(context):
    roles = [role.name for role in context.message.author.roles]
    if "Admin" in roles:
        return True
    return False


def update_config():
    with open('config.json', 'w') as fp:
        json.dump(config, fp)


class Owner(commands.Cog, name="owner"):
    def __init__(self, bot):
        self.bot = bot

    # the bot will say anything you want
    @commands.command(name="say", aliases=["echo"], description="Bot will say anything you want")
    async def say(self, context, *, args):
        if has_roles(context):
            await context.send(args)

    @commands.command(name="embed", description="Bot will say anything in an embed")
    async def embed(self, context, *, args):
        if has_roles(context):
            embed = discord.Embed(
                description=args,
                color=0x42F56C
            )
            await context.send(embed=embed)

    @commands.command(name="enableinvitefilter", description="Enables invite filter.")
    async def enableinvitefilter(self, context):
        if has_roles(context):
            config['invitefilterenabled'] = True
            update_config()
            await context.send(embed=discord.Embed(description="Invite Filter enabled", color=0x00ff73))

    @commands.command(name="disableinvitefilter", description="Disables invite filter.")
    async def disableinvitefilter(self, context):
        if has_roles(context):
            config['invitefilterenabled'] = False
            update_config()
            await context.send(embed=discord.Embed(description="Invite Filter disabled", color=0xff0000))

    @commands.command(name="sendDM", description="Bot will DM a user after a set interval. Syntax: !sendDM [member@] "
                                                 "[number of times the DM should be sent] [interval in minutes] [the "
                                                 "message]\n ")
    async def senddm(self, context, member: discord.Member, count: int, interval: int, message: str):
        if has_roles(context):
            embed = discord.Embed(
                description=f"`{member.name}` will be DMed {count} times, every {interval} minutes!",
                color=0x42F56C
            )
            await context.send(embed=embed)
            for i in range(count):
                await member.send(message)
                await asyncio.sleep(interval*60)

    @commands.command(name="enableautorole", description="Enables Auto-Role.")
    async def enableautorole(self, context, role: discord.Role):
        if has_roles(context):
            if role.id not in config['autoroles']:
                config['autoroles'].append(role.id)
            update_config()
            await context.send(embed=discord.Embed(description="Auto-role enabled!", color=0x00ff73))

    @commands.command(name="disbleautorole", description="Disables Auto-Role.")
    async def disbleautorole(self, context, role: discord.Role = None):
        if has_roles(context):
            if role is None:
                config['autoroles'] = []
            elif role.id in config['autoroles']:
                config['autoroles'].remove(role.id)
            else:
                await context.send('this role is not autorole')
                return
            update_config()
            await context.send(embed=discord.Embed(description="Auto-role disabled!", color=0xff0000))

    @commands.command(name="dmonline", description="DMs all online members.")
    async def dm_all(self, context, *, args):
        if has_roles(context):
            for i in context.guild.members:
                if i == self.bot.user or context.message.author.bot:
                    pass
                try:
                    if i.status == "online" or i.status == "idle":
                        print(i.name)
                        await i.send(embed=discord.Embed(description=args))
                except Exception as e:
                    print(e)
        await context.send(embed=discord.Embed(description="All online members were DMed."))

    @commands.command(name="resetinv", description="Resets top inviters.")
    async def resetinv(self, context):
        if has_roles(context):
            for invite in await context.guild.invites():
                await invite.delete()
            invite_uses[str(context.guild.id)] = []
            with open('invites.json', 'w') as fp:
                json.dump(invite_uses, fp)
            await context.send(embed=discord.Embed(description="Top Inviters were reset."))

    @commands.command(name="enablemanualrole", description="Enables manual role.")
    async def enablemanualrole(self, context):
        if has_roles(context):
            for member in context.guild.members:
                if len(member.roles) == 1:
                    await member.add_roles(context)
            await context.send(embed=discord.Embed(description="Added roles."))


def setup(bot):
    bot.add_cog(Owner(bot))
