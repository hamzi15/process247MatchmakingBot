import asyncio
import datetime
import json
import os
import platform
import sys
import random
import string
import re

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot
from discord.utils import get

from utils.db import dbAction
from utils.matchmaking import MatchMaking
from utils.stats import Stats

if not os.path.isfile("config.json") and not os.path.isfile('cache.json'):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json", encoding="cp866") as file:
        config = json.load(file)
    with open("cache.json", encoding="cp866") as file:
        cache = json.load(file)

intents = discord.Intents.all()
intents.members = True
bot = Bot(command_prefix=config["bot_prefix"], intents=intents)
queue_dict = {}
for i in config['channel_ids']['lobby_channel_ids']:
    queue_dict[int(i)] = []
db = dbAction()


@bot.event
async def on_ready():
    if not update_cache.is_running():
        update_cache.start()
    if not status_task.is_running():
        status_task.start()
    for i in config['channel_ids']['lobby_channel_ids']:
        channel = get(bot.get_all_channels(), id=i)
        if channel.members:
            for member in channel.members:
                await on_voice_channel_connect(member, channel)

    print('Logged in as ' + bot.user.name)
    print(f"Discord.py API version: {discord.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")


@tasks.loop(hours=10)
async def update_cache():
    for member in bot.get_all_members():
        if not member.bot:
            retrieved_roles = set_roles(member)
            print('inside update_cache')
            cache[str(member.id)] = {'display_name': str(member.display_name), 'rank_valuation': await fetch_info(member),
                                     'primary_role': retrieved_roles[0],
                                     'secondary_role': retrieved_roles[1]}

        # Can be `value`, "no_summoner", "unranked", "less_than_50"
    with open('cache.json', 'w') as file:
        json.dump(cache, file, indent=4)
        file.close()


async def fetch_info(member):
    response = await MatchMaking.fetch_rank(member)
    if not response:
        # Players league id is not in name has to be removed
        return 'no_summoner'
    else:
        tier, rank, wins, losses, lp = None, None, None, None, None
        for info in response:
            try:
                if info['queueType'] == "RANKED_SOLO_5x5":
                    tier = info['tier']
                    rank = info['rank']
                    wins = info["wins"]
                    losses = info["losses"]
                    lp = info["leaguePoints"]
            except:
                pass
        if not tier:
            # Unranked Player has to be removed
            return 'unranked'
        else:
            ans = MatchMaking.player_valuation(tier, rank, wins, losses, lp)
            if not ans:
                # Player has played less than 50 matches in total has to removed
                return 'less_than_50'
            else:
                return ans


def set_roles(member):
    print('inside set_roles')
    print(member.display_name)
    lol_roles = ['top', 'jungle', 'mid', 'adc', 'support']
    retrieved_roles = ['primary', 'secondary']

    if '[' in member.display_name or ']' in member.display_name:
        main = re.split('[\[\] ]+', member.display_name)[1]
        if main.lower() in lol_roles:
            retrieved_roles[0] = main
    for role in member.roles:
        # print(role.name)
        if role.name.startswith('Mains ') and role.name[6:].lower().rstrip() in lol_roles \
                and retrieved_roles[0] == 'primary':
            retrieved_roles[0] = role.name[6:]
        elif role.name.lower().rstrip() in lol_roles:
            retrieved_roles[1] = role.name
    print(retrieved_roles)
    return retrieved_roles


@tasks.loop(minutes=1.0)
async def status_task():  # to set a game's status
    statuses = ["with you!", "with Riot API!", "with humans!"]
    await bot.change_presence(activity=discord.Game(random.choice(statuses)))


@bot.event
async def on_voice_channel_disconnect(member, channel):
    print('inside on_voice_channel_disconnect')
    lobby_channels = config['channel_ids']['lobby_channel_ids']
    if channel.id in lobby_channels:
        for key in queue_dict:  # removing member from queue
            if member in queue_dict[key]:
                queue_dict[key].remove(member)
                print(f'{member.name} left the lobby')
                break


not_eligible_members = []


