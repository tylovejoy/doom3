from __future__ import annotations

import enum
import typing
from typing import Literal, TypedDict

Categories = typing.Literal["Time Attack", "Mildcore", "Hardcore", "Bonus", "General"]
Categories_NoGen = typing.Literal["Time Attack", "Mildcore", "Hardcore", "Bonus"]
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
Ranks = Literal["Gold", "Diamond", "Grandmaster", "Unranked"]


class Rank(enum.StrEnum):
    UNRANKED = "Unranked"
    GOLD = "Gold"
    DIAMOND = "Diamond"
    GRANDMASTER = "Grandmaster"

    @classmethod
    def all(cls) -> list[Rank]:
        return [cls.UNRANKED, cls.GOLD, cls.DIAMOND, cls.GRANDMASTER]


class Category(enum.StrEnum):
    TIME_ATTACK = "Time Attack"
    MILDCORE = "Mildcore"
    HARDCORE = "Hardcore"
    BONUS = "Bonus"
    GENERAL = "General"

    @classmethod
    def all(cls) -> list[Category]:
        return [cls.TIME_ATTACK, cls.MILDCORE, cls.HARDCORE, cls.BONUS]


class MissionDifficulty(enum.StrEnum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXPERT = "Expert"
    GENERAL = "General"

    @classmethod
    def diffs(cls):
        return [cls.EASY, cls.MEDIUM, cls.HARD, cls.EXPERT]

class MissionType(enum.StrEnum):
    XP_THRESHOLD = "XP Threshold"
    MISSION_THRESHOLD = "Mission Threshold"
    TOP_PLACEMENT = "Top Placement"
    SUB_TIME = "Sub Time"
    COMPLETION = "Completion"

    @classmethod
    def difficulty(cls):
        return [cls.SUB_TIME, cls.COMPLETION]

    @classmethod
    def general(cls):
        return [cls.XP_THRESHOLD, cls.MISSION_THRESHOLD, cls.TOP_PLACEMENT]


class CategoryData(TypedDict):
    code: str
    level: str
    creator: str


class MissionData(TypedDict):
    mission_type: MissionType
    target: float


BaseXP = {
    "nickname": "",
    "Easy": 0,
    "Medium": 0,
    "Hard": 0,
    "Expert": 0,
    "General": 0,
    "Mission Total XP": 0,
    "Total XP": 0,
    "Time Attack": 0,
    "Mildcore": 0,
    "Hardcore": 0,
    "Bonus": 0,
}
