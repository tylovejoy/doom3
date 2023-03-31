from __future__ import annotations

import asyncio
import typing

import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import locale_str as _T

import utils
from views import MAP_DATA

if typing.TYPE_CHECKING:
    import core
    from core import DoomCtx, DoomItx


class Test(commands.Cog):
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
        self,
        ctx: DoomCtx,
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
        >sync $ -> Clears global commands
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

    @commands.command()
    @commands.is_owner()
    async def xx(self, ctx: DoomCtx):
        # msg = await ctx.send("starting")
        # thread = await ctx.channel.create_thread(name="Test", message=msg)
        map_name = "Petra"
        print(MAP_DATA)
        print(MAP_DATA["Petra"])
        print(MAP_DATA["Petra"].IMAGE_URL)
        embed = utils.DoomEmbed(
            title="Map Submission - Confirmation",
            description=(
                f">>> ` Code ` FAKEST\n"
                f"`  Map ` {map_name}\n"
                f"` Type ` Multilevel, Hardcore\n"
            ),
            color=MAP_DATA.get(map_name, discord.Color.from_str("#000000")).COLOR,
            image=MAP_DATA.get(map_name, None).IMAGE_URL,
            thumbnail=ctx.bot.user.display_avatar.url,
        )
        print(embed.to_dict())
        await ctx.send(embed=embed)
        # await asyncio.sleep(1)

    @commands.command()
    @commands.is_owner()
    async def log(
        self,
        ctx: DoomCtx,
        level: typing.Literal["debug", "info", "DEBUG", "INFO"],
    ):
        ctx.bot.logger.setLevel(level.upper())
        await ctx.message.delete()

    @app_commands.command(name=_T("testing123"))
    @app_commands.guilds(discord.Object(id=utils.GUILD_ID))
    # @app_commands.describe(user=_T("The user to bonk."))
    async def bonk(self, interaction: DoomItx, user: discord.User):
        await interaction.response.send_message(
            f":hammer: {user.mention}", ephemeral=True
        )


async def setup(bot: core.Doom):
    await bot.add_cog(Test(bot))
