from __future__ import annotations

import typing

import discord
from discord.ext import commands
from discord import app_commands

import utils
import views
from cogs.tournament.utils.utils import Category, full_title_map, reverse_title_map

if typing.TYPE_CHECKING:
    import core


class TournamentSubmissions(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    async def insert_record(
        self, category: Category, user_id: int, screenshot_url: str, record: float
    ):
        query = """
            INSERT INTO tournament_records (user_id, category, record, tournament_id, screenshot)
            VALUES ($1, $2, $3, (SELECT id FROM tournament WHERE active = TRUE LIMIT 1), $4)
            ON CONFLICT (user_id, category, tournament_id) 
            DO UPDATE SET record = EXCLUDED.record, screenshot = EXCLUDED.screenshot
            WHERE tournament_records.user_id = excluded.user_id
              AND tournament_records.category = excluded.category
              AND tournament_records.tournament_id = excluded.tournament_id
              AND excluded.record < tournament_records.record
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
            SELECT record FROM tournament_records 
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
            return  # TODO: Error
        old_record = await self.get_old_record(
            itx.user.id,
            category,
            tournament_id,
        )
        if old_record and old_record < record:
            return  # TODO: Raise error
        pretty_record = utils.pretty_record(record)
        content = f"**{itx.user.mention}'s {full_title_map[category]} Submission**\n**Record:** {pretty_record}"
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
    @app_commands.guilds(discord.Object(id=195387617972322306))
    async def ta(
        self,
        itx: core.DoomItx,
        screenshot: discord.Attachment,
        record: app_commands.Transform[float, utils.RecordTransformer],
    ):
        await self.submission(itx, screenshot, record, Category.TIME_ATTACK)

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=195387617972322306))
    async def mc(
        self,
        itx: core.DoomItx,
        screenshot: discord.Attachment,
        record: app_commands.Transform[float, utils.RecordTransformer],
    ):
        await self.submission(itx, screenshot, record, Category.MILDCORE)

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=195387617972322306))
    async def hc(
        self,
        itx: core.DoomItx,
        screenshot: discord.Attachment,
        record: app_commands.Transform[float, utils.RecordTransformer],
    ):
        await self.submission(itx, screenshot, record, Category.HARDCORE)

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=195387617972322306))
    async def bo(
        self,
        itx: core.DoomItx,
        screenshot: discord.Attachment,
        record: app_commands.Transform[float, utils.RecordTransformer],
    ):
        await self.submission(itx, screenshot, record, Category.BONUS)

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=195387617972322306))
    async def submit(
        self,
        itx: core.DoomItx,
        category: typing.Literal["Time Attack", "Mildcore", "Hardcore", "Bonus"],
        screenshot: discord.Attachment,
        record: app_commands.Transform[float, utils.RecordTransformer],
    ):
        await self.submission(itx, screenshot, record, reverse_title_map[category])
