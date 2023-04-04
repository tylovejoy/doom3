import math

import discord

GUILD_ID = 689587520496730129  # 195387617972322306

STAFF = 854144700842639360  # 1047262740315643925


VERIFIED = "<:_:1042541867469910056>"
HALF_VERIFIED = "<:_:1042541868723998871>"
UNVERIFIED = "<:_:1042541865821556746>"

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
    return filled + ((6 - len(filled)) * EMPTY_STAR)


def generate_all_stars() -> list[str]:
    return [create_stars(x) for x in range(7)]


ALL_STARS = generate_all_stars()
ALL_STARS_CHOICES = [
    discord.app_commands.Choice(name=x, value=i) for i, x in enumerate(ALL_STARS)
]

NEW_MAPS = 856605387050188821  # 856602254769782835
VERIFICATION_QUEUE = 813768098191769640  # 811467249100652586

SPR_RECORDS = 693673770086301737  # 801496775390527548
RECORDS = 860291006493491210  # 856513618091049020
TOP_RECORDS = 873572468982435860

HALL_OF_FAME_ID = 931959281845157978  # TODO: this needs to be prod ready
TOURNAMENT_SUBMISSIONS = 840408122181812225  # This too