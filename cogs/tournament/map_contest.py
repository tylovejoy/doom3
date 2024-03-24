from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import utils
from views import Confirm

if typing.TYPE_CHECKING:
    import core


class MapContest(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    @app_commands.command(name="map-contest")
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def submit(
        self,
        itx: core.DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeTransformer],
    ):
        """
        Submit a map to the map contest.

        Args:
            itx:
            map_code: Overwatch share code.

        Returns:

        """
        await itx.response.defer(ephemeral=True)
        tournament = self.bot.current_tournament
        if not tournament or tournament.end < discord.utils.utcnow():
            await itx.edit_original_response(content="There is no ongoing contest/tournament at this time.")
            return

        if itx.client.map_cache.get(map_code, None):
            await itx.edit_original_response(content="You cannot submit previously released map.")
            return

        query = "SELECT EXISTS(SELECT 1 FROM map_contest WHERE user_id = $1 AND tournament_id = $2)"
        if await self.bot.database.fetchval(query, itx.user.id, tournament.id):
            content = (
                "You can only submit once per contest.\n\n"
                "Do you to overwrite your previous submission with map code: `{map_code}`**`?"
            )
        else:
            content = f"Submitting map code: `{map_code}`\n\nAre you sure you want to submit this map?"

        view = Confirm(itx)
        await itx.edit_original_response(
            content=content,
            view=view,
        )
        await view.wait()
        if not view.value:
            return

        query = """
            INSERT INTO map_contest
              (user_id, map_code, tournament_id)
            VALUES
              ($1, $2, $3)
                ON CONFLICT (user_id, tournament_id) DO UPDATE SET map_code = $2
        """
        await self.bot.database.set(query, itx.user.id, map_code, tournament.id)

    @app_commands.command(name="map-contest-list")
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def view(self, itx: core.DoomItx):
        """
        Lists all map codes available in the current (or previous) map contest without user information.

        Args:
            itx:

        Returns:

        """
        await itx.response.defer()
        tournament = self.bot.current_tournament
        if not tournament:
            query = "SELECT MAX(id) FROM tournament"
            tournament = self.bot.database.fetchval(query)
            # await itx.edit_original_response(content="There is no ongoing contest/tournament at this time.")
            # return

        query = "SELECT map_code, user_id FROM map_contest WHERE tournament_id = $1"
        rows = [f"`{r['map_code']}`" async for r in self.bot.database.get(query, tournament.id)]
        await itx.edit_original_response(content="\n".join(rows))

    @app_commands.command(name="map-contest-list-users")
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def view_users(self, itx: core.DoomItx):
        """
        Lists all map codes available in the current (or previous) map contest WITH user information.

        Args:
            itx:

        Returns:

        """
        await itx.response.defer()
        tournament = self.bot.current_tournament
        if not tournament:
            query = "SELECT MAX(id) FROM tournament"
            tournament = self.bot.database.fetchval(query)
            # await itx.edit_original_response(content="There is no ongoing contest/tournament at this time.")
            # return

        query = "SELECT user_id, map_code FROM map_contest WHERE tournament_id = $1"
        users = itx.client.all_users
        details = [
            f"`{row['map_code']}` - {users[row['user_id']]['nickname']} ({row['user_id']})"
            async for row in self.bot.database.get(query, tournament.id)
        ]

        await itx.edit_original_response(content="\n".join(details))

    @app_commands.command(name="map-contest-delete-code")
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def delete_map(
        self,
        itx: core.DoomItx,
        map_code: app_commands.Transform[str, utils.MapCodeTransformer],
    ):
        """
        Delete a map code from the current map contest.
        Args:
            itx:
            map_code:

        Returns:

        """
        await itx.response.defer()
        tournament = self.bot.current_tournament
        if not tournament or tournament.end < discord.utils.utcnow():
            await itx.edit_original_response(content="There is no ongoing contest/tournament at this time.")
            return

        view = Confirm(itx)
        await itx.edit_original_response(
            content=f"Are you sure you want to delete map code `{map_code}`?",
            view=view,
        )
        await view.wait()
        if not view.value:
            return

        query = "DELETE FROM map_contest WHERE tournament_id = $1 AND map_code = $2"
        await self.bot.database.set(query, tournament.id, map_code)
