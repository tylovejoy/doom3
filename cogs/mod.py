from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import cogs
import utils
import views

if typing.TYPE_CHECKING:
    import core


class ModCommands(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context[core.Doom]) -> bool:
        return True
        # return bool(ctx.author.get_role(utils.STAFF))

    mod = app_commands.Group(
        name="mod",
        guild_ids=[utils.GUILD_ID],
        description="Mod only commands",
    )
    keep_alive = app_commands.Group(
        name="keep-alive",
        guild_ids=[utils.GUILD_ID],
        description="Keep Threads Alive",
        parent=mod,
    )

    @keep_alive.command(name="add")
    async def add_keep_alive(
        self, itx: core.Interaction[core.Doom], thread: discord.Thread
    ) -> None:
        """
        Add a keep thread alive.

        Args:
            itx: Interaction
            thread: Thread to keep alive
        """
        if thread.id in self.bot.keep_alives:
            await itx.response.send_message(
                f"{thread.mention} already in keep alive list.",
                ephemeral=True,
            )
            return

        self.bot.keep_alives.append(thread.id)
        await self.bot.database.set(
            "INSERT INTO keep_alives (thread_id) VALUES ($1)",
            thread.id,
        )
        await itx.response.send_message(
            f"Added {thread.mention} to keep alive list.",
            ephemeral=True,
        )

    @keep_alive.command(name="remove")
    async def remove_keep_alive(
        self, itx: core.Interaction[core.Doom], thread: discord.Thread
    ) -> None:
        """
        Remove a keep alive thread.

        Args:
            itx: Interaction
            thread: Thread to remove from keep alive list
        """
        if thread.id not in self.bot.keep_alives:
            await itx.response.send_message(
                f"{thread.mention} is not currently in the keep alive list.",
                ephemeral=True,
            )
            return

        self.bot.keep_alives.remove(thread.id)
        await self.bot.database.set(
            "DELETE FROM keep_alives WHERE thread_id = $1;",
            thread.id,
        )
        await itx.response.send_message(
            f"Removed {thread.mention} from keep alive list.",
            ephemeral=True,
        )

    @mod.command(name="remove-record")
    @app_commands.autocomplete(
        map_code=cogs.map_codes_autocomplete, level_name=cogs.map_levels_autocomplete
    )
    async def remove_record(
        self,
        itx: core.Interaction[core.Doom],
        member: discord.Member,
        map_code: app_commands.Transform[str, utils.MapCodeRecordsTransformer],
        level_name: app_commands.Transform[str, utils.MapLevelTransformer],
    ):
        await itx.response.defer(ephemeral=True)
        record = [
            x
            async for x in self.bot.database.get(
                "SELECT * FROM records r "
                "LEFT JOIN users u on r.user_id = u.user_id "
                "WHERE r.user_id=$1 AND map_code=$2 AND level_name=$1",
                member.id,
                map_code,
                level_name,
            )
        ]
        if not record:
            raise utils.NoRecordsFoundError

        record = record[0]
        embed = utils.DoomEmbed(
            title="Delete Record",
            description=(
                f"`Name` {record.nickname}\n"
                f"`Code` {utils.pretty_record(record.map_code)}\n"
                f"`Level` {record.level_name}\n"
            ),
        )
        view = views.Confirm(itx)
        await itx.edit_original_response(
            content="Delete this record?", embed=embed, view=view
        )
        await view.wait()

        if not view.value:
            return

        await self.bot.database.set(
            "DELETE FROM records WHERE user_id=$1 AND map_code=$2 AND level_name=$1",
            member.id,
            map_code,
            level_name,
        )

    @mod.command(name="change-name")
    @app_commands.autocomplete(member=cogs.users_autocomplete)
    async def change_name(
        self,
        itx: core.Interaction[core.Doom],
        member: app_commands.Transform[int, utils.UserTransformer],
        nickname: app_commands.Range[str, 1, 25],
    ):
        old = self.bot.all_users[member]["nickname"]
        self.bot.all_users[member]["nickname"] = nickname
        await self.bot.database.set(
            "UPDATE users SET nickname=$1 WHERE user_id=$2", nickname, member
        )
        await itx.response.send_message(
            f"Changing {old} ({member}) nickname to {nickname}"
        )


async def setup(bot: core.Doom):
    await bot.add_cog(ModCommands(bot))
