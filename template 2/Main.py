from __future__ import print_function
import discord
from discord.ext import commands
from discord.ext.tasks import loop
from discord import Role
import asyncio
import random
import json
import datetime
import os
from collections import defaultdict
import time
from datetime import timedelta

import re


class HelpCommand(commands.DefaultHelpCommand):
    def __init__(self):
        super(HelpCommand, self).__init__()

    async def send_bot_help(self, mapping):
        if not id_in_userids(self.context.author.id):
            return

        embed = discord.Embed(title="Commands")
        embed.add_field(name="Giveaway",
                        value="!giveaway title| no.of winners | time (hours) | channel and |winner ids [optional]  ",
                        inline=False)
        embed.add_field(name="Top Inviters", value="!invites", inline=False)
        embed.add_field(name="Message Leaderboard", value="!lb", inline=False)
        embed.add_field(name="Resets Message Leaderboard", value="!reset", inline=False)
        embed.add_field(name="Resets Top Inviters", value="!resetinv", inline=False)
        embed.add_field(name="Give Roles", value="!enablemanualrole @role", inline=False)
        embed.add_field(name="Disable/Enable Autorole", value="!disableautorole @role\n!enableautorole @role",
                        inline=False)
        embed.add_field(name="Disable/Enable Invite Filter", value="!disableinvitefilter\n!enableinvitefilter",
                        inline=False)
        await self.context.send(embed=embed)


DISCORD_INVITE = r'discord(?:\.com|app\.com|\.gg)[\/invite\/]?(?:[a-zA-Z0-9\-]{2,32})'
intents = discord.Intents.all()
client = commands.Bot("!", intents=intents, help_command=HelpCommand())

with open('config.json', 'r') as fp:
    config = json.load(fp)
with open('warnings.json', 'r') as fp:
    warnings = json.load(fp)
with open('verified.json', 'r') as fp:
    verified = json.load(fp)
with open('filterwords.txt', 'r', encoding='UTF-8') as fp:
    filterwords = fp.read().splitlines()
with open('invites.json', 'r') as o:
    invite_uses = json.load(o)

custom_invites = {}
epoch = datetime.datetime.utcfromtimestamp(0)


def get_invites(message):
    regex = re.compile(DISCORD_INVITE)
    invites = regex.findall(message)
    return invites or None


def find_invite_by_code(invite_list, code):
    for inv in invite_list:
        if inv.code == code:
            return inv


def id_in_userids(uid):
    return uid in config['userids']


def update_config():
    with open('config.json', 'w') as fp:
        json.dump(config, fp)


def seperArgs(arg, delimeter):
    finalArgs = []
    toAppend = ''
    index = 0
    for i in arg:
        if (i == delimeter):
            finalArgs.append(toAppend.strip())
            toAppend = ''
        else:
            toAppend += i
        if (index == len(arg) - 1):
            finalArgs.append(toAppend.strip())
            toAppend = ''
        index += 1
    return finalArgs


def user_add_xp(user_id, xp, message):
    if os.path.isfile('user.json'):
        user_id = str(user_id)
        with open('user.json', 'r') as fp:
            users = json.load(fp)
        if users.get(str(user_id)) is not None:
            if users[user_id]['msg'] <= 2 and len(message.content.split()) > 20:
                users[user_id]['xp'] += xp
                users[user_id]['xp_time'] = (datetime.datetime.utcnow() - epoch).total_seconds()
                users[user_id]['msg'] += 1
                with open('user.json', 'w') as fp:
                    json.dump(users, fp)
            else:
                time_diff = (datetime.datetime.utcnow() - epoch).total_seconds() - users[user_id]['xp_time']
                if time_diff >= 3600:
                    users[user_id]['xp'] += xp
                    users[user_id]['xp_time'] = (datetime.datetime.utcnow() - epoch).total_seconds()
                    users[user_id]['msg'] = 0
                    with open('user.json', 'w') as fp:
                        json.dump(users, fp)

        else:
            if len(message.content.split()) > 20:
                users[user_id] = {}
                users[user_id]['xp'] = xp
                users[user_id]['xp_time'] = (datetime.datetime.utcnow() - epoch).total_seconds()
                users[user_id]['msg'] = 1
                with open('user.json', 'w') as fp:
                    json.dump(users, fp)


