from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

import utils

if TYPE_CHECKING:
    import core


class VentureRedirect(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot
        self.help_cd = commands.CooldownMapping.from_cooldown(
            1,
            360,
            commands.BucketType.channel,
        )
        self.general_cd = commands.CooldownMapping.from_cooldown(
            1,
            600,
            commands.BucketType.channel,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return  # ignore DoomBot

        if "venture" not in message.content.lower():
            return  # Only concerned with Venture references

        if message.channel.id in [689703945924247558, 689704042393501756]:  # lounge/videos
            bucket = self.general_cd.get_bucket(message)
            retry_after = bucket.update_rate_limit()
        elif message.channel.id in [754026577758519548, utils.SPR_RECORDS, utils.RECORDS]:  # help/records
            bucket = self.help_cd.get_bucket(message)
            retry_after = bucket.update_rate_limit()
        else:
            return  # ignore all other channels

        if not retry_after:
            content = (
                "### Hey there!\n"
                "We'd love for you to stay and enjoy **Doomfist Parkour** with us but "
                "if you'd like to chat about **Venture Parkour**, "
                "you may want to visit the **Venture Parkour** server!\n\n"
                "https://discord.gg/qe4wyUfYBU"
            )
            await message.channel.send(content)


async def setup(bot: core.Doom):
    await bot.add_cog(VentureRedirect(bot))
