from __future__ import annotations

import asyncio
import decimal
import math
import typing

import xlsxwriter

from cogs.tournament.utils import (
    BaseXP,
    Categories,
    Category,
    MissionDifficulty,
    MissionType,
    Rank,
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
XP: typing.TypeAlias = dict[int, dict[str, int]]


class ExperienceCalculator:
    def __init__(self, tournament: TournamentData):
        self._tournament = tournament
        self._xp: XP = {}

    async def compute_xp(self) -> XP:
        await self._computer_leaderboard_xp()
        await self._compute_difficulty_missions()
        await self._compute_general_missions()
        return self._xp

    async def _computer_leaderboard_xp(self):
        query = """
            WITH t_records AS (SELECT tr.user_id,
                                      record,
                                      coalesce(ur.value, 'Unranked')                                                            as value,
                                      tr.category,
                                      rank()
                                      over (partition by ur.user_id, value, tr.category, ur.category order by inserted_at DESC) as date_rank
                               FROM tournament_records tr
                                        LEFT JOIN user_ranks ur on tr.user_id = ur.user_id and tr.category = ur.category
                               WHERE tournament_id = $1),
                 top AS (SELECT category, min(record) as top_record FROM t_records GROUP BY category, value),
                 top_recs AS (SELECT user_id, record, top.category, value as "rank"
                              FROM top
                                       LEFT JOIN t_records r ON top.category = r.category
                                  AND record = top.top_record)
            SELECT nickname, r.user_id, r.record, r.category, tr.record as top_record
            FROM top_recs tr
            
                     RIGHT JOIN t_records r ON tr.category = r.category AND tr.rank = r.value
                     LEFT JOIN users u on r.user_id = u.user_id
            WHERE date_rank = 1;
        """
        async for row in self._tournament.client.database.get(
            query, self._tournament.client.current_tournament.id
        ):
            await self._create_xp_row(row)

            value = self._lb_xp_formula(row.category, row.record, row.top_record)

            self._xp[row.user_id][row.category] += value
            self._xp[row.user_id]["Total XP"] += value

    async def _create_xp_row(self, row):
        if not self._xp.get(row.user_id, None):
            self._xp[row.user_id] = BaseXP.copy()
            self._xp[row.user_id]["nickname"] = row.nickname

    @staticmethod
    def _lb_xp_formula(
        category: Categories, record: decimal.Decimal, top_record: decimal.Decimal
    ) -> int:
        record = float(record)
        top_record = float(top_record)
        multi = XP_MULTIPLIER[category]
        formula = (1 - (record - top_record) / (multi * top_record)) * 2500

        if formula < 100:
            return 100
        return math.ceil(formula)

    async def _compute_difficulty_missions(self):
        query = """
            WITH t_records AS (SELECT tr.user_id, record, coalesce(ur.value, 'Unranked') as value, tr.category FROM tournament_records tr
                                        LEFT JOIN user_ranks ur on tr.user_id = ur.user_id and tr.category = ur.category
                               WHERE tournament_id = $1),
                 top AS (SELECT category, min(record) as top_record FROM t_records GROUP BY category, value),
                 top_recs AS (SELECT user_id, record, top.category, value as "rank"
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
                     LEFT JOIN top_recs tr ON tr.category = t.category AND tr.rank = t.rank;
        """
        async for row in self._tournament.client.database.get(
            query, self._tournament.client.current_tournament.id
        ):
            # await self._create_xp_row(row)
            self._xp[row.user_id]["Mission Total XP"] += MISSION_POINTS[row.difficulty]
            self._xp[row.user_id]["Total XP"] += MISSION_POINTS[row.difficulty]
            self._xp[row.user_id][row.difficulty] += 1

    async def _compute_general_missions(self):
        query = """
            SELECT type, target, extra_target FROM tournament_missions WHERE id = $1 AND category = 'General';
        """

        general_mission = await self._tournament.client.database.get_one(
            query, self._tournament.id
        )

        if not general_mission:
            return

        if general_mission.type == MissionType.XP_THRESHOLD:
            for user_id, xp in self._xp.items():
                if xp["Total XP"] >= general_mission.target:
                    self._add_general_xp(user_id)

        elif general_mission.type == MissionType.MISSION_THRESHOLD:
            for user_id, data in self._xp.items():
                if data[general_mission.extra_target] >= general_mission.target:
                    self._add_general_xp(user_id)

        elif general_mission.type == MissionType.TOP_PLACEMENT:
            await self._compute_top_placement(general_mission.target)

    async def _compute_top_placement(self, target: int):
        query = """
            WITH t_records AS (SELECT tr.user_id, record, coalesce(ur.value, 'Unranked') as value, tr.category, rank()
                                        over (partition by ur.user_id, value, tr.category, ur.category order by inserted_at DESC) as date_rank
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
                           FROM t_records
                           WHERE date_rank = 1),
                 top_three AS (SELECT user_id, count(user_id) as amount
                               FROM ranks
                               WHERE rank_num <= 3
                               GROUP BY user_id)
            SELECT *
            FROM top_three
            WHERE amount >= $2;
        """
        async for row in self._tournament.client.database.get(
            query, self._tournament.id, target
        ):
            self._add_general_xp(row.user_id)

    def _add_general_xp(self, user_id: int):
        self._xp[user_id]["Mission Total XP"] += MISSION_POINTS[
            MissionDifficulty.GENERAL
        ]
        self._xp[user_id]["Total XP"] += MISSION_POINTS[MissionDifficulty.GENERAL]
        self._xp[user_id]["General"] = 1


# noinspection PyTypeChecker
class SpreadsheetCreator:
    _records: list[DotRecord] = []
    _split_records: dict[Rank, dict[Category, list[DotRecord]]] = {
        rank: {category: [] for category in Category.all()} for rank in Rank.all()
    }
    _workbook: xlsxwriter.Workbook = xlsxwriter.Workbook("DPK_Tournament.xlsx")
    _rank_worksheets: list[Worksheet] = []
    _missions_worksheet: Worksheet = None

    def __init__(
        self,
        tournament: TournamentData,
        xp: XP,
    ):
        self._tournament = tournament
        self._xp = xp

    @property
    def records(self) -> list[DotRecord]:
        return self._records

    async def create(self):
        await self._get_records()
        await asyncio.to_thread(self._init_workbook)

    async def _get_records(self):
        query = """
            WITH recs AS (SELECT tr.user_id, nickname, tr.category, tr.record, coalesce(ur.value, 'Unranked') as rank, rank()
                                        over (partition by nickname, value, tr.category, ur.category order by inserted_at DESC) as date_rank
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
                     record)
            SELECT * FROM recs WHERE date_rank = 1;    
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

    def _init_workbook(self):
        grandmaster = self._workbook.add_worksheet(name="Grandmaster")
        diamond = self._workbook.add_worksheet(name="Diamond")
        gold = self._workbook.add_worksheet(name="Gold")
        unranked = self._workbook.add_worksheet(name="Unranked")
        missions = self._workbook.add_worksheet(name="Missions")

        self._rank_worksheets: list[Worksheet] = [grandmaster, diamond, gold, unranked]
        self._missions_worksheet: Worksheet = missions
        self._format_sheets()
        self._write_mission_data()
        self._write_leaderboards()
        self._workbook.close()

    def _get_worksheet(self, name: str):
        return self._workbook.get_worksheet_by_name(name)

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
            "A1",
            [
                "Names",
                "Easy",
                "Medium",
                "Hard",
                "Expert",
                "General",
                "Missions Total",
                "Total XP",
            ],
            cell_format=self._workbook.add_format({"border": 1}),
        )

        self._missions_worksheet.set_column_pixels(0, 19, width=105)
        self._missions_worksheet.set_column(
            1, 5, cell_format=self._workbook.add_format({"align": "center"})
        )

    def _write_mission_data(self):
        for i, (user_id, data) in enumerate(self._xp.items(), start=2):
            self._get_worksheet("Missions")
            self._missions_worksheet.write_row(
                "A" + str(i),
                [
                    f"{data['nickname']} ({user_id})",
                    data["Easy"],
                    data["Medium"],
                    data["Hard"],
                    data["Expert"],
                    data["General"],
                    data["Mission Total XP"],
                    data["Total XP"],
                ],
            )
        self._missions_worksheet.set_column(
            1, 5, cell_format=self._workbook.add_format({"align": "center"})
        )

    def _write_leaderboards(self):
        for rank, categories in self._split_records.items():
            worksheet = self._get_worksheet(rank)
            for category, records in categories.items():
                for row_idx, record in enumerate(records, start=2):
                    worksheet.write(
                        row_idx,
                        COLUMN_MAPPER[category][0],
                        f"{record.nickname} ({record.user_id})",
                    )
                    worksheet.write(
                        row_idx,
                        COLUMN_MAPPER[category][1],
                        record.record,
                    )
                    worksheet.write(
                        row_idx,
                        COLUMN_MAPPER[category][2],
                        self._xp[record.user_id][category],
                    )