@client.event
async def on_ready():
    print('logged on')
    print('Starting tasks')
    event_points.start()
    top_invites.start()
    background_task.start()
    for guild in client.guilds:
        try:
            custom_invites[guild.id] = await guild.invites()
            if str(guild.id) not in invite_uses:
                invite_uses[str(guild.id)] = []
                with open('invites.json', 'w') as fp:
                    json.dump(invite_uses, fp)
        except Exception:
            pass


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_add_xp(message.author.id, 1, message)
    if get_invites(str(message.content)) is not None and config['invitefilterenabled']:
        if str(message.author.id) in warnings and warnings[str(message.author.id)][0] >= 3:
            warnings[str(message.author.id)] = [0]
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
            await message.guild.ban(message.author)
        elif str(message.author.id) in warnings and warnings[str(message.author.id)][0] < 3:
            warnings[str(message.author.id)][0] += 1
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
        else:
            warnings[str(message.author.id)] = [0]
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
        await message.delete()
        msg = await message.channel.send(embed=discord.Embed(description=f"WARNING {message.author.mention}: YOU "
                                                                         f"CAN'T SEND LINKS HERE."))
        time.sleep(5)  # delay warning msg
        await msg.delete()

    if any([word in message.content.lower() for word in filterwords]):
        if str(message.author.id) in warnings and warnings[str(message.author.id)][0] >= 3:
            warnings[str(message.author.id)] = [0]
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
            await message.guild.ban(message.author)
        elif str(message.author.id) in warnings and warnings[str(message.author.id)][0] < 3:
            warnings[str(message.author.id)][0] += 1
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
        else:
            warnings[str(message.author.id)] = [0]
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
        await message.delete()
        msg = await message.channel.send(f"WARNING {message.author.mention}: YOU CAN'T USE THIS WORD. DONT REPEAT IT.")
        time.sleep(5)  # delay warning msg
        await msg.delete()
    await client.process_commands(message)


@client.event
async def on_member_remove(member):
    channel = client.get_channel(config['channelids']['leave'])

    if channel is None:
        print('No leave channel. Ignoring.')
        return

    await channel.send(f"{member.name} left the server")
    custom_invites[member.guild.id] = await member.guild.invites()
    for invite in invite_uses[str(member.guild.id)]:
        if invite[2] == member.name:
            invite[1] -= 1
            return
    with open('invites.json', 'w') as fp:
        json.dump(invite_uses, fp)


@client.event
async def on_member_join(member):
    if (datetime.datetime.now() - member.created_at).days < config['dayslimit']:
        await member.send(config['manualacceptmsg'])
        ma_channel = client.get_channel(config['channelids']['manualaccept'])
        if ma_channel is None:
            print('No manual accept channel. Ignoring new user')
            return

        for i in member.guild.channels:
            await i.set_permissions(member, read_messages=False, send_messages=False)
        await ma_channel.set_permissions(member, read_messages=True, send_messages=True)
        return

    roles_to_add = [member.guild.get_role(i) for i in config['autoroles'] if member.guild.get_role(i) is not None]
    await member.add_roles(*roles_to_add)

    await member.send(config['welcomemsg'])

    invites_before_join = custom_invites[member.guild.id]
    invites_after_join = await member.guild.invites()
    if len(invites_before_join) == 0:
        for invite in invites_after_join:
            tup = [invite.inviter.name, 1, member.name, 'test']
            invite_uses[str(member.guild.id)].append(tup)
            with open('invites.json', 'w') as fp:
                json.dump(invite_uses, fp)
            return
    for invite in invites_before_join:
        if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:
            custom_invites[member.guild.id] = invites_after_join
            for i in invite_uses[str(member.guild.id)]:
                if invite.inviter.name == i[0] and member.name == i[2]:
                    i[1] += 1
                    with open('invites.json', 'w') as fp:
                        json.dump(invite_uses, fp)
                    return
            tup = [invite.inviter.name, 1, member.name, 'test']
            invite_uses[str(member.guild.id)].append(tup)
            with open('invites.json', 'w') as fp:
                json.dump(invite_uses, fp)
            return
        else:
            custom_invites[member.guild.id] = invites_after_join
            tup = [invite.inviter.name, 1, member.name, 'test']
            invite_uses[str(member.guild.id)].append(tup)
            with open('invites.json', 'w') as fp:
                json.dump(invite_uses, fp)
            return


