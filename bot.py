import datetime
import json
import os
import platform
import sys
import random

import string
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from discord.utils import get

from utils.db import dbAction
from utils.matchmaking import MatchMaking
from utils.queue import Queue
from utils.stats import Stats

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)

intents = discord.Intents.all()
intents.members = True
bot = Bot(command_prefix=config["bot_prefix"], intents=intents)
queue = Queue()  # Queue object initialization
db = dbAction()


@bot.event
async def on_ready():
    if not status_task.is_running():
        status_task.start()
    print('Logged in as ' + bot.user.name)
    print(f"Discord.py API version: {discord.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")


@tasks.loop(minutes=1.0)
async def status_task():  # to set a game's status
    statuses = ["with you!", "with Riot API!", "with humans!"]
    await bot.change_presence(activity=discord.Game(random.choice(statuses)))


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    print('inside on voice state')
    lobby_channel = config['channel_ids']['lobby_channel_id']

    try:
        if before.channel is not None and before.channel.id == lobby_channel and after.channel is None:  # pop member from queue if they leave the lobby
            print('inside on voice state if member leaves the lobby')
            if member in queue.lst:
                queue.lst.remove(member)
            print(f'{member.name} left the lobby')
    except:
        print('passing from member joined lobby')
        pass

    if before.channel is None and after.channel is not None:  # if member joins the lobby
        if after.channel.id == lobby_channel:
            print('inside on voice state if member joins')
            print(f'{member.name} joined the lobby')
            matchmakingObj = MatchMaking()

            lobby_channel = member.voice.channel
            queue.push(member)
            no_of_members = len(lobby_channel.members)
            if no_of_members >= 10:
                no_of_members -= 10
                list_of_players = list()
                for i in range(10):
                    list_of_players.append(queue.pop())

                captain = None

                no_rank_members = matchmakingObj.prepare_roles_ranks(list_of_players)
                if no_rank_members:
                    for member in no_rank_members:
                        response = await MatchMaking.fetch_rank(member)
                        if not response:
                            # League ID does not exist need to remove member from lobby.
                            list_of_players.remove(member)
                            for player in list_of_players:
                                queue.push(player)
                            await member.move_to(get(member.guild.channels, id=879421470869192785))
                            await member.send(embed=discord.Embed(color=0xff000,
                                                                  description="*We couldn't find you in LoL database. If you are registered with LoL then please add your league id in your server nickname, i.e. '[ADA] P429'. AND register with Orianna Bot in the server.\nOR\nContact the server admins.*"))
                            return
                        else:
                            matchmakingObj.dict_of_players[member][0] = MatchMaking.rank_value(response)
                            if not captain:
                                captain = member
                    if not captain:
                        captain = list_of_players[random.randint(0, 9)]

                red, blue = matchmakingObj.matchmaker(list_of_players)
                red_channel, blue_channel, text_channel, role, password, lobby_name = await create_channels(
                    member.guild)
                await db.write_to_db(lobby_name, red, blue, captain.id)
                embed = discord.Embed(color=random.randint(0, 0xffff), description="⏳ Matchmaking...")
                embed.timestamp = datetime.datetime.now()
                msg = await text_channel.send(embed=embed)
                for key in red:
                    await red[key].add_roles(role)
                    await red[key].move_to(red_channel)
                for key in blue:
                    await blue[key].add_roles(role)
                    await blue[key].move_to(blue_channel)
                teams_and_roles_description = await get_description(red, blue, password, role.name, captain.id)
                embed.description = teams_and_roles_description
                log_channel = get(member.guild.channels, name=config["log_channel_id"])
                await log_channel.send(embed=embed)
                await msg.edit(embed=embed)

    try:
        if (after.channel and before.channel) and (before.channel.type == 'voice' and after.channel.type == 'voice') and \
                (('blue side' in str(before.channel.name).lower() and 'red side' in str(after.channel.name).lower()) or
                 ('blue side' in str(before.channel.name).lower() and 'red side' in str(after.channel.name).lower())):
            # if member changes team voice channel, i.e. from red side to blue side or vice versa
            try:
                print("inside member changed teams channels")
                await member.move_to(before.channel)
                await member.send(embed=discord.Embed(color=0xff0000, description="**WARNING**\n" \
                                                                                  "You can't join the other teams voice channel.\n\n"
                                                                                  "**Don't do it again. Tha admins are notified.**"))
                # await db.write_lb_stats(member_summoner_id=)
            except Exception as e:
                print(e)
    except:
        print('passing from member changed teams')
        pass

    try:
        if (after.channel is None or after.channel.type == 'voice') and before.channel is not None and (
                'red side' in str(before.channel.name).lower() or 'blue side' in str(before.channel.name).lower()):
            print("inside delete category and role")

            # role_category_name = str(before.channel.category.name)
            # role = get(member.guild.roles, name=role_category_name)
            # await member.remove_roles(role)  # if member leaves a match voice channel, remove secret role

            channel = before.channel
            if not channel.members:  # delete category and empty voice channels
                flag = True
                list_of_category_channels = channel.category.channels
                for category_channel in list_of_category_channels:
                    if category_channel != channel and str(category_channel.type) != "text":
                        if category_channel.members:
                            flag = False
                            break
                        else:
                            continue
                if flag:
                    red, blue, captain_id = await db.get_teams(channel.category.name)
                    latest_match_stats = Stats.get_stats(red, blue)
                    embed = get_stats_embed(latest_match_stats, get(member.guild.members, captain.id),
                                            channel.category.name)
                    print('Stats description: ', embed.description)
                    # send match stats to relevant channels during the final touches (ask the customer)
                    await db.write_stats(latest_match_stats,"monthly-stats")
                    await db.write_stats(latest_match_stats,"weekly-stats")
                    await db.write_stats(latest_match_stats,"overall-stats")
                    await db.write_stats(latest_match_stats,"daily-stats")
                    
                    for channel in list_of_category_channels:
                        await channel.delete()
                    await channel.category.delete()
                    await remove_roles(channel.category.name, member.guild, red, blue)
    except:
        print('passing from delete category')
        pass


