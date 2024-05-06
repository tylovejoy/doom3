from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import utils
import views

if typing.TYPE_CHECKING:
    import core
    from core import DoomCtx, DoomItx


class ModCommands(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    async def cog_check(self, ctx: DoomCtx) -> bool:
        return True
        # return bool(ctx.author.get_role(utils.STAFF))

    mod = app_commands.Group(
        **utils.mod_,
        guild_ids=[utils.GUILD_ID],
    )
    keep_alive = app_commands.Group(
        **utils.keep_alive_,
        guild_ids=[utils.GUILD_ID],
        parent=mod,
    )

    @keep_alive.command(**utils.add_keep_alive)
    @app_commands.describe(**utils.keep_alive_args)
    async def add_keep_alive(self, itx: DoomItx, thread: discord.Thread) -> None:
        if thread.id in self.bot.keep_alives:
            await itx.response.send_message(
                f"{thread.mention} already in keep alive list.",
                ephemeral=True,
            )
            return

        self.bot.keep_alives.append(thread.id)
        query = "INSERT INTO keep_alives (thread_id) VALUES ($1);"
        await self.bot.database.execute(
            query,
            thread.id,
        )
        await itx.response.send_message(
            f"Added {thread.mention} to keep alive list.",
            ephemeral=True,
        )

    @keep_alive.command(**utils.remove_keep_alive)
    @app_commands.describe(**utils.keep_alive_args)
    async def remove_keep_alive(self, itx: DoomItx, thread: discord.Thread) -> None:
        if thread.id not in self.bot.keep_alives:
            await itx.response.send_message(
                f"{thread.mention} is not currently in the keep alive list.",
                ephemeral=True,
            )
            return

        self.bot.keep_alives.remove(thread.id)
        query = "DELETE FROM keep_alives WHERE thread_id = $1;"
        await self.bot.database.execute(
            query,
            thread.id,
        )
        await itx.response.send_message(
            f"Removed {thread.mention} from keep alive list.",
            ephemeral=True,
        )

    @mod.command(**utils.remove_record)
    @app_commands.describe(**utils.remove_record_args)
    async def remove_record(
        self,
        itx: DoomItx,
        user: discord.Member,
        map_code: app_commands.Transform[str, utils.MapCodeRecordsTransformer],
        level_name: app_commands.Transform[str, utils.MapLevelTransformer],
    ):
        await itx.response.defer(ephemeral=True)
        query = """
            WITH all_user_records AS (
                SELECT *, rank() OVER (ORDER BY inserted_at DESC) as latest FROM records r 
                LEFT JOIN users u on r.user_id = u.user_id 
                WHERE r.user_id = $1 AND map_code = $2 AND level_name = $3
            )
            SELECT * FROM all_user_records WHERE latest = 1
        """
        row = await self.bot.database.fetchrow(
            query,
            user.id,
            map_code,
            level_name,
        )
        if not row:
            raise utils.NoRecordsFoundError

        embed = utils.DoomEmbed(
            title="Delete Record",
            description=(
                f"`Name` {row['nickname']}\n"
                f"`Code` {row['map_code']}\n"
                f"`Level` {row['level_name']}\n"
                f"`Record` {utils.pretty_record(row['record'])}\n"
            ),
        )
        view = views.Confirm(itx)
        await itx.edit_original_response(
            content="Delete this record?", embed=embed, view=view
        )
        await view.wait()

        if not view.value:
            return
        query = """
              WITH
                latest AS (
                  SELECT max(inserted_at)
                    FROM records
                   WHERE
                       user_id = $1
                   AND map_code = $2
                   AND level_name = $3
                )
            DELETE
              FROM records
             WHERE
                 user_id = $1
             AND map_code = $2
             AND level_name = $3
             AND inserted_at = latest
        """
        await self.bot.database.execute(
            query,
            user.id,
            map_code,
            level_name,
        )

    @mod.command(**utils.change_name)
    @app_commands.describe(**utils.change_name_args)
    async def change_name(
        self,
        itx: DoomItx,
        user: app_commands.Transform[int, utils.UserTransformer],
        nickname: app_commands.Range[str, 1, 25],
    ):
        old = self.bot.all_users[user]["nickname"]
        self.bot.all_users[user]["nickname"] = nickname
        query = "UPDATE users SET nickname=$1 WHERE user_id=$2;"
        await self.bot.database.execute(
            query, nickname, user
        )
        await itx.response.send_message(
            f"Changing {old} ({user}) nickname to {nickname}"
        )


async def setup(bot: core.Doom):
    await bot.add_cog(ModCommands(bot))
