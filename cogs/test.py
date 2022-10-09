from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import utils

if typing.TYPE_CHECKING:
    import core


class Test(commands.Cog):
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: typing.Literal["~", "*", "^"] | None = None,
    ) -> None:
        """
        ?sync -> global sync
        ?sync ~ -> sync current guild
        ?sync * -> copies all global app commands to current guild and syncs
        ?sync ^ -> clears all commands from the current
                        guild target and syncs (removes guild commands)
        ?sync id_1 id_2 -> syncs guilds with id 1 and 2
        """
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            elif spec == "$":
                ctx.bot.tree.clear_commands()
                await ctx.bot.tree.sync()
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands "
                f"{'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    @app_commands.command(name="command-2")
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    async def my_private_command(
        self, interaction: core.Interaction[core.Doom], first: int, second: str
    ) -> None:
        """/command-2"""
        users = [
            x async for x in interaction.client.database.get("""SELECT * FROM users;""")
        ]
        embed = utils.DoomEmbed(title="Test", description="Test")

        embed.add_field(
            name="Ayutthaya (20 CP) by SoulCrusher",
            value=(
                "┣ **Code:** TEST\n"
                "┣ **Map Type(s):** Single\n"
                "┣ **Rating:** 5.0/10\n"
                "┗ **Description:** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Ayutthaya (20 CP) by SoulCrusher",
            value=(
                "┣ **Code:** TEST\n"
                "┣ **Map Type(s):** Single\n"
                "┣ **Rating:** 5.0/10\n"
                "┗ **Description:** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Ayutthaya (20 CP) by SoulCrusher",
            value=(
                "> **Code:** TEST\n"
                "> **Map Type(s):** Single\n"
                "> **Rating:** 5.0/10\n"
                "> **Description:** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Ayutthaya (20 CP) by SoulCrusher",
            value=(
                "> **Code:** TEST\n"
                "> **Map Type(s):** Single\n"
                "> **Rating:** 5.0/10\n"
                "> **Description:** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n"
            ),
            inline=False,
        )

        await interaction.response.send_message(
            f"{users} {first} {second}", embed=embed
        )
        # raise ValueError


async def setup(bot: core.Doom):
    await bot.add_cog(Test(bot))