def get_stats_embed(stats, captain, match_id):
    embed = discord.Embed(color=random.randint(0, 0xff0000))
    description = f'**Match ID:** {match_id}\n\n' \
                  f'**Captain:** {captain.name}\n' \
                  f'**Winner:** {stats["win"]}\n\n' \
                  f"**Kill Deaths Assists CreepScore PentaKills QuadraKills**\n"
    for discord_id in stats:
        description += f"{stats[discord_id]['kills']} {stats[discord_id]['deaths']} {stats[discord_id]['assists']} {stats[discord_id]['creepScore']} {stats[discord_id]['pentaKills']} {stats[discord_id]['quadraKills']}\n"

    embed.description = description
    return embed


async def remove_roles(category_name, guild, red, blue):
    role_to_delete = get(guild.roles, name=category_name)
    for key in red:
        red[key].remove_roles(role_to_delete)
        blue[key].remove_roles(role_to_delete)  # remove the role when the channels are empty


async def get_description(red, blue, password, match_name, captain_id):
    try:
        description = f"**⚔️Teams and Roles**\n\n" \
                      f"**Captain:** <!@{captain_id}>\n\n" \
                      f"**🔴 Red Side: **\n" \
                      f"   Top     - <!@{red['top'].id}>\n" \
                      f"   Jungle  - <!@{red['jungle'].id}>\n" \
                      f"   Mid     - <!@{red['mid'].id}>\n" \
                      f"   ADC     - <!@{red['adc'].id}>\n" \
                      f"   Support - <!@{red['support'].id}>\n\n" \
                      f"**🔵 Blue: **\n" \
                      f"   Top     - <!@{blue['top'].id}>\n" \
                      f"   Jungle  - <!@{blue['jungle'].id}>\n" \
                      f"   Mid     - <!@{blue['mid'].id}>\n" \
                      f"   ADC     - <!@{blue['adc'].id}>\n" \
                      f"   Support - <!@{blue['support'].id}>\n\n\n" \
                      f"Match Name: {match_name}" \
                      f"Password: {password}"
        await get_attention(queue.__len__())
        return description
    except:
        await get_attention(queue.__len__())
        return "Sample message since we don't have 10 members right now."


async def get_attention(no_of_members):
    get_attention_channel = config['channel_ids']['get_attention_channel_id']
    channel = bot.get_channel(get_attention_channel)  # id of the attention channel
    embed = discord.Embed(color=random.randint(0, 0xffff),
                          description='            **ATTENTION**\nA new match has just started.\n\n')
    embed.add_field(name="Number of subs remaining",
                    value=f"{no_of_members}\n\n")
    embed.set_footer(text="Join lobby now to start a new match")
    embed.timestamp = datetime.datetime.now()
    await channel.send(content='@everyone', embed=embed)


def generate_name_password():
    name = f"{config['lobby_name']} | {config['lobby_number']}"
    password = ''
    for x in range(11):
        password += random.choice(string.ascii_letters + string.digits)
    config['lobby_number'] += 1
    with open('config.json', 'w') as file:
        json.dump(config, file)
        file.close()
    return name, password


async def create_channels(guild):
    role_category_name, password = generate_name_password()
    category = await guild.create_category(name=role_category_name)
    role = await guild.create_role(name=role_category_name)
    await category.set_permissions(role, read_messages=True, send_messages=True, connect=True, speak=True)

    # make category accessible only to people with a specific role which we generate. The name of
    # the category and role must be the same

    # await category.set_permissions(guild.default_role, read_messages=False, connect=False)

    red = await category.create_voice_channel(name=config['vc1'], bitrate=96000, user_limit=5)
    await red.set_permissions(role, connect=True, speak=True)
    await red.set_permissions(guild.default_role, connect=False, speak=False)

    blue = await category.create_voice_channel(name=config['vc2'], bitrate=96000, user_limit=5)
    await blue.set_permissions(role, connect=True, speak=True)
    await blue.set_permissions(guild.default_role, connect=False, speak=False)

    text_channel = await category.create_text_channel(name=config['tc'])
    await text_channel.set_permissions(role, read_messages=True, send_messages=True, connect=True, speak=True)
    await text_channel.set_permissions(guild.default_role, read_messages=False, send_messages=False, connect=False,
                                       speak=False)

    return red, blue, text_channel, role, password, role_category_name


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
