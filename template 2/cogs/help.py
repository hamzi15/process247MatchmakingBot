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


class Help(commands.Cog, name="help"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", description="Displays the list of commands")
    async def help(self, context):  # lists all commands in all the cogs of the bot
        if has_roles(context):
            prefix = config["bot_prefix"]
            if not isinstance(prefix, str):
                prefix = prefix[0]
            embed = discord.Embed(title="Help", description="List of available commands:", color=0x541760)
            for i in self.bot.cogs:
                cog = self.bot.get_cog(i.lower())
                commands = cog.get_commands()
                command_list = [command.name for command in commands]
                command_description = [command.description for command in commands]
                help_text = '\n'.join(f'{prefix}{n} - {h}' for n, h in zip(command_list, command_description))
                embed.add_field(name=i.capitalize(), value=f'```{help_text}```', inline=False)
            await context.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
