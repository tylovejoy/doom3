from __future__ import annotations

import datetime
import enum
import typing

import dateparser
from discord import app_commands

if typing.TYPE_CHECKING:
    import core

# TODO: Change these before prod
TA_ROLE = 841339455285886976
MC_ROLE = 841339569705844756
HC_ROLE = 841339590421381150
BO_ROLE = 841339621391859723
TRIFECTA_ROLE = 841378440078819378
BRACKET_ROLE = 841370294068576258

ANNOUNCEMENTS = 941737397316616192


class Category(enum.StrEnum):
    TIME_ATTACK = "ta"
    MILDCORE = "mc"
    HARDCORE = "hc"
    BONUS = "bo"

    @classmethod
    def all(cls) -> list[str]:
        return [cls.TIME_ATTACK, cls.MILDCORE, cls.HARDCORE, cls.BONUS]


class MissionCategory(enum.StrEnum):
    TIME_ATTACK = "Time Attack"
    MILDCORE = "Mildcore"
    HARDCORE = "Hardcore"
    BONUS = "Bonus"
    GENERAL = "General"


class MissionDifficulty(enum.StrEnum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXPERT = "Expert"
    GENERAL = "General"


class MissionType(enum.StrEnum):
    XP_THRESHOLD = "XP Threshold"
    MISSION_THRESHOLD = "Mission Threshold"
    TOP_PLACEMENT = "Top Placement"
    SUB_TIME = "Sub Time"
    COMPLETION = "Completion"

    @classmethod
    def general(cls):
        return [cls.SUB_TIME, cls.COMPLETION]

    @classmethod
    def difficulty(cls):
        return [cls.XP_THRESHOLD, cls.MISSION_THRESHOLD, cls.TOP_PLACEMENT]


role_map = {
    Category.TIME_ATTACK: TA_ROLE,
    Category.MILDCORE: MC_ROLE,
    Category.HARDCORE: HC_ROLE,
    Category.BONUS: BO_ROLE,
}

full_title_map = {
    Category.TIME_ATTACK: "Time Attack",
    Category.MILDCORE: "Mildcore",
    Category.HARDCORE: "Hardcore",
    Category.BONUS: "Bonus",
}

reverse_title_map = {v: k for k, v in full_title_map.items()}


class CategoryData(typing.TypedDict):
    code: str
    level: str


def parse(value: str) -> datetime.datetime:
    return dateparser.parse(value, settings={"PREFER_DATES_FROM": "future"})
