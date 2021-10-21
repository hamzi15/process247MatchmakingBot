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


def has_roles(context):
    if config["admin_role_id"] in [role.id for role in context.author.roles]:
        return True
    return False


class LeagueCommands(commands.Cog, name="admin"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setcategory", description="Reset category name. Syntax: "
                                                      "<prefix>setcategory <new name>")
    async def set_category_name(self, context, name: str):
        if has_roles(context):
            config['lobby_name'] = name
            with open('config.json', 'w') as file:
                json.dump(config, file)
                file.close()
            await context.send(
                embed=discord.Embed(color=randint(0, 0x000ff), description='*Match category name successfully changed.*'))

    # @commands.command(name="setlobby", description="Reset lobby name. Syntax: "
    #                                                   "<prefix>setlobby <new name>")
    # async def set_lobby(self, context, name: str):
    #     if has_roles(context):
    #         config['lobby_name'] = name
    #         with open('config.json', 'w') as file:
    #             json.dump(config, file)
    #             file.close()
    #         await context.send(
    #             embed=discord.Embed(color=randint(0, 0x000ff), description='*Lobby name successfully changed.*'))

    @commands.command(name="setvc", description="Reset game voice channel names. Syntax: "
                                                "<prefix>setcategory <voice channel 1 name> <voice channel 2 "
                                                "name>")
    async def set_vc(self, context, vc1: str, vc2: str):
        if has_roles(context):
            config['vc1'] = vc1
            config['vc2'] = vc2
            with open('config.json', 'w') as file:
                json.dump(config, file)
                file.close()
            await context.send(embed=discord.Embed(color=randint(0, 0x000ff),
                                                   description='*Voice channel names successfully changed.*'))


def setup(bot):
    bot.add_cog(LeagueCommands(bot))