@loop(hours=12)
async def event_points():
    counter = 0
    channel = client.get_channel(int(config["channelids"]['points']))  # Insert channel ID here

    if channel is None:
        print("No points channel. Stopping event_points task.")
        event_points.cancel()
        return

    counter += 1
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
        user = await client.fetch_user(i[0])
        embed.add_field(name=f"{user.name}", value=f"{i[1]}", inline=False)
    await channel.send(embed=embed)


@loop(hours=12)
async def top_invites():
    counter = 0
    channel = client.get_channel(int(config["channelids"]["invites"]))  # Insert channel ID here

    if channel is None:
        print('No top invites channel. Stopping top_invites task.')
        top_invites.cancel()
        return

    counter += 1
    await asyncio.sleep(10)
    d = defaultdict(int)
    if len(invite_uses[str(channel.guild.id)]) != 0:
        users = invite_uses[str(channel.guild.id)]
    else:
        users = []
    for i in users:
        if i[1] == 0:
            users.remove(i)
    for t in users:
        d[(t[0], t[-1])] += t[1]
    result = [(k[0], d[k], k[1]) for k in d]
    users = result
    users.sort(key=lambda x: x[1], reverse=True)
    list2 = users[:10]
    embed = discord.Embed(title="Top Inviters")
    for i in list2:
        embed.add_field(name=f"{i[0]}", value=f"{i[1]}", inline=False)
    await channel.send(embed=embed)


@loop(seconds=1)
async def background_task():
    global config
    counter = 0
    channel = client.get_channel(774303797593768026)  # Insert channel ID here

    if channel is None:
        print('No repeatmsg channel. Stopping bg_task.')
        background_task.cancel()
        return

    await channel.send(config['repeatmsg'])
    while not client.is_closed():
        counter += 1
        await asyncio.sleep(1)


