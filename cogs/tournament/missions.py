from __future__ import annotations

import typing

import discord
from discord.ext import commands
from discord import app_commands

import views

from cogs.tournament.utils.utils import (
    MissionCategory,
    MissionType,
)
from database import DotRecord
from utils import time_convert, pretty_record

if typing.TYPE_CHECKING:
    import core


Categories = typing.Literal["Time Attack", "Mildcore", "Hardcore", "Bonus", "General"]
Difficulty = typing.Literal["Easy", "Medium", "Hard", "Expert", "General"]
Type = typing.Literal[
    "--DIFFICULTY--",
    "XP Threshold",
    "Mission Threshold",
    "Top Placement",
    "----GENERAL----",
    "Sub Time",
    "Completion",
]


class Missions(commands.Cog):
    def __init__(self, bot: core.Doom):
        self.bot = bot

    missions = app_commands.Group(
        name="missions",
        description="Missions",
        guild_ids=[195387617972322306],
    )

    @missions.command()
    async def add(
        self,
        itx: core.DoomItx,
        category: Categories,
        difficulty: Difficulty,
        mission_type: Type,
        target: str,
    ):
        if "-" in mission_type:
            return  # TODO: Raise

        if not itx.client.current_tournament:
            return  # TODO: Raise

        await itx.response.defer()
        # Verify if mission type goes with category
        if (
            category == MissionCategory.GENERAL
            and mission_type not in MissionType.general()
        ):
            return  # TODO: Raise

        if (
            category != MissionCategory.GENERAL
            and mission_type not in MissionType.difficulty()
        ):
            return  # TODO: Raise

        target = self.validate_target(mission_type, target)

        old_mission = await itx.client.database.get_one(
            "SELECT * FROM tournament_missions WHERE category = $1 AND difficulty = $2 and id = $3",
            category,
            difficulty,
            itx.client.current_tournament.id,
        )
        if old_mission:
            content = (
                "There's already a mission in this category and difficulty.\n"
                "Are you sure you want to overwrite this?\n\n"
            )
        else:
            content = "Is this correct?\n\n"
        content += (
            f"**Category: **{category}\n"
            f"**Difficulty: ** {difficulty}\n"
            f"**Type: ** {mission_type}\n"
            f"**Target: ** {target}\n"
        )
        view = views.Confirm(itx)
        await itx.edit_original_response(content=content, view=view)
        await view.wait()
        if not view.value:
            return

        await itx.client.database.set(
            """
            INSERT INTO tournament_missions (id, type, target, difficulty, category) 
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id, category, difficulty)
            DO UPDATE SET target = EXCLUDED.target, type = EXCLUDED.type
            """,
            itx.client.current_tournament.id,
            mission_type,
            target,
            difficulty,
            category,
        )

    @staticmethod
    def validate_target(mission_type: Type, target: str) -> int | float:
        if mission_type in MissionType.difficulty():
            try:
                res = int(target)
            except ValueError:
                # TODO: RAISE
                raise ValueError
        elif mission_type == MissionType.SUB_TIME:
            res = time_convert(target)
        else:
            res = 0
        return res

    @missions.command()
    async def remove(
        self,
        itx: core.DoomItx,
        category: Categories,
        difficulty: Difficulty,
    ):
        if not itx.client.current_tournament:
            return  # TODO: Raise

        await itx.response.defer(ephemeral=True)
        mission = await itx.client.database.get_one(
            "SELECT * FROM tournament_missions WHERE category = $1 AND difficulty = $2 and id = $3",
            category,
            difficulty,
            itx.client.current_tournament.id,
        )
        if not mission:
            return  # TODO: Raise

        view = views.Confirm(itx)
        await itx.edit_original_response(
            content=(
                "Are you sure you want to delete this mission?\n\n"
                f"**Category: **{category}\n"
                f"**Difficulty: ** {difficulty}\n"
                f"**Type: ** {mission.type}\n"
                f"**Target: ** {mission.target}\n"
            ),
            view=view,
        )
        await view.wait()
        if not view.value:
            return

        await itx.client.database.set(
            "DELETE FROM tournament_missions WHERE category = $1 AND difficulty = $2 and id = $3",
            category,
            difficulty,
            itx.client.current_tournament.id,
        )

    @missions.command()
    async def publish(self, itx: core.DoomItx):
        if not itx.client.current_tournament:
            return  # TODO: Raise

        await itx.response.defer(ephemeral=True)
        query = """
            SELECT *
            FROM tournament_missions
            WHERE id = $1
            ORDER BY category != 'General',
                     category != 'Time Attack',
                     category != 'Mildcore',
                     category != 'Hardcore',
                     category != 'Bonus',
                     difficulty != 'Easy',
                     difficulty != 'Medium',
                     difficulty != 'Hard',
                     difficulty != 'Expert'
        """
        missions = [
            x
            async for x in itx.client.database.get(
                query, itx.client.current_tournament.id
            )
        ]
        if not missions:
            return  # TODO: Raise

        embed = itx.client.current_tournament.announcement_embed(
            self.pretty_missions(missions)
        )
        await itx.edit_original_response(embed=embed)

    def pretty_missions(self, missions: list[DotRecord]):
        description = "__**Missions**__\n"
        cur_title = "\n**" + missions[0].category + ":**\n"
        mission_text = ""
        for mission in missions:
            if mission.category + ":\n" != cur_title:
                description += cur_title
                description += mission_text
                mission_text = ""
                cur_title = mission.category + ":\n"
            mission_text += self.format_missions(
                mission.difficulty, mission.type, mission.target
            )
        if mission_text:
            description += mission_text
        return description

    @staticmethod
    def format_missions(
        difficulty: str, mission_type: str, target: str | int | float
    ) -> str:
        """Format missions into user-friendly strings."""
        formatted = ""
        if mission_type == MissionType.XP_THRESHOLD:
            formatted += f"Get {target} XP (excluding this mission)\n"
        elif mission_type == MissionType.MISSION_THRESHOLD:
            formatted += f"Complete {target} missions\n"
        elif mission_type == MissionType.TOP_PLACEMENT:
            formatted += f"Get Top 3 in {target} categories.\n"
        elif mission_type == MissionType.SUB_TIME:
            formatted += f"Get sub {pretty_record(float(target))}\n"
        elif mission_type == MissionType.COMPLETION:
            formatted += "Complete the level.\n"

        return f"- {difficulty}: {formatted}"
