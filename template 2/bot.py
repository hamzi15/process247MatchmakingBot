import asyncio
import json
import os
import platform
import sys
import time
from collections import defaultdict
import datetime
import re
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)

with open('invites.json', 'r') as o:
    invite_uses = json.load(o)

with open('warnings.json', 'r') as fp:
    warnings = json.load(fp)

with open('filterwords.txt', 'r', encoding='UTF-8') as fp:
    filterwords = fp.read().splitlines()

intents = discord.Intents.default()
intents.members = True
bot = Bot(command_prefix=config["bot_prefix"], intents=intents)
DISCORD_INVITE = r'discord(?:\.com|app\.com|\.gg)[\/invite\/]?(?:[a-zA-Z0-9\-]{2,32})'
epoch = datetime.datetime.utcfromtimestamp(0)
custom_invites = {}


def find_invite_by_code(invite_list, code):
    for inv in invite_list:
        if inv.code == code:
            return inv


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


def get_invites(message):
    regex = re.compile(DISCORD_INVITE)
    invites = regex.findall(message)
    return invites or None


@bot.event
async def on_ready():
    if not event_points.is_running():
        event_points.start()
    if not top_invites.is_running():
        top_invites.start()
    print(f"Logged in as {bot.user.name}")
    print(f"Discord.py API version: {discord.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")

bot.remove_command("help")
if __name__ == "__main__":  # loading the features of the bot
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                bot.load_extension(f"cogs.{extension}")
                print(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f"Failed to load extension {extension}\n{exception}")


@tasks.loop(hours=12)
async def event_points():
    counter = 0
    channel = bot.get_channel(int(config["channelids"]['points']))  # Insert channel ID here

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
        user = await bot.fetch_user(i[0])
        embed.add_field(name=f"{user.name}", value=f"{i[1]}", inline=False)
    await channel.send(embed=embed)


@tasks.loop(hours=12)
async def top_invites():
    counter = 0
    channel = bot.get_channel(int(config["channelids"]["invites"]))  # Insert channel ID here

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


