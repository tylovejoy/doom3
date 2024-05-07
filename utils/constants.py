import math

import discord

VERIFIED = "<:_:1042541867469910056>"
HALF_VERIFIED = "<:_:1042541868723998871>"
UNVERIFIED = "<:_:1042541865821556746>"
TROPHY = "🏆"

TIME = "⌛"

VERIFIED_EMOJI = discord.PartialEmoji.from_str(VERIFIED)
HALF_VERIFIED_EMOJI = discord.PartialEmoji.from_str(HALF_VERIFIED)
UNVERIFIED_EMOJI = discord.PartialEmoji.from_str(UNVERIFIED)

FIRST = "<:_:1043226244575142018>"
SECOND = "<:_:1043226243463659540>"
THIRD = "<:_:1043226242335391794>"

PLACEMENTS = {
    1: FIRST,
    2: SECOND,
    3: THIRD,
}


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
