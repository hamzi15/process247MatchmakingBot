import discord
from discord.ext import commands
import json
import os
import sys

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


class ModerationCog(commands.Cog, name="moderation"):
    def __init__(self, bot):
        self.bot = bot

    # kick out a user from the server
    @commands.command(name='kick', pass_context=True, description="Kick out a user")
    async def kick(self, context, member: discord.Member, *, reason="Not specified"):
        if has_roles(context):
            if member.guild_permissions.administrator:
                embed = discord.Embed(
                    title="Error!",
                    description="User has Admin permissions.",
                    color=0x541760
                )
                await context.send(embed=embed)
            else:
                try:
                    await member.kick(reason=reason)
                    embed = discord.Embed(
                        title="User Kicked!",
                        description=f"**{member}** was kicked by **{context.message.author}**!",
                        color=0x42F56C
                    )
                    embed.add_field(
                        name="Reason:",
                        value=reason
                    )
                    await context.send(embed=embed)
                    try:
                        await member.send(
                            f"You were kicked by **{context.message.author}**!\nReason: {reason}"
                        )
                    except:
                        pass
                except:
                    embed = discord.Embed(
                        title="Error!",
                        description="An error occurred while trying to kick the user. Make sure my role is above the role "
                                    "of the user you want to kick.",
                        color=0x541760
                    )
                    await context.message.channel.send(embed=embed)

    # change the nickname of a user
    @commands.command(name="nickname", description="Change the nickname of a user")
    async def nickname(self, context, member: discord.Member, *, nickname=None):
        if has_roles(context):
            try:
                await member.edit(nick=nickname)
                embed = discord.Embed(
                    title="Changed Nickname!",
                    description=f"**{member}'s** new nickname is **{nickname}**!",
                    color=0x42F56C
                )
                await context.send(embed=embed)
            except:
                embed = discord.Embed(
                    title="Error!",
                    description="An error occurred while trying to change the nickname of the user. Make sure my role is "
                                "above the role of the user you want to change the nickname.",
                    color=0x541760
                )
                await context.message.channel.send(embed=embed)


    # ban a user
    @commands.command(name="ban", description="Ban a user")
    async def ban(self, context, member: discord.Member, *, reason="Not specified"):
        if has_roles(context):
            try:
                if member.guild_permissions.administrator:
                    embed = discord.Embed(
                        title="Error!",
                        description="User has Admin permissions.",
                        color=0x541760
                    )
                    await context.send(embed=embed)
                else:
                    await member.ban(reason=reason)
                    embed = discord.Embed(
                        title="User Banned!",
                        description=f"**{member}** was banned by **{context.message.author}**!",
                        color=0x42F56C
                    )
                    embed.add_field(
                        name="Reason:",
                        value=reason
                    )
                    await context.send(embed=embed)
                    await member.send(f"You were banned by **{context.message.author}**!\nReason: {reason}")
            except:
                embed = discord.Embed(
                    title="Error!",
                    description="An error occurred while trying to ban the user. Make sure my role is above the role of "
                                "the user you want to ban.",
                    color=0x541760
                )
                await context.send(embed=embed)

    # warn a user in their DMs
    @commands.command(name="warn",
                      description="Warn a user in their DMs. Has an extra reason argument followed by the member's @.")
    async def warn(self, context, member: discord.Member, *, reason="Not specified"):
        if has_roles(context):
            embed = discord.Embed(
                title="User Warned!",
                description=f"**{member}** was warned by **{context.message.author}**!",
                color=0x42F56C
            )
            embed.add_field(
                name="Reason:",
                value=reason
            )
            await context.send(embed=embed)
            try:
                await member.send(f"You were warned by **{context.message.author}**!\nReason: {reason}")
            except:
                pass

    # delete an n number of messages
    @commands.command(name="clear", description="Deletes an n number of messages")
    async def clear(self, context, amount):
        if has_roles(context):
            channel = context.message.channel
            try:
                amount = int(amount)+1
            except:
                embed = discord.Embed(
                    title="Error!",
                    description=f"`{amount}` is not a valid number.",
                    color=0x541760
                )
                await context.send(embed=embed)
                return
            if amount < 1:
                embed = discord.Embed(
                    title="Error!",
                    description=f"`{amount}` is not a valid number.",
                    color=0x541760
                )
                await context.send(embed=embed)
                return
            purged_messages = await channel.purge(limit=amount)
            embed = discord.Embed(
                title="Chat Cleared!",
                description=f"**{context.message.author}** cleared **{len(purged_messages)-1}** messages!",
                color=0x541760
            )
            await context.send(embed=embed)

    # dm's a user
    @commands.command(name="dm", description="DMs a user. Syntax: !dm [member @] [message]")
    async def dm(self, context, member: discord.Member, *, message):
        if has_roles(context):
            embed = discord.Embed(
                description=f"{message}",
                color=0xD5059D
            )
            try:
                # To know what permissions to give to your bot, please see here: https://discordapi.com/permissions.html and remember to not give Administrator permissions.
                await member.send(embed=embed)
                await context.send(f"I sent {member.display_name} a private message!")
            except discord.Forbidden:
                await context.send(embed=embed)


def setup(bot):
    bot.add_cog(ModerationCog(bot))