@bot.event
async def on_message(message):  # executed when a message is sent by someone
    if message.author == bot.user or message.author.bot:
        return

    user_add_xp(message.author.id, 1, message)
    if get_invites(str(message.content)) is not None and config['invitefilterenabled']:
        if str(message.author.id) in warnings and warnings[str(message.author.id)][0] >= 3:
            warnings[str(message.author.id)] = [0]
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
            await message.delete()
            await message.author.send(embed=discord.Embed(
                description=f"**You have been banned from `{message.guild.name}` for spamming server invites.**",
                color=0xff0000))
            msg = await message.channel.send(embed=discord.Embed(
                description=f"**{message.author.mention} has been banned from the server for spamming server invites.**",
                color=0xff0000))
            time.sleep(5)
            await msg.delete()
            try:
                await message.guild.ban(message.author)
            except:
                msg = await message.channel.send(
                    embed=discord.Embed(description=f"**Missing Permissions to ban {message.author.mention}.**",
                                        color=0xff0000))
                time.sleep(5)
                await msg.delete()
            return
        elif str(message.author.id) in warnings and warnings[str(message.author.id)][0] < 3:
            warnings[str(message.author.id)][0] += 1
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
        else:
            warnings[str(message.author.id)] = [0]
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
        await message.delete()
        await message.author.send(embed=discord.Embed(
            description=f"**WARNING {message.author.mention}: YOU CAN'T SEND LINKS IN `{message.guild.name}`.**",
            color=0xff0000))
        msg = await message.channel.send(
            embed=discord.Embed(description=f"**WARNING {message.author.mention}: YOU CAN'T SEND LINKS HERE.**",
                                color=0xff0000))
        time.sleep(5)  # delay warning msg
        await msg.delete()

    if any([word in message.content.lower().strip() for word in filterwords]):
        curse_word = []
        for word in filterwords:
            if word in message.content.lower().strip():
                curse_word.append(word.upper())
        if str(message.author.id) in warnings and warnings[str(message.author.id)][0] >= 3:
            warnings[str(message.author.id)] = [0]
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
            await message.delete()
            await message.author.send(embed=discord.Embed(
                description=f"**You have been banned from `{message.guild.name}` for using banned words.**",
                color=0xff0000))
            msg = await message.channel.send(embed=discord.Embed(
                description=f"**{message.author.mention} has been banned from the server for using banned words.**",
                color=0xff0000))
            time.sleep(5)
            await msg.delete()
            try:
                await message.guild.ban(message.author)
            except:
                msg = await message.channel.send(
                    embed=discord.Embed(description=f"**Missing Permissions to ban {message.author.mention}.**",
                                        color=0xff0000))
                time.sleep(5)
                await msg.delete()
            return
        elif str(message.author.id) in warnings and warnings[str(message.author.id)][0] < 3:
            warnings[str(message.author.id)][0] += 1
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
        else:
            warnings[str(message.author.id)] = [0]
            with open('warnings.json', 'w') as fp:
                json.dump(warnings, fp)
        await message.delete()
        await message.author.send(embed=discord.Embed(
            description=f"**WARNING {message.author.mention}:** YOU CAN'T USE THE WORD/S: **```{', '.join(curse_word)}```**  IN **`{message.guild.name}`**.\n **DON'T REPEAT IT**.",
            color=0xff0000))
        msg = await message.channel.send(embed=discord.Embed(
            description=f"**WARNING {message.author.mention}:** YOU CAN'T USE THIS WORD HERE.\n **DON'T REPEAT IT**.",
            color=0xff0000))
        time.sleep(5)  # delay warning msg
        await msg.delete()
    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    if (datetime.datetime.now() - member.created_at).days < config['dayslimit']:
        await member.send(config['manualacceptmsg'])
        ma_channel = bot.get_channel(config['channelids']['manualaccept'])
        if ma_channel is None:
            print('No manual accept channel. Ignoring new user')
            return

        for i in member.guild.channels:
            await i.set_permissions(member, read_messages=False, send_messages=False)
        await ma_channel.set_permissions(member, read_messages=True, send_messages=True)
        return
    roles_to_add = [member.guild.get_role(i) for i in config['autoroles'] if member.guild.get_role(i) is not None]
    await member.add_roles(*roles_to_add)
    await member.send(embed=discord.Embed(description=config['welcomemsg'], color=0x123f90))

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


@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(config['channelids']['leave'])
    current_time = datetime.datetime.now()
    time = (current_time-member.joined_at).days

    if channel is None:
        print('No leave channel. Ignoring.')
        return
    await channel.send(embed=discord.Embed(description=f"{member.mention} left the server after {time} days!", color=0xff0000))
    custom_invites[member.guild.id] = await member.guild.invites()
    for invite in invite_uses[str(member.guild.id)]:
        if invite[2] == member.name:
            invite[1] -= 1
            return
    with open('invites.json', 'w') as fp:
        json.dump(invite_uses, fp)


@bot.event
async def on_command_completion(ctx):  # command executed successfully
    fullCommandName = ctx.command.qualified_name
    split = fullCommandName.split(" ")
    executedCommand = str(split[0])
    print(
        f"Executed {executedCommand} command in {ctx.guild.name} (ID: {ctx.message.guild.id}) by {ctx.message.author} (ID: {ctx.message.author.id})")


@bot.event
async def on_command_error(context, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(
            title="Please slow down!",
            description=f"You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
            color=0x8233FF
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Error!",
            description="You are missing the permission `" + ", ".join(
                error.missing_perms) + "` to execute this command!",
            color=0xFF3387
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Error!",
            description=str(error).capitalize(),
            color=0xFF5733
        )
        await context.send(embed=embed)
    raise error


bot.run(config["token"])
