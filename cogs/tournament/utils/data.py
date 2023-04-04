from __future__ import annotations

import datetime
import typing
from typing import Literal

import discord.utils

from utils import make_ordinal, pretty_record

if typing.TYPE_CHECKING:
    import core

import utils
from cogs.tournament.utils import Category, CategoryData, Rank
from cogs.tournament.utils.utils import role_map


rank_display = {
    Rank.GOLD: "<:gold:931317421862699118>",
    Rank.DIAMOND: "<:diamond:931317455639445524>",
    Rank.GRANDMASTER: "<:grandmaster:931317469396729876>",
    Rank.UNRANKED: "",
}

class TournamentData:
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
    def categories(self) -> list[Category]:
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
        embed_type: Literal["start", "end", "announcement", "leaderboard", "hall_of_fame"],
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

    async def hall_of_fame(self):
        hof_embed = self.base_embed("", "hall_of_fame")
        hof_embed.title += "Hall of Fame - Top 3"
        lb_embeds = []
        for category in self.map_data:
            lb_description = ""
            hof_embed_field_value = ""
            async for record in self.client.database.get(
                """
                    WITH t_records AS (SELECT ur.user_id, record, ur.value, tr.category, screenshot
                                       FROM tournament_records tr
                                                LEFT JOIN user_ranks ur on tr.user_id = ur.user_id and tr.category = ur.category
                                       WHERE tournament_id = $1),
                         ranks AS (SELECT user_id,
                                          record,
                                          value,
                                          category,
                                          screenshot,
                                          rank() OVER (
                                              PARTITION BY category
                                              ORDER BY record
                                              ) rank_num
                                   FROM t_records)
                    SELECT r.user_id, nickname, record, value , category, screenshot, rank_num
                    FROM ranks r
                    LEFT JOIN users u ON r.user_id = u.user_id
                    WHERE category = $2
                    ORDER BY category != 'Time Attack',
                             category != 'Mildcore',
                             category != 'Hardcore',
                             category != 'Bonus',
                             rank_num
                             
                """,
                self.id,
                category,
            ):

                value = (
                    f"`{make_ordinal(record.rank_num)}` - {record.nickname} - {pretty_record(record.record)} "
                    f"{rank_display[record.value]} [Image]({record.screenshot})\n"
                )
                if record.rank_num < 3:
                    hof_embed_field_value += value
                lb_description += value
            hof_embed.add_field(
                name=category,
                value=hof_embed_field_value,
                inline=False,
            )
            lb_embeds.append(self.base_embed(lb_description, "leaderboard"))

        return hof_embed, lb_embeds
