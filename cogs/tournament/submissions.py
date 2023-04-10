from __future__ import annotations

import typing

import discord
from discord import app_commands
from discord.ext import commands

import utils
import views
from cogs.tournament.utils import Categories_NoGen, Category
from cogs.tournament.utils.errors import TournamentNotActiveError
from cogs.tournament.utils.utils import ORGANIZER

if typing.TYPE_CHECKING:
    import core


class TournamentSubmissions(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    tournament = app_commands.Group(
        name="tournament",
        description="tournament",
        guild_ids=[195387617972322306, utils.GUILD_ID],
    )

    async def insert_record(
        self, category: Category, user_id: int, screenshot_url: str, record: float
    ):
        query = """
            INSERT INTO tournament_records (user_id, category, record, tournament_id, screenshot)
            VALUES ($1, $2, $3, (SELECT id FROM tournament WHERE active = TRUE LIMIT 1), $4)
        """
        await self.bot.database.set(query, user_id, category, record, screenshot_url)

    async def get_tournament_id(self) -> int:
        return (
            self.bot.current_tournament and self.bot.current_tournament.id
        ) or await self.bot.database.fetchval(
            "SELECT id FROM tournament WHERE active = TRUE;"
        )

    async def get_old_record(
        self, user_id: int, category: Category, tournament_id: int
    ):
        return await self.bot.database.fetchval(
            """
            SELECT record, rank()
                over (order by inserted_at DESC) as date_rank FROM tournament_records 
            WHERE user_id = $1 AND
            category = $2 AND 
            tournament_id = $3;
            """,
            user_id,
            category,
            tournament_id,
        )

    @staticmethod
    async def get_image_url(itx: core.DoomItx):
        return (await itx.original_response()).attachments[0].url

    async def submission(
        self,
        itx: core.DoomItx,
        screenshot: discord.Attachment,
        record: float,
        category: Category,
    ):
        tournament_id = await self.get_tournament_id()
        if not tournament_id:
            raise TournamentNotActiveError
        old_record = await self.get_old_record(
            itx.user.id,
            category,
            tournament_id,
        )
        if old_record and old_record < record:
            raise utils.RecordNotFasterError
        pretty_record = utils.pretty_record(record)
        content = f"**{itx.user.mention}'s {category} Submission**\n**Record:** {pretty_record}"
        view = views.Confirm(itx, confirm_msg=content)
        await itx.response.send_message(
            f"{itx.user.mention}, is this correct?\n\n{content}",
            file=await screenshot.to_file(),
            view=view,
        )
        await view.wait()
        if not view.value:
            return
        url = await self.get_image_url(itx)
        await self.insert_record(category, itx.user.id, url, record)

    @app_commands.command()
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def ta(
        self,
        itx: core.DoomItx,
        screenshot: discord.Attachment,
        record: app_commands.Transform[float, utils.RecordTransformer],
    ):
        await self.submission(itx, screenshot, record, Category.TIME_ATTACK)

    @app_commands.command()
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def mc(
        self,
        itx: core.DoomItx,
        screenshot: discord.Attachment,
        record: app_commands.Transform[float, utils.RecordTransformer],
    ):
        await self.submission(itx, screenshot, record, Category.MILDCORE)

    @app_commands.command()
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def hc(
        self,
        itx: core.DoomItx,
        screenshot: discord.Attachment,
        record: app_commands.Transform[float, utils.RecordTransformer],
    ):
        await self.submission(itx, screenshot, record, Category.HARDCORE)

    @app_commands.command()
    @app_commands.guilds(
        discord.Object(id=195387617972322306), discord.Object(id=utils.GUILD_ID)
    )
    async def bo(
        self,
        itx: core.DoomItx,
        screenshot: discord.Attachment,
        record: app_commands.Transform[float, utils.RecordTransformer],
    ):
        await self.submission(itx, screenshot, record, Category.BONUS)

    @tournament.command()
    async def submit(
        self,
        itx: core.DoomItx,
        category: Category,
        screenshot: discord.Attachment,
        record: app_commands.Transform[float, utils.RecordTransformer],
    ):
        await self.submission(itx, screenshot, record, category)

    @tournament.command()
    async def delete(
        self,
        itx: core.DoomItx,
        category: Categories_NoGen,
        user: discord.Member | None = None,
    ):
        tournament_id = await self.get_tournament_id()
        if not tournament_id:
            raise TournamentNotActiveError

        if (
            user
            and user != itx.user
            and itx.guild.get_role(ORGANIZER) not in itx.user.roles
        ):
            raise utils.NoPermissionsError

        if not user:
            user = itx.user

        view = views.Confirm(itx)
        await itx.response.send_message(
            f"Do you want to delete {user.mention}'s latest {category} submission?",
            view=view,
        )

        await view.wait()
        if not view.value:
            return

        query = """
        WITH latest_record AS (SELECT max(inserted_at)
                               FROM tournament_records
                               WHERE user_id = $1
                                 AND tournament_id = $3
                                 AND category = $2)
        DELETE
        FROM tournament_records
        WHERE user_id = $1
          AND tournament_id = $3
          AND category = $2
          AND inserted_at = latest_record
        """
        await itx.client.database.set(query, user.id, category, tournament_id)