@bot.event
async def on_voice_channel_connect(member, channel):
    global not_eligible_members
    lobby_channels = config['channel_ids']['lobby_channel_ids']
    print('inside on_voice_channel_connect')
    if channel.id in lobby_channels:
        print(f'{member.name} joined {channel.name} lobby')
        matchmakingObj = MatchMaking()
        queue_dict[channel.id].append(member)  # get the relevant list from queue dict
        if len(channel.members) >= 10:
            list_of_players = list(set(queue_dict[channel.id][0:10]))
            queue_dict[channel.id] = list(set(queue_dict[channel.id][10:]))

            lobby_channel = get(bot.get_all_channels(), id=channel.id)
            assert len(lobby_channel.members) >= 10, "Members less than 10 in lobby"
            for member in list_of_players:
                try:
                    rank_valuation = cache[str(member.id)]["rank_valuation"]
                except KeyError:
                    print('rank_valuation except: ', member.display_name)
                    rank_valuation = await fetch_info(member)
                    retrieved_roles = set_roles(member)
                    cache[str(member.id)] = {'display_name': member.display_name,
                                             'rank_valuation': rank_valuation,
                                             'primary_role': retrieved_roles[0],
                                             'secondary_role': retrieved_roles[1]}
                    with open('cache.json', 'w') as outfile:
                        json.dump(cache, file, indent=4)
                        outfile.close()
                check = True
                if type(rank_valuation) != int and type(rank_valuation) != float:  # First rank_value check
                    rank_valuation = await fetch_info(member)  # Check API again to reconfirm eligibility
                    if type(rank_valuation) != int and type(rank_valuation) != float:
                        check = False
                        not_eligible_members.append(member)  # Add to non-eligibility list after second test
                    else:
                        # check = True
                        cache[str(member.id)]["rank_valuation"] = rank_valuation  # Otherwise update rank value
                        with open('cache.json', 'w') as file:
                            json.dump(cache, file)
                            file.close()
                if check:
                    player_info = [rank_valuation, cache[str(member.id)]["primary_role"],
                                   cache[str(member.id)]["secondary_role"]]
                    matchmakingObj.dict_of_players[member] = player_info

            lobby_channel = get(bot.get_all_channels(), id=channel.id)
            assert len(lobby_channel.members) >= 10, "Members less than 10 in lobby"

            if not_eligible_members:
                for member in not_eligible_members:
                    list_of_players.remove(member)
                    await removed_member_dm(member, error=cache[str(member.id)]["rank_valuation"])
                for player in reversed(list_of_players):
                    queue_dict[channel.id].insert(0, player)
                not_eligible_members = []
                return

            red, blue = matchmakingObj.matchmaker(list_of_players)
            captain = random.choice(list_of_players)
            print('\nRed: ', red)
            print('\nBlue: ', blue)
            red_channel, blue_channel, text_channel, role, password, lobby_name = \
                (await asyncio.gather(create_channels(member.guild, channel)))[0]
            await db.write_to_db(lobby_name, red, blue, captain.id)  # save the match teams and match id in db
            embed = discord.Embed(color=random.randint(0, 0xffff), description="⏳ Matchmaking...")
            embed.timestamp = datetime.datetime.now()
            for key in blue:
                await (blue[key]).add_roles(role)
                await (blue[key]).move_to(blue_channel)
            for key in red:
                print('\nred[key]: ', red[key])
                await (red[key]).add_roles(role)
                await (red[key]).move_to(red_channel)
            teams_and_roles_description = await get_description(red, blue, password, role.name, captain.id)
            embed.description = teams_and_roles_description
            await text_channel.send(embed=embed)
            for announcement_channel_id in config["channel_ids"]['get_attention_channel_ids']:
                announcement_channel = get(bot.get_all_channels(), id=announcement_channel_id)
                if announcement_channel in channel.category.channels:
                    await get_attention(announcement_channel, role)


@bot.event
async def on_voice_channel_move(member, before_channel, after_channel):
    lobby_channels = config['channel_ids']['lobby_channel_ids']
    if after_channel.id in lobby_channels:
        await on_voice_channel_connect(member, after_channel)
        return

    before_channel_name = before_channel.name.lower()
    after_channel_name = after_channel.name.lower()
    if before_channel.category == after_channel.category:
        if ('blue side' in before_channel_name and 'red side' in after_channel_name) or \
                ('blue side' in before_channel_name and 'red side' in after_channel_name):
            # if member changes team voice channel, i.e. from red side to blue side or vice versa
            print("inside member changed teams channels")
            await member.move_to(before_channel)
            await member.send(embed=discord.Embed(color=0xff0000, description="**WARNING**\n" \
                                                                              "You can't join the other team's voice "
                                                                              "channel.\n\n "
                                                                              "**Don't do it again or else you will "
                                                                              "be banned.**"))
        else:
            return


