from __future__ import annotations

import decimal
import math
import typing
from functools import reduce
from operator import concat

import xlsxwriter
from discord.ext import commands

if typing.TYPE_CHECKING:
    import core

from cogs.tournament.utils import (
    Categories,
    Category,
    Difficulty,
    MissionData,
    MissionDifficulty,
    MissionType,
    Rank,
    Ranks,
)
from cogs.tournament.utils.data import TournamentData
from database import DotRecord

XP_MULTIPLIER = {
    "Time Attack": 0.14094,
    "Mildcore": 0.3654,
    "Hardcore": 0.8352,
    "Bonus": 0.3654,
}

MISSION_POINTS = {
    MissionDifficulty.EXPERT: 2000,
    MissionDifficulty.HARD: 1500,
    MissionDifficulty.MEDIUM: 1000,
    MissionDifficulty.EASY: 500,
    MissionDifficulty.GENERAL: 2000,
}

COLUMN_MAPPER = {
    Category.TIME_ATTACK: (0, 1, 2, 0),
    Category.MILDCORE: (4, 5, 6, 1),
    Category.HARDCORE: (8, 9, 10, 2),
    Category.BONUS: (12, 13, 14, 3),
}

Worksheet = typing.TypeVar("Worksheet")


class ExperienceCalculator:
    def __init__(self, tournament: TournamentData):
        self.tournament = tournament
        self.xp: dict[int, int] = {}
        self.mission_totals: dict[int, dict[Difficulty, int]] = {}

    async def compute_xp(self) -> dict[int, int]:
        await self.computer_leaderboard_xp()
        await self.compute_difficulty_missions()
        await self.compute_general_missions()
        return self.xp

    async def computer_leaderboard_xp(self):
        query = """
                    WITH t_records AS (SELECT ur.user_id, record, ur.value, tr.category
                                       FROM tournament_records tr
                                                LEFT JOIN user_ranks ur on tr.user_id = ur.user_id and tr.category = ur.category
                                       WHERE tournament_id = $1),
                         top AS (SELECT category, min(record) as top_record FROM t_records GROUP BY category, value),
                         top_recs AS (SELECT user_id, record, top.category, value as "rank"
                                      FROM top
                                               LEFT JOIN t_records r ON top.category = r.category
                                          AND record = top.top_record)
                    SELECT r.user_id, r.record, r.category, tr.record as top_record
                    FROM top_recs tr
                             RIGHT JOIN t_records r ON tr.category = r.category AND tr.rank = r.value;
                """
        async for row in self.tournament.client.database.get(
            query, self.tournament.client.current_tournament.id
        ):
            if not self.xp.get(row.user_id, None):
                self.xp[row.user_id] = 0
                self.mission_totals[row.user_id] = {
                    "Easy": 0,
                    "Medium": 0,
                    "Hard": 0,
                    "Expert": 0,
                    "General": 0,
                }
            self.xp[row.user_id] += self.lb_xp_formula(
                row.category, row.record, row.top_record
            )

    @staticmethod
    def lb_xp_formula(
        category: Categories, record: decimal.Decimal, top_record: decimal.Decimal
    ):
        multiplier = XP_MULTIPLIER[category]
        formula = (
            1
            - (float(record) - float(top_record))
            / (multiplier * float(top_record))
            * 2500
        )
        return 100 if formula < 100 else math.ceil(formula)

    async def compute_difficulty_missions(self):
        query = """
            WITH t_records AS (SELECT ur.user_id, record, ur.value, tr.category
                               FROM tournament_records tr
                                        LEFT JOIN user_ranks ur on tr.user_id = ur.user_id and tr.category = ur.category
                               WHERE tournament_id = $1),
                 top AS (SELECT category, min(record) as top_record FROM t_records GROUP BY category, value),
                 top_records AS (SELECT user_id, record, top.category, value as "rank"
                                 FROM top
                                          LEFT JOIN t_records r ON top.category = r.category
                                     AND record = top.top_record),
                 sub_time_missions AS (SELECT target,
                                              t_records.user_id,
                                              t_records.category,
                                              nickname,
                                              difficulty,
                                              value,
                                              record
                                       FROM tournament_missions
                                                RIGHT JOIN t_records ON t_records.category = tournament_missions.category
                                                LEFT JOIN users ON users.user_id = t_records.user_id
                                       WHERE id = $1
                                         AND CASE
                                                 WHEN type = 'Sub Time' THEN record < target
                                                 WHEN type = 'Completion' THEN record > -10000000
                                                 ELSE true
                                           END
                                       ORDER BY t_records.category != 'Time Attack',
                                                t_records.category != 'Mildcore',
                                                t_records.category != 'Hardcore',
                                                t_records.category != 'Bonus',
                                                difficulty != 'Expert',
                                                difficulty != 'Hard',
                                                difficulty != 'Medium',
                                                difficulty != 'Easy'),
                 distinct_values AS (SELECT DISTINCT ON (user_id, category, nickname) user_id,
                                                                            category,
                                                                            nickname,
                                                                            difficulty,
                                                                            value as rank,
                                                                            record
                           FROM sub_time_missions
                           ORDER BY user_id, category, nickname,
                                    difficulty != 'Expert',
                                    difficulty != 'Hard',
                                    difficulty != 'Medium',
                                    difficulty != 'Easy')
            SELECT t.user_id, t.category, nickname, difficulty, tr.record as top_record
            FROM distinct_values t
                     LEFT JOIN top_records tr ON tr.category = t.category AND tr.rank = t.rank;
        """
        async for row in self.tournament.client.database.get(
            query, self.tournament.client.current_tournament.id
        ):
            self.xp[row.user_id] += MISSION_POINTS[row.difficulty]
            self.mission_totals[row.user_id][row.difficulty] += 1

    async def compute_general_missions(self):
        query = """
            SELECT type, target, extra_target FROM tournament_missions WHERE id = $1 AND category = 'General';
        """
        if not (
            general_mission := await self.tournament.client.database.get_one(
                query, self.tournament.id
            )
        ):
            return

        if general_mission.type == MissionType.XP_THRESHOLD:
            for user_id, xp in self.xp.items():
                if xp >= general_mission.target:
                    self.xp[user_id] += MISSION_POINTS[MissionDifficulty.GENERAL]

        elif general_mission.type == MissionType.MISSION_THRESHOLD:
            for user_id, data in self.mission_totals.items():
                if data[general_mission.extra_target] >= general_mission.target:
                    self.xp[user_id] += MISSION_POINTS[MissionDifficulty.GENERAL]

        elif general_mission.type == MissionType.TOP_PLACEMENT:
            await self.compute_top_placement(general_mission.target)

    async def compute_top_placement(self, target: int):
        query = """
            WITH t_records AS (SELECT ur.user_id, record, ur.value, tr.category
                               FROM tournament_records tr
                                        LEFT JOIN user_ranks ur on tr.user_id = ur.user_id and tr.category = ur.category
                               WHERE tournament_id = $1),
                 ranks AS (SELECT user_id,
                                  record,
                                  value,
                                  category,
                                  rank() OVER (
                                      PARTITION BY value, category
                                      ORDER BY record
                                      ) rank_num
                           FROM t_records),
                 top_three AS (SELECT user_id, count(user_id) as amount
                               FROM ranks
                               WHERE rank_num <= 3
                               GROUP BY user_id)
            SELECT *
            FROM top_three
            WHERE amount >= $2;
        """
        async for row in self.tournament.client.database.get(
            query, self.tournament.id, target
        ):
            self.xp[row.user_id] += MISSION_POINTS[MissionDifficulty.GENERAL]


