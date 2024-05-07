import math

import discord

STAR = "★"
EMPTY_STAR = "☆"


def create_stars(rating: int | float | None) -> str:
    if not rating:
        return "Unrated"
    filled = math.ceil(rating) * STAR
    return filled + ((5 - len(filled)) * EMPTY_STAR)


def generate_all_stars() -> list[str]:
    return [create_stars(x) for x in range(6)]


ALL_STARS = generate_all_stars()
ALL_STARS_CHOICES = [discord.app_commands.Choice(name=x, value=i) for i, x in enumerate(ALL_STARS)]