@bot.event
async def on_voice_channel_alone(member, channel1):  # executed when 2 members are remaining in a voice channel
    print('inside on_voice_channel_alone')
    if 'blue' not in channel1.name.lower() and 'red' not in channel1.name.lower():
        return
    for i in channel1.category.channels:
        print('inside alone for loop')
        if i != channel1 and i.type.name == 'voice' and len(i.members) <= 2:
            print('inside alone for loop')
            match_id = channel1.category.name
            red, blue, captain_id = await db.get_teams(match_id)
            red = add_member_obj(red)
            blue = add_member_obj(blue)
            category_to_be_deleted = channel1.category
            role = get(member.guild.roles, name=category_to_be_deleted.name)
            print('Role to be deleted name: ', role.name)
            print('Category name: ', category_to_be_deleted.name)
            await role.delete()
            for channel in enumerate(category_to_be_deleted.channels):
                try:
                    print(f'\n{channel[0]}. deleting {channel[1].name}')
                    await asyncio.gather(channel[1].delete())
                except:
                    print("Passing from delete channel on_voice_channel_alone")
                    pass
            print(f'\ndeleting {category_to_be_deleted.name}')
            await asyncio.gather(category_to_be_deleted.delete())
            print('deleted category and removed roles')
            break
    else:
        return

    latest_match_stats = await Stats.get_stats(red, blue)
    print('\nlatest_match_stats: ', latest_match_stats)
    embed = get_stats_embed(latest_match_stats, captain_id, match_id)
    print('Stats description: ', embed.description)
    # send match stats to match history channels
    for i in ['monthly_lb', 'weekly_lb', 'overall_lb', 'daily_lb']:
        await db.write_stats(latest_match_stats, i)


async def removed_member_dm(member, error='no_summoner'):
    await member.move_to(get(member.guild.channels, id=797704589305577488))
    if error == 'no_summoner':
        await member.send(embed=discord.Embed(color=0xff000,
                                              description="*We couldn't find you in LoL database. If you are "
                                                          "registered with LoL then please add your summoner name in "
                                                          "your server nickname, i.e. '[ADA] Goldfish'. AND register "
                                                          "with Orianna Bot in the server.\nOR\nMention `@Tech "
                                                          "Support` in the technical issues channel.*"))
        print(f'removed {member.name} from lobby for not having summoner name')
    elif error == 'less_than_50':
        await member.send(embed=discord.Embed(color=0xff000,
                                              description="*Your number of wins and losses is less than 50. Your "
                                                          "account is not eligible for matchmaking. Please don't do "
                                                          "it again.\n\nIf you are seeing this by mistake, "
                                                          "please contact an admin.*"))
        print(f'removed {member.name} from lobby for having wins & losses < 50')
    else:
        await member.send(embed=discord.Embed(color=0xff000,
                                              description="*Your account is currently unranked and it's not eligible "
                                                          "for matchmaking. Please don't do it again.\n\nIf you are "
                                                          "seeing this by mistake, please contact an admin.*"))
        print(f'removed {member.name} from lobby for having an unranked account')
    return


def add_member_obj(team):
    for rank in team:
        team[rank] = get(bot.get_all_members(), id=team[rank])
    return team


def get_stats_embed(stats, captain_id, match_id):
    embed = discord.Embed(color=random.randint(0, 0xff0000))
    description = f'**Match ID:** {match_id}\n\n' \
                  f'**Captain:** <@!{captain_id}>\n' \
                  f"**ID--------|-Kills-|-Deaths-|-Assists-|-CreepScore-|-PentaKills-|-QuadraKills-|**\n"
    # f'**Winner:** {stats["win"]}\n\n' \
    for discord_id in stats:
        league_id = re.split("[\[\] ]+", bot.get_user(discord_id).display_name)
        if len(league_id) > 2:
            league_id.pop(0)
            league_id.pop(0)
            league_id = ' '.join(league_id)
        elif len(league_id) == 2:
            league_id = league_id[1]
        description += f"{league_id} {stats[discord_id]['kills']} {stats[discord_id]['deaths']} {stats[discord_id]['assists']} {stats[discord_id]['creepScore']} {stats[discord_id]['pentaKills']} {stats[discord_id]['quadraKills']}\n"
    embed.description = description
    return embed


