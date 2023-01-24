from __future__ import annotations

import asyncio
import json
import random
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
    length = 0

    async def cog_check(self, ctx: commands.Context[core.Doom]) -> bool:
        return (
            ctx.channel.id == 882243150419197952 or ctx.guild.id == 968553235239559239
        )  # Spam-friendly

    @app_commands.command(**utils.alerts)
    @app_commands.describe(**utils.alerts_args)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def alerts(
        self,
        itx: core.Interaction[core.Doom],
        value: typing.Literal["On", "Off"],
    ):
        value_bool = value == "On"
        await itx.client.database.set(
            "UPDATE users SET alertable=$1 WHERE user_id=$2",
            value_bool,
            itx.user.id,
        )
        await itx.response.send_message(f"Alerts set to {value}.", ephemeral=True)


    @app_commands.command(**utils.name)
    @app_commands.describe(**utils.name_args)
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def nickname_change(
        self,
        itx: core.Interaction[core.Doom],
        nickname: app_commands.Range[str, 1, 25],
    ) -> None:
        await itx.response.send_message(
            f"Changing your nick name from {itx.client.all_users[itx.user.id]['nickname']} to {nickname}",
            ephemeral=True,
        )
        await itx.client.database.set(
            "UPDATE users SET nickname=$2 WHERE user_id=$1",
            itx.user.id,
            nickname,
        )
        itx.client.all_users[itx.user.id]["nickname"] = nickname

    @app_commands.command(**utils.brug_mode)
    @app_commands.describe(**utils.fun_args)
    @app_commands.guilds(
        discord.Object(id=utils.GUILD_ID), discord.Object(id=968553235239559239)
    )
    async def brug_mode(self, itx: core.Interaction[core.Doom], text: str):
        await itx.response.send_message(utils.emojify(text)[:2000])

    @app_commands.command(**utils.uwufier)
    @app_commands.describe(**utils.fun_args)
    @app_commands.guilds(
        discord.Object(id=utils.GUILD_ID), discord.Object(id=968553235239559239)
    )
    async def uwufier(self, itx: core.Interaction[core.Doom], text: str):
        await itx.response.send_message(utils.uwuify(text)[:2000])

    @app_commands.command(**utils.blarg)
    @app_commands.guilds(
        discord.Object(id=utils.GUILD_ID), discord.Object(id=968553235239559239)
    )
    async def blarg(self, itx: core.Interaction[core.Doom]):
        await itx.response.send_message("BLARG")

    @app_commands.command(**utils.u)
    @app_commands.describe(**utils.u_args)
    @app_commands.guilds(discord.Object(id=968553235239559239))
    async def _u(self, itx: core.Interaction[core.Doom], user: discord.Member):
        insults = [
            " is the guy of all ass",
            " is a littel shit bitch asshole",
            ", you are one of the people of all time",
            " is a Mictocellular pancake bastard",
            " is a fucing dumbass",
            ": The Holied King of All Rodents",
            " doesn't go joe mode. . .",
            " capitulated, then died.",
            " has swampy marsupial hind legs",
            " is the third plac e winner of the 2018 dumbass contest for all idiots",
            " is Cock Broken...",
        ]

        insult = random.choice(insults)

        await itx.response.send_message(f"{user.display_name}{insult}")

    @app_commands.command(**utils.increase)
    @app_commands.guilds(discord.Object(id=968553235239559239))
    async def increase(self, itx: core.Interaction[core.Doom]):
        self.length += 1
        await itx.response.send_message(f"8{'=' * self.length}D")
        if random.random() > 0.80:
            await asyncio.sleep(2)
            await itx.edit_original_response(content=f"DICK CHOPPED...")
            self.length = 0

    @app_commands.command(**utils.decrease)
    @app_commands.guilds(discord.Object(id=968553235239559239))
    async def decrease(self, itx: core.Interaction[core.Doom]):
        if self.length > 0:
            self.length -= 1
        await itx.response.send_message(f"8{'=' * self.length}D")
        if random.random() < 0.20:
            await asyncio.sleep(2)
            await itx.edit_original_response(content=f"DICK VIAGRA TIME...")
            self.length = 50


async def setup(bot: core.Doom):
    await bot.add_cog(Personal(bot))
