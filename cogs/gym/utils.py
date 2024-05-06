from __future__ import annotations

import math
from typing import TYPE_CHECKING, Literal

from discord import app_commands

import cogs
import utils
from utils import BaseParkourException

if TYPE_CHECKING:
    from core import DoomItx

Units = Literal["kg", "lb"]


TARGETS = Literal[
    "abductors",
    "abs",
    "adductors",
    "biceps",
    "calves",
    "cardiovascular system",
    "delts",
    "forearms",
    "glutes",
    "hamstrings",
    "lats",
    "levator scapulae",
    "pectorals",
    "quads",
    "serratus anterior",
    "spine",
    "traps",
    "triceps",
    "upper back",
]

BODY_PARTS = Literal[
    "back",
    "cardio",
    "chest",
    "lower arms",
    "lower legs",
    "neck",
    "shoulders",
    "upper arms",
    "upper legs",
    "waist",
]

EQUIPMENT = Literal[
    "assisted",
    "band",
    "barbell",
    "body weight",
    "bosu ball",
    "cable",
    "dumbbell",
    "elliptical machine",
    "ez barbell",
    "kettlebell",
    "leverage machine",
    "medicine ball",
    "resistance band",
    "skierg machine",
    "sled machine",
    "smith machine",
    "stability ball",
    "stationary bike",
    "stepmill machine",
    "trap bar",
    "upper body ergometer",
    "weighted",
    "wheel roller",
]


class OneRepMax:
    @classmethod
    def formulas(cls):
        return {
            "Brzycki": cls.brzycki_1rm,
            "Epley": cls.epley_1rm,
            "Lander": cls.lander_1rm,
            "Lombardi": cls.lombardi_1rm,
            "Mayhew": cls.mayhew_1rm,
            "O'Conner": cls.oconner_1rm,
            "Wathen": cls.wathen_1rm,
        }

    @staticmethod
    def brzycki_1rm(weight: float, reps: int) -> float:
        return weight * (36 / (37 - reps))

    @staticmethod
    def epley_1rm(weight: float, reps: int) -> float:
        return weight * (1 + reps / 30)

    @staticmethod
    def lander_1rm(weight: float, reps: int) -> float:
        return 100 * (weight / (101.3 - 2.67123 * reps))

    @staticmethod
    def lombardi_1rm(weight: float, reps: int) -> float:
        return (weight * reps) ** 0.1

    @staticmethod
    def mayhew_1rm(weight: float, reps: int) -> float:
        return (100 * weight) / (52.2 + 41.9 * math.e ** (-0.055 * reps))

    @staticmethod
    def oconner_1rm(weight: float, reps: int) -> float:
        return weight * (1 + reps / 40)

    @staticmethod
    def wathen_1rm(weight: float, reps: int) -> float:
        return (100 * weight) / (48.8 + 53.8 * math.e ** (-0.075 * reps))


class ExerciseTransformer(app_commands.Transformer):
    async def transform(self, itx: DoomItx, value: str) -> str:
        if value not in itx.client.exercise_category_map:
            value = utils.fuzz_(value, itx.client.exercise_category_map)
        return value

    async def autocomplete(self, itx: DoomItx, value: int | float | str) -> list[app_commands.Choice[str]]:
        return await cogs.autocomplete(value, itx.client.exercise_names)


class DuplicateExercise(BaseParkourException):
    """This exercise already exists."""


class ExerciseDoesntExist(BaseParkourException):
    """This exercise does not exist."""