async def get_description(red, blue, password, match_name, captain_id):
    description = f"**⚔️Teams and Roles**\n\n" \
                  f"**Lobby Name:**     {match_name}\n" \
                  f"**Password:**       {password}\n\n" \
                  f"**Captain:** <@!{captain_id}>\n\n" \
                  f"**🔵 Blue Team: **\n" \
                  f"   **Top     -** <@!{blue['Top'].id}>\n" \
                  f"   **Jungle  -** <@!{blue['Jungle'].id}>\n" \
                  f"   **Mid     -** <@!{blue['Mid'].id}>\n" \
                  f"   **ADC     -** <@!{blue['Adc'].id}>\n" \
                  f"   **Support -** <@!{blue['Support'].id}>\n\n" \
                  f"**🔴 Red Team: **\n" \
                  f"   **Top     -** <@!{red['Top'].id}>\n" \
                  f"   **Jungle  -** <@!{red['Jungle'].id}>\n" \
                  f"   **Mid     -** <@!{red['Mid'].id}>\n" \
                  f"   **ADC     -** <@!{red['Adc'].id}>\n" \
                  f"   **Support -** <@!{red['Support'].id}>\n\n\n" \
                  f"*<@!{captain_id}> You are incharge of creating the lobby, please use the above `Lobby Name` and " \
                  f"`Password`.* "
    return description


async def get_attention(channel, role):
    embed = discord.Embed(color=random.randint(0, 0xffff),
                          description='            **ATTENTION**\nA new match has just started.\n\n')

    embed.set_footer(text="Join the lobby now to start a new match.")
    embed.timestamp = datetime.datetime.now()
    await channel.send(content=role.mention, embed=embed)


def generate_name_password(lobby_channel):
    password = ''
    for x in range(11):
        password += random.choice(string.ascii_letters + string.digits)
    name = f"P247-{lobby_channel.category.name.split('-')[0]}-{config['lobby_numbers'][str(lobby_channel.id)]}-{random.choice(password) + random.choice(password)}"
    config['lobby_numbers'][str(lobby_channel.id)] += 1
    with open('config.json', 'w') as file:
        json.dump(config, file, indent=4)
        file.close()
    return name, password


async def create_channels(guild, lobby_channel):
    role_category_name, password = generate_name_password(lobby_channel)
    player_role = get(guild.roles, name='Player')
    category = await guild.create_category(name=role_category_name)
    role = await guild.create_role(name=role_category_name)
    await category.set_permissions(role, read_messages=True, send_messages=True, connect=True, speak=True)

    # make category accessible only to people with a specific role which we generate. The name of
    # the category and role must be the same

    await category.set_permissions(guild.default_role, read_messages=True, connect=False, speak=False,
                                   send_messages=False)

    blue_name = '🔵' + config['vc2']
    blue = await category.create_voice_channel(name=blue_name, bitrate=98000, user_limit=5)
    await blue.set_permissions(role, connect=True, speak=True)
    await blue.set_permissions(guild.default_role, connect=False, speak=False)
    await blue.set_permissions(player_role, read_messages=True, connect=False, speak=False)

    red_name = '🔴' + config['vc1']
    red = await category.create_voice_channel(name=red_name, bitrate=98000, user_limit=5)
    await red.set_permissions(role, connect=True, speak=True)
    await red.set_permissions(guild.default_role, connect=False, speak=False)
    await red.set_permissions(player_role, read_messages=True, connect=False, speak=False)

    text_channel_name = '⚔️' + config['tc']
    text_channel = await category.create_text_channel(name=text_channel_name)
    await text_channel.set_permissions(role, read_messages=True, send_messages=True, connect=True, speak=True)
    await text_channel.set_permissions(guild.default_role, read_messages=False, send_messages=False, connect=False,
                                       speak=False)
    await text_channel.set_permissions(player_role, read_messages=False, send_messages=False, connect=False,
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
