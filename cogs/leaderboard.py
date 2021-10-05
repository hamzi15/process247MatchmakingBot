import json
import os
import sys

import discord
from discord.ext import commands

# import asyncio

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)


class Leaderboard(commands.Cog, name="leaderboard"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lb", description="Shows the leaderboard of a match.")
    async def leaderboard(self, context):
        #   fetch leaderboard from API endpoint
        pass


def setup(bot):
    bot.add_cog(Leaderboard)