class Giveaway(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def giveaway(self, ctx):
        if not id_in_userids(ctx.author.id):
            return

        arguements = seperArgs(ctx.message.content, '|')
        arguements[0] = arguements[0].replace("!giveaway", '')
        x = arguements[3]
        id = []
        for i in x:
            if i != "<" and i != "#" and i != ">":
                id.append(i)
        id = "".join(id)
        channel = client.get_channel(int(id))
        giveawayembed = discord.Embed(
            title=arguements[0],
            colour=discord.Color.green()
        )
        win = []
        if len(arguements) >= 5:
            for i in arguements[4].split():
                win.append(i)
        timing = datetime.datetime.now() + timedelta(hours=int(arguements[2]))
        giveawayembed.add_field(name="Hosted by", value=f"{ctx.author.mention}", inline=False)
        giveawayembed.add_field(name="Ends in", value=f"{arguements[2]}h | {timing.hour}:{timing.minute}")
        msg = await channel.send(embed=giveawayembed)
        await msg.add_reaction("🎉")
        await asyncio.sleep(int(arguements[2]) * 3600)
        msg = await msg.channel.fetch_message(msg.id)
        for reaction in msg.reactions:
            if reaction.emoji == "🎉":
                users = await reaction.users().flatten()
                if self.client.user in users:
                    users.remove(self.client.user)

                for i, word in enumerate(users):
                    users[i] = word.id
                if len(win) != 0:
                    for i in win:
                        if int(i) in users:
                            users.remove(int(i))
                if len(users) == 0 or len(users) < int(arguements[1]):
                    await channel.send(f"Couldn't determine a winner.")
                    endembed = discord.Embed(
                        title="Giveaway ended!",
                    )
                    endembed.add_field(name="winners", value="NONE")
                    await msg.edit(embed=endembed)
                    return
                winner = random.choices(users, k=int(arguements[1]) - len(win))
                endembed = discord.Embed(
                    title="Giveaway ended!",
                )
                for i, word in enumerate(winner):
                    winner[i] = "<@" + str(word) + ">"
                if len(win) != 0:
                    for i in win:
                        winner.append("<@" + str(i) + ">")
                endembed.add_field(name="winners", value=" ".join(winner))
                winn = " ".join(winner)
                await channel.send(f"Winners: {winn}")
                await channel.send(f"Winner pls contact {ctx.author.mention}")

        await msg.edit(embed=endembed)

    @giveaway.error
    async def giveaway_error(self, ctx, error):
        await ctx.send(error)


@client.command()
async def resetinv(ctx):
    for invite in await ctx.guild.invites():
        await invite.delete()
    invite_uses[str(ctx.guild.id)] = []
    with open('invites.json', 'w') as fp:
        json.dump(invite_uses, fp)


@client.command()
async def invites(ctx):
    if not id_in_userids(ctx.author.id):
        return

    if len(invite_uses[str(ctx.guild.id)]) != 0:
        users = invite_uses[str(ctx.guild.id)]
    else:
        users = []
    d = defaultdict(int)
    for i in users:
        if i[1] == 0:
            users.remove(i)
    for t in users:
        d[(t[0], t[-1])] += t[1]
    result = [(k[0], d[k], k[1]) for k in d]
    users = result
    users.sort(key=lambda x: x[1], reverse=True)
    list2 = users[:10]
    embed = discord.Embed(title="Top Inviters")
    for i in list2:
        embed.add_field(name=f"{i[0]}", value=f"{i[1]}", inline=False)
    await ctx.send(embed=embed)


@client.command()
async def reset(ctx):
    if not id_in_userids(ctx.author.id):
        return
    with open('user.json', 'w') as fp:
        json.dump({}, fp)


@client.command()
async def lb(ctx):
    if not id_in_userids(ctx.author.id):
        return

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
        user = await client.fetch_user(str(i[0]))
        embed.add_field(name=f"{user.name}", value=f"{i[1]}", inline=False)
    await ctx.send(embed=embed)


@client.command()
async def enablemanualrole(ctx, role: Role):
    for member in ctx.guild.members:
        if len(member.roles) == 1:
            await member.add_roles(role)
    await ctx.send("added roles")


@client.command()
async def enableautorole(ctx, role: Role):
    if role.id not in config['autoroles']:
        config['autoroles'].append(role.id)
    update_config()
    await ctx.send("autorole enabled")


@client.command()
async def disableautorole(ctx, role: Role = None):
    if role is None:
        config['autoroles'] = []
    elif role.id in config['autoroles']:
        config['autoroles'].remove(role.id)
    else:
        await ctx.send('this role is not autorole')
        return
    update_config()
    await ctx.send("autorole disabled")


@client.command()
async def enableinvitefilter(ctx):
    config['invitefilterenabled'] = True
    update_config()
    await ctx.send("invite filter enabled")


@client.command()
async def disableinvitefilter(ctx):
    config['invitefilterenabled'] = False
    update_config()
    await ctx.send("invite filter disabled")


async def on_command_error(ctx, err):
    await ctx.send(f'ERROR: {err}')


client.on_command_error = on_command_error
client.add_cog(Giveaway(client))
client.run(config['token'])
