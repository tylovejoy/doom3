from __future__ import annotations

import datetime
import typing
from typing import Literal

import discord.utils

if typing.TYPE_CHECKING:
    import core
import utils
from cogs.tournament.utils.utils import (
    Category,
    CategoryData,
    role_map,
    # MissionCategory,
    # MissionDifficulty,
    MissionType,
)


# class TournamentRecordsData:
#     user_id: int
#     record: float
#     category: Category
#
#     def __hash__(self):
#         return hash((self.user_id, self.category))
#
#     def __eq__(self, other):
#         if isinstance(other, TournamentRecordsData):
#             return self.user_id == other.user_id and self.category == other.category
#         raise TypeError
#
#     def __ne__(self, other):
#         if isinstance(other, TournamentRecordsData):
#             return self.user_id != other.user_id or self.category != other.category
#         raise TypeError
#
#     def __lt__(self, other):
#         if isinstance(other, TournamentRecordsData):
#             return self == other and self.record < other.record
#         raise TypeError
#
#     def __le__(self, other):
#         if isinstance(other, TournamentRecordsData):
#             return self == other and self.record <= other.record
#         raise TypeError
#
#     def __gt__(self, other):
#         if isinstance(other, TournamentRecordsData):
#             return self == other and self.record > other.record
#         raise TypeError
#
#     def __ge__(self, other):
#         if isinstance(other, TournamentRecordsData):
#             return self == other and self.record >= other.record
#         raise TypeError
#
#
# class MissionData:
#     category: MissionCategory
#     difficulty: MissionDifficulty
#     type: MissionType
#     value: float


class TournamentData:
    # records: dict[Category, set[TournamentRecordsData]] = {
    #     k: [] for k in Category.all()
    # }
    # missions: dict[Category, MissionData]

    def __init__(
        self,
        *,
        client: core.Doom,
        title: str,
        start: datetime.datetime,
        end: datetime.datetime,
        data: dict[Category, CategoryData],
        bracket: bool,
        id_: int | None = None,
    ):
        self.client = client
        self.title = title
        self.start = start
        self.end = end
        self.map_data = data
        self.bracket = bracket
        self.id = id_

    def __repr__(self):
        return (
            f"Tournament<{self.id}>: \n"
            f" - Title: {self.title}\n"
            f" - Start: {self.start}\n"
            f" - End: {self.start}\n"
            f" - Bracket: {self.bracket}"
        )

    @property
    def categories(self) -> list[str]:
        return [cat for cat in Category.all() if cat in self.map_data]

    @property
    def ta_data(self) -> CategoryData | None:
        return self.map_data.get(Category.TIME_ATTACK, None)

    @property
    def mc_data(self) -> CategoryData | None:
        return self.map_data.get(Category.MILDCORE, None)

    @property
    def hc_data(self) -> CategoryData | None:
        return self.map_data.get(Category.HARDCORE, None)

    @property
    def bo_data(self) -> CategoryData | None:
        return self.map_data.get(Category.BONUS, None)

    @property
    def start_formatted(self) -> str:
        return (
            discord.utils.format_dt(self.start, style="R")
            + "\n"
            + discord.utils.format_dt(self.start, style="F")
        )

    @property
    def end_formatted(self) -> str:
        return (
            discord.utils.format_dt(self.end, style="R")
            + "\n"
            + discord.utils.format_dt(self.end, style="F")
        )

    @property
    def dates(self):
        return f"**Start:**\n{self.start_formatted}\n" f"**End:**\n{self.end_formatted}"

    @property
    def mention_ids(self) -> list[int]:
        return [role_map[cat] for cat in Category.all() if cat in self.map_data]

    def embed_description(self) -> str:
        map_info = ""
        print(self.map_data)
        for cat, data in self.map_data.items():  # TODO: Change ID to utils
            map_info += (
                self.client.get_guild(195387617972322306)
                .get_role(role_map[cat])
                .mention
                + "\n"
                f"**Code:** {data['code']}\n"
                f"**Level:** {data['level']}\n"
            )

        return map_info

    def base_embed(
        self,
        description: str,
        embed_type: Literal["start", "end", "announcement", "leaderboard"],
    ) -> discord.Embed:
        embed = utils.DoomEmbed(
            title=self.title,
            description=description,
            thumbnail="http://207.244.249.145/assets/images/icons/gold_cup.png",
            image=f"http://207.244.249.145/assets/images/icons/tournament_{embed_type}_banner.png",
            color=discord.Color.gold(),
        )
        return embed

    def start_embed(self):
        return self.base_embed(self.embed_description() + "\n\n" + self.dates, "start")

    def announcement_embed(self, announcement: str):
        return self.base_embed(announcement, "announcement")

    def end_embed(self):
        description = (
            "**The round has ended!**\n" "Stay tuned for the next announcement!\n\n"
        )
        # TODO: Add champions
        return self.base_embed(description, "end")

    # def get_record(self, data: TournamentRecordsData) -> TournamentRecordsData:
    #     for record in self.records[data.category]:
    #         if record == data:
    #             return record
    #     raise TypeError  # TODO: Real error
    #
    # def replace_record(self, data: TournamentRecordsData):
    #     record = self.get_record(data)
    #     if record > data:
    #         self.records[data.category].remove(record)
    #         self.records[data.category].add(data)
    #     else:
    #         raise TypeError  # TODO: Real error
