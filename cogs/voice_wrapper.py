from discord.ext import commands


class VoiceWrapper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        self._multi_dispatch("!voice_state_update", member, before, after)
        if before.channel != after.channel:
            self._multi_dispatch("voice_channel_update", member, before.channel, after.channel)
            if before.channel is None:
                self._multi_dispatch("voice_channel_connect", member, after.channel)
            elif after.channel is None:
                self._multi_dispatch("voice_channel_disconnect", member, before.channel)
                if 0 <= len(before.channel.members) <= 2:
                    self._multi_dispatch("voice_channel_alone", member, before.channel)
            else:
                self._multi_dispatch("voice_channel_move", member, before.channel, after.channel)

    def _multi_dispatch(self, name, member, *args, **kwargs):
        if name.startswith("!"):
            name = name.lstrip("!")
        else:
            self.bot.dispatch(name, member, *args, **kwargs)

        if member.bot:
            self.bot.dispatch(name + "_bot", member, *args, **kwargs)
            if member == self.bot.user:
                self.bot.dispatch(name + "_me", *args, **kwargs)
            else:
                self.bot.dispatch(name + "_other_bot", member, *args, **kwargs)
        else:
            self.bot.dispatch(name + "_user", member, *args, **kwargs)


def setup(bot):
    bot.add_cog(VoiceWrapper(bot))
