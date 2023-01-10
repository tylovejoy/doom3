from __future__ import annotations

import asyncio
import json
import typing

import discord
from discord import app_commands
from discord.ext import commands

import utils

if typing.TYPE_CHECKING:
    import core

with open("assets/emoji-data.json", "r", encoding="utf8") as f:
    mapping = json.load(f)


class Personal(commands.Cog):
    async def cog_check(self, ctx: commands.Context[core.Doom]) -> bool:
        return ctx.channel.id == 882243150419197952 or ctx.guild.id == 968553235239559239  # Spam-friendly

    @app_commands.command(name="name")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def nickname_change(
        self, itx: core.Interaction[core.Doom], nickname: app_commands.Range[str, 1, 25]
    ) -> None:
        """
        Change your display name in bot commands.

        Args:
            itx: Interaction
            nickname: New nickname
        """
        await itx.response.send_message(
            f"Changing your nick name from {itx.client.all_users[itx.user.id]['nickname']} to {nickname}"
        )
        await itx.client.database.set(
            "UPDATE users SET nickname=$2 WHERE user_id=$1",
            itx.user.id,
            nickname,
        )
        itx.client.all_users[itx.user.id]["nickname"] = nickname

    @app_commands.command(name="brug-mode")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID), discord.Object(id=968553235239559239))
    async def brug_mode(self, itx: core.Interaction[core.Doom], text: str):
        await itx.response.send_message(utils.emojify(text)[:2000])

    @app_commands.command(name="uwu")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID), discord.Object(id=968553235239559239))
    async def uwufier(self, itx: core.Interaction[core.Doom], text: str):
        await itx.response.send_message(utils.uwuify(text)[:2000])

    @app_commands.command(name="blarg")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID), discord.Object(id=968553235239559239))
    async def blarg(self, itx: core.Interaction[core.Doom]):
        await itx.response.send_message("BLARG")


async def setup(bot: core.Doom):
    await bot.add_cog(Personal(bot))
