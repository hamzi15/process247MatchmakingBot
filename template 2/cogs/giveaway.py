import asyncio
import datetime
import json
import os
import random
import sys
import time

import discord
from discord.ext import commands, tasks

if not os.path.isfile("giveaway.json"):
    sys.exit("'giveaway.json' not found! Add it and try again.")
else:
    with open("giveaway.json") as file:
        config = json.load(file)


class Giveaways(commands.Cog, name="giveaways"):
    def __init__(self, bot):
        self.bot = bot
        self.config = json.load(open("giveaway.json", "r"))
        self.color = 0xff006a
        self.giveaway_task.start()
        self.channel = 886626697833766962
        self.hosted_by = None

    @commands.command(name="giveaway", aliases=["gstart"], description="!giveaway name_of_the_prize|duration|winners")
    @commands.has_role("Admin")
    async def giveaway(self, ctx: commands.Context, info: str, *args):
        answers = info.strip().replace("_", " ").split("|")
        winners = args
        if len(args) != int(answers[2]):
            await ctx.send(embed=discord.Embed(description="ERROR: Invalid number of winners.", color=0xff0000))
            return
        try:
            winner = abs(int(answers[2]))
            if winner <= 0:
                await ctx.send(embed=discord.Embed(description="You did not enter a positive number in winners. Do it like this: !giveaway prize|time|winners"))
                return
        except ValueError:
            await ctx.send(embed=discord.Embed(
                description="You did not enter an integer in winners. Do it like this: !giveaway prize|time|winners"))
            return
        prize = answers[0].title()
        converted_time = convert(answers[1])
        if converted_time == -1:
            await ctx.send("You did not enter the correct unit of time (example: '1d' or '1h')")
        elif converted_time == -2:
            await ctx.send("Your time value should be an integer.")
            return
        try:
            await ctx.message.delete()
        except:
            pass
        giveaway_embed = discord.Embed(
            title="🎉 {} 🎉".format(prize),
            color=self.color,
            description=f'» **{winner}** {"winner" if winner == 1 else "winners"}\n'
                        f'» Hosted by {ctx.author.mention}\n\n'
                        f'» **React with 🎉 to get into the giveaway.**\n'
        ) \
            .set_footer(icon_url=self.bot.user.avatar_url, text="Ends at")

        giveaway_embed.timestamp = datetime.datetime.utcnow() + datetime.timedelta(seconds=converted_time[0])
        giveaway_message = await ctx.guild.get_channel(self.channel).send(embed=giveaway_embed)
        await giveaway_message.add_reaction("🎉")
        self.hosted_by = ctx.author
        now = int(time.time())
        giveaways = json.load(open("giveaway.json", "r"))
        if winners:
            data = {
            "prize": prize,
            "host": ctx.author.id,
            "winners": winners,
            "end_time": now + converted_time[0],
            "channel_id": ctx.guild.get_channel(self.channel).id,
            "winner": [winner.mention for winner in winners],
            "message_id": ctx.message.id
            }
        else:
            data = {
                "prize": prize,
                "host": ctx.author.id,
                "winners": winners,
                "end_time": now + converted_time[0],
                "channel_id": ctx.guild.get_channel(self.channel).id,
                "winner": -1,
                "message_id": ctx.message.id
            }

        giveaways[str(giveaway_message.id)] = data
        json.dump(giveaways, open("giveaway.json", "w"), indent=4)

    @commands.command(
        name="stopgiveaway",
        aliases=["stop"],
        usage="{giveaway_id}", description="Stops the giveaway. !stopgiveaway (id of the giveaway message)"
    )
    @commands.has_role("Admin")
    async def gstop(self, ctx: commands.Context, message_id):
        await ctx.message.delete()
        giveaways = json.load(open("giveaway.json", "r"))
        if message_id not in giveaways.keys():
            return await ctx.send(
                embed=discord.Embed(title="Error",
                                    description="This giveaway ID is not found.",
                                    color=self.color))
        await self.stop_giveaway(ctx.guild.get_channel(self.channel), message_id, giveaways[message_id])

    @commands.command(name="reroll",
                      description="Rerolls a giveaway for a new winner. !reroll (id of the giveaway message)")
    @commands.has_role("Admin")
    async def reroll(self, ctx, msg_id: int):
        try:
            new_msg = await ctx.guild.get_channel(self.channel).fetch_message(msg_id)
            users = await new_msg.reactions[0].users().flatten()
            users.pop(users.index(config[msg_id]["winners"]))
            winner = random.choice(users)
            await ctx.guild.get_channel(self.channel).send(f":tada: The new winner is: {winner.mention}!")
        except:
            prefix = "!"
            await ctx.send(
                f":x: There was an error! \n`{prefix}reroll <Channel that hosted the giveaway> <messageID of the giveaway message>` ")

    def cog_unload(self):
        self.giveaway_task.cancel()

    async def stop_giveaway(self, channel, g_id, data):
        giveaway_message = await channel.fetch_message(int(g_id))
        users = await giveaway_message.reactions[0].users().flatten()
        users.pop(users.index(self.bot.user))
        winner = data["winner"]
        if winner == -1:
            if len(users) < data["winners"]:
                winners_number = len(users)
            else:
                winners_number = data["winners"]

            winners = random.sample(users, winners_number)
            users_mention = []
            for user in winners:
                users_mention.append(user.mention)
                await user.send(embed=discord.Embed(description=f"Congratulations **{user.mention}**, you won the giveaway. Please Dm {self.hosted_by.mention}"))
            result_embed = discord.Embed(
                title="🎉 {} 🎉".format(data["prize"]),
                color=self.color,
                description=f"Congratulations **{', '.join(users_mention)}** , you won the giveaway! Please DM {self.hosted_by.mention} to claim the "
                            "prize :)").set_footer(icon_url=self.bot.user.avatar_url, text="Giveaway Ended!")
            await giveaway_message.edit(embed=result_embed)
            ghost_ping = await channel.send(", ".join(users_mention))
            await ghost_ping.delete()
            giveaways = json.load(open("giveaway.json", "r"))
            del giveaways[g_id]
            json.dump(giveaways, open("giveaway.json", "w"), indent=4)
        else:
            string = ""
            for i in winner:
                string += i + ", "
            result_embed = discord.Embed(
                title="🎉 {} 🎉".format(data["prize"]),
                color=self.color,
                description=f"Congratulations **{winner}** you won the giveaway! Please DM {self.hosted_by.mention} to claim the "
                            "prize :)").set_footer(icon_url=self.bot.user.avatar_url, text="Giveaway Ended!")
            await giveaway_message.edit(embed=result_embed)
            ghost_ping = await channel.send(", ".join(winner))
            await ghost_ping.delete()
            giveaways = json.load(open("giveaway.json", "r"))
            del giveaways[g_id]
            json.dump(giveaways, open("giveaway.json", "w"), indent=4)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, (commands.CommandNotFound, discord.HTTPException)):
            return

        if isinstance(error, commands.MemberNotFound):
            return await ctx.send(embed=discord.Embed(description="Invalid arguments. Please follow the syntax of this command.", color=self.color))

        if isinstance(error, commands.MissingPermissions):
            return await ctx.send(embed=discord.Embed(
                title="Error",
                description="You don't have the permission to use this command.",
                color=self.color))
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"You forgot to provide an argument, please do it like: `{ctx.command.name} {ctx.command.usage}`",
                color=self.color))

    @tasks.loop(seconds=10)
    async def giveaway_task(self):
        await self.bot.wait_until_ready()
        giveaways = json.load(open("giveaway.json", "r"))

        if len(giveaways) == 0:
            return

        for giveaway in giveaways:
            data = giveaways[giveaway]
            try:
                if int(time.time()) > data["end_time"]:
                    await asyncio.gather(self.stop_giveaway(self.bot.get_channel(self.channel), giveaway, data))
            except:
                pass


def convert(date):
    pos = ["s", "m", "h", "d"]
    time_dic = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}
    i = {"s": "Seconds", "m": "Minutes", "h": "Hours", "d": "Days"}
    unit = date[-1]
    if unit not in pos:
        return -1
    try:
        val = int(date[:-1])

    except:
        return -2

    if val == 1:
        return val * time_dic[unit], i[unit][:-1]
    else:
        return val * time_dic[unit], i[unit]


def setup(bot):
    bot.add_cog(Giveaways(bot))
