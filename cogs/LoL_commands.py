import json
import os
import sys
from random import randint

import discord
from discord.ext import commands

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)


class LeagueCommands(commands.Cog, name="league_commands"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setleaguecreds", description="Adds a player's LoL id and region to the database. Syntax: "
                                                         "<prefix>setleaguecreds <LoL id> <region>")
    async def set_league_creds(self, context, lol_id, region):
        if not context.author.id in config['dict_lol_ids']
            config['dict_lol_ids'][context.author.id] = [lol_id][region]
        pass

    @commands.command(name="removeleaguecreds", description="Removes a player's LoL id and region from the database. Syntax: "
                                                         "<prefix>removeleaguecreds <player @>")
    async def remove_league_creds(self, context):
        config['dict_lol_ids'].pop(context.author.id)
        await context.send(content=context.author.id, embed=discord.Embed(description="*Successfully removed from database!*", color=randint(0, 0xffff)))


def setup(bot):
    bot.add_cog(LeagueCommands)