class SpreadsheetCreator:
    _records: list[DotRecord] = []
    _split_records: dict[Rank, dict[Category, list[DotRecord]]] = {
        rank: {category: [] for category in Category.all()} for rank in Rank.all()
    }
    _workbook: xlsxwriter.Workbook = xlsxwriter.Workbook("DPK_Tournament.xlsx")
    _rank_worksheets: list[Worksheet] = []
    _missions_worksheet: Worksheet = None
    _row_tracker = [
        # T  M  H  B
        [2, 2, 2, 2],  # Unranked
        [2, 2, 2, 2],  # Gold
        [2, 2, 2, 2],  # Diamond
        [2, 2, 2, 2],  # Grandmaster
    ]

    def __init__(
        self,
        tournament: TournamentData,
        xp: dict[int, int],
        totals: dict[int, dict[Difficulty, int]],
    ):
        self._tournament = tournament
        self._xp = xp
        self._totals = totals

    async def create(self):
        await self._get_records()
        self.init_workbook()

    async def _get_records(self):
        query = """
            SELECT tr.user_id, nickname, tr.category, tr.record, ur.value as rank
            FROM tournament_records tr
                     LEFT JOIN users u on u.user_id = tr.user_id
                     LEFT JOIN user_ranks ur on u.user_id = ur.user_id AND tr.category = ur.category
            WHERE tournament_id = $1
            ORDER BY value != 'Grandmaster',
                     value != 'Diamond',
                     value != 'Gold',
                     value != 'Unranked',
                     tr.category != 'Time Attack',
                     tr.category != 'Mildcore',
                     tr.category != 'Hardcore',
                     tr.category != 'Bonus',
                     record;
        """
        self._records = [
            record
            async for record in self._tournament.client.database.get(
                query, self._tournament.id
            )
        ]
        self._split_ranks()

    def _split_ranks(self):
        for record in self._records:
            self._split_records[record.rank][record.category].append(record)

    def init_workbook(self):
        grandmaster = self._workbook.add_worksheet(name="Grandmaster")
        diamond = self._workbook.add_worksheet(name="Diamond")
        gold = self._workbook.add_worksheet(name="Gold")
        unranked = self._workbook.add_worksheet(name="Unranked")
        missions = self._workbook.add_worksheet(name="Missions")

        self._rank_worksheets: list[Worksheet] = [grandmaster, diamond, gold, unranked]
        self._missions_worksheet: Worksheet = missions
        self._format_sheets()

    def _get_worksheet(self, name: str):
        return self._workbook.get_worksheet_by_name(name)

    @staticmethod
    def _get_worksheet_idx(name: str):
        return {
            "Unranked": 0,
            "Gold": 1,
            "Diamond": 2,
            "Grandmaster": 3,
        }

    def _format_sheets(self):
        for worksheet in self._rank_worksheets:
            # Rank titles
            merge_format = self._workbook.add_format(
                {"align": "center", "bg_color": "#93c47d", "border": 1}
            )
            worksheet.merge_range("A1:C1", "Time Attack", merge_format)
            merge_format = self._workbook.add_format(
                {"align": "center", "bg_color": "#ff9900", "border": 1}
            )
            worksheet.merge_range("E1:G1", "Mildcore", merge_format)
            merge_format = self._workbook.add_format(
                {"align": "center", "bg_color": "#ff0000", "border": 1}
            )
            worksheet.merge_range("I1:K1", "Hardcore", merge_format)
            merge_format = self._workbook.add_format(
                {"align": "center", "bg_color": "#ffff00", "border": 1}
            )
            worksheet.merge_range("M1:O1", "Bonus", merge_format)
            # Name, Time, Points titles
            worksheet.write_row(
                "A2",
                ["Name", "Time", "Points", None] * 4,
                cell_format=self._workbook.add_format({"align": "left", "border": 1}),
            )
            worksheet.set_column_pixels(0, 15, width=105)
            worksheet.write(1, 3, "", self._workbook.add_format({"border": 0}))
            worksheet.write(1, 7, "", self._workbook.add_format({"border": 0}))
            worksheet.write(1, 11, "", self._workbook.add_format({"border": 0}))
            worksheet.write(1, 15, "", self._workbook.add_format({"border": 0}))
        self._missions_worksheet.write_row(
            'A1',
            [
                "Names",
                "Easy",
                "Medium",
                "Hard",
                "Expert",
                "General",
                "Missions Total",
                "Total XP",
                "TA Average XP",
                "MC Average XP",
                "HC Average XP",
                "BO Average XP",
            ],
            cell_format=self._workbook.add_format({"border": 1}),
        )
        center_fmt = self._workbook.add_format({"align": "center"})

        self._missions_worksheet.set_column_pixels(0, 19, width=105)
        self._missions_worksheet.set_column(1, 5, cell_format=center_fmt)

    def _write_mission_data(self):
        # for i, user_id in enumerate(self._xp, start=2):
        #
        #
        #
        #
        # for i, (user_id, data) in enumerate(tournament.xp.items(), start=2):
        #     user = await ExperiencePoints.find_user(user_id)
        #     missions_total = (
        #             data["easy"] * 500
        #             + data["medium"] * 1000
        #             + data["hard"] * 1500
        #             + data["expert"] * 2000
        #             + data["general"] * 2000
        #     )
        #
        #     missions_ws.write_row(
        #         "A" + str(i),
        #         [
        #             f"{user.alias} ({user.user_id})",
        #             data["easy"],
        #             data["medium"],
        #             data["hard"],
        #             data["expert"],
        #             data["general"],
        #             missions_total,
        #             ceil(data["xp"]),
        #             ceil(data["ta_cur_avg"]),
        #             ceil(data["mc_cur_avg"]),
        #             ceil(data["hc_cur_avg"]),
        #             ceil(data["bo_cur_avg"]),
        #         ],
        #     )
        # missions_ws.set_column(1, 5, cell_format=center_fmt)
        ...

    def _write_leaderboards(self):
        for rank, categories in self._split_records.items():
            for category, records in categories.items():
                for _ in records:
                    ...
