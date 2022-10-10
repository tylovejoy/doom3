from __future__ import annotations

import typing

from discord.ext import commands

if typing.TYPE_CHECKING:
    import core


class GymUtils(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    @commands.command()
    async def convert(self, ctx: commands.Context, value: float):
        if ctx.message.channel.id != 999000079283273911:
            return
        kg = 0.45359237 * round(value, 2)
        lb = 2.2 * round(value, 2)
        print(ctx.author)
        await ctx.send(
            f"{value} lb ≈ {round(kg, 2)} kg\n" f"{value} kg ≈ {round(lb, 2)} lb"
        )


async def setup(bot: core.Doom):
    await bot.add_cog(GymUtils(bot))
