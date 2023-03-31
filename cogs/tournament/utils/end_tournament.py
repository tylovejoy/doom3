from functools import reduce
from operator import concat
from typing import Literal

from cogs.tournament.utils.data import TournamentData
from cogs.tournament.utils.utils import MissionDifficulty
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
}
Ranks = Literal["Gold", "Diamond", "Grandmaster", "Unranked"]


class ExperienceCalculator:
    def __init__(
        self,
        tournament: TournamentData,
        records: dict[Ranks, list[DotRecord]],
        missions,
    ):
        self.split_ranks = records
        self.all_records = reduce(concat, self.split_ranks.values())
        self.tournament = tournament
        self.missions = missions
        self.xp_store = self.init_xp_store()

    @staticmethod
    def leaderboard_xp_formula(category, record, top_record):
        formula = (
            1 - (record.record - top_record) / (XP_MULTIPLIER[category] * top_record)
        ) * 2500
        if formula < 100:
            xp = 100
        else:
            xp = formula
        return xp

    def init_xp_store(self) -> dict[int, dict[str, int]]:
        """Initialize the XP dictionary. Fill with all active players."""
        store = {}
        for category in self.tournament.categories:
            records = self.split_ranks[category]
            for record in records:
                if not store.get(record.user_id):
                    store[record.user_id] = {
                        "Easy": 0,
                        "Medium": 0,
                        "Hard": 0,
                        "Expert": 0,
                        "General": 0,
                        "Time Attack": 0,
                        "Mildcore": 0,
                        "Hardcore": 0,
                        "Bonus": 0,
                        "XP": 0,
                    }
        return store

    def leaderboard_xp(self):
        for category, records in self.split_ranks.items():
            if not records:
                continue
            top_record = records[0].record
            for record in records:
                xp = await self.leaderboard_xp_formula(category, record, top_record)
                self.xp_store[record.user_id][category] += xp
                self.xp_store[record.user_id]["XP"] += xp

    def compute_mission_xp(self):
        """Compute the XP from difficulty based missions."""

        for category in self.tournament.categories:
            records = self.all_records.records
            missions = category_attr.missions
            for record in records:
                store = await mission_complete_check(missions, record, store)
        return store

    def mission_complete_check(self, missions, record, store: dict) -> dict:
        # Goes hardest to easiest, because highest mission only
        for mission_category in MISSION_CATEGORIES:
            mission: TournamentMissions = getattr(missions, mission_category, None)
            if not mission:
                continue

            type_ = mission.type
            target = mission.target

            if (type_ == "sub" and record.record < float(target)) or (
                type_ == "complete" and record.record
            ):
                store[record.user_id][mission_category] += 1
                store[record.user_id]["xp"] += MISSION_POINTS[mission_category]
                break
        return store

    def compute_xp(self):
        self.leaderboard_xp()
