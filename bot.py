import datetime
import json
import os
import platform
import sys
import random

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot

from utils.matchmaking import MatchMaking
from utils.queue import Queue

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)

intents = discord.Intents.all()
intents.members = True
bot = Bot(command_prefix=config["bot_prefix"], intents=intents)
queue = Queue()  # Queue object initialization



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


async def add_to_spectator_channel(user: discord.Member):
    spectator_channel_id = config['spectator_channel_id']
    channel = bot.get_channel(spectator_channel_id).add_member(user)
    return channel


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    print('inside on voice state')
    lobby_channel = config['channel_ids']['lobby_channel_id']
    if before.channel is None and after.channel is not None:
        if after.channel.id == lobby_channel:
            print('inside on voice state if')
            lobby_channel = member.voice.channel
            queue.push(member)
            no_of_members = len(lobby_channel.members)
            if no_of_members >= 10:
                no_of_members -= 10
                list_of_players = list()
                if queue.__len__() == 10:
                    while queue.__len__():
                        list_of_players.append(queue.pop())
                matchmakingObj = MatchMaking()
                red, blue = matchmakingObj.matchmaker(
                    list_of_players)  # red_blue_team_looks_like_this = { 'role': 'discord_id', 'role2': 'discord_id2'}
                # CURRENTLY red_blue_team_looks_like_this = { role': memberobj, 'role2': memberobj}
                red_channel, blue_channel, text_channel = create_channels(member.guild)
                embed = discord.Embed(color=random.randint(0, 0xffff), description="⏳ Matchmaking...")
                embed.timestamp = datetime.datetime.now()
                msg = await text_channel.send(embed)
                for key in red:
                    await red[key].move_to(red_channel.id)
                for key in blue:
                    await blue[key].move_to(blue_channel.id)
                teams_and_roles_description = get_description(red, blue)
                embed.description = teams_and_roles_description
                await msg.edit(embed=embed)
                await get_attention(no_of_members)


def get_description(red, blue):
    description = f"**Teams and Roles**\n\n" \
                  f"**:red_circle: Red Side**\n" \
                  f"   Top     - <!@{red['top'].id}>\n" \
                  f"   Jungle  - <!@{red['jungle'].id}>\n" \
                  f"   Mid     - <!@{red['mid'].id}>\n" \
                  f"   ADC     - <!@{red['adc'].id}>\n" \
                  f"   Support - <!@{red['support'].id}>\n\n" \
                  f"**:blue_circle: Blue Side**\n" \
                  f"   Top     - <!@{blue['top'].id}>\n" \
                  f"   Jungle  - <!@{blue['jungle'].id}>\n" \
                  f"   Mid     - <!@{blue['mid'].id}>\n" \
                  f"   ADC     - <!@{blue['adc'].id}>\n" \
                  f"   Support - <!@{blue['support'].id}>\n"
    return description


async def get_attention(no_of_members):
    get_attention_channel = config['channel_ids']['get_attention_channel_id']
    channel = bot.get_channel(get_attention_channel)  # id of the attention channel
    embed = discord.Embed(color=random.randint(0, 0xffff),
                          description='            **ATTENTION**\n\nA new match has just started.\n')
    embed.add_field(name="Number of subs remaining in the lobby",
                    value=f"{no_of_members}\n")
    embed.set_footer(text="*Join lobby now to start a new match*")
    embed.timestamp = datetime.datetime.now()
    await channel.send(content='@everyone', embed=embed)


def generate_name():
    name = f"Process247 Lobby {config['lobby_number']}"
    config['lobby_number'] += 1
    with open('config.json', 'w') as file:
        json.dump(config, file)
        file.close()
    return name


def create_channels(guild):
    category = guild.create_category(name=generate_name())
    red = category.create_voice_channel(name=":red_circle: • Red Side", bitrate=95, user_limit=5)
    blue = category.create_voice_channel(name=":blue_circle: • Blue Side", bitrate=95, user_limit=5)
    text_channel = category.create_text_channel(name=":crossed_swords: Teams And Roles")
    return red, blue, text_channel


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


#
# @bot.event
# async def on_member_join(member):
#


# @bot.event
# async def on_member_remove(member):


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
