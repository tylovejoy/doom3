from __future__ import annotations

import datetime
import decimal
import re
import typing

from discord import Embed, app_commands

import cogs
import database
import utils
from utils import DoomEmbed

if typing.TYPE_CHECKING:
    import core


URL_REGEX = re.compile(
    r"^https?:\/\/(?:www\.)?"
    r"[-a-zA-Z0-9@:%._\+~#=]{1,256}\."
    r"[a-zA-Z0-9()]{1,6}\b"
    r"(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$"
)


class MapCodeTransformer(app_commands.Transformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> str:
        value = value.upper().replace("O", "0").lstrip().rstrip()
        if not re.match(utils.CODE_VERIFICATION, value):
            raise utils.IncorrectCodeFormatError
        return value


class MapCodeAutoTransformer(MapCodeTransformer):
    async def autocomplete(
        self, itx: core.Interaction[core.Doom], value: str
    ) -> list[app_commands.Choice[str]]:
        return await cogs.autocomplete(value, itx.client.map_codes_choices)


class MapCodeRecordsTransformer(MapCodeAutoTransformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> str:
        value = value.upper().replace("O", "0").lstrip().rstrip()

        if value not in itx.client.map_cache.keys():
            raise utils.InvalidMapCodeError

        if not re.match(utils.CODE_VERIFICATION, value):
            raise utils.IncorrectCodeFormatError

        return value


class MapLevelTransformer(app_commands.Transformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> str:
        if value not in itx.client.map_cache[itx.namespace.map_code]["levels"]:
            value = utils.fuzz_(value, itx.client.map_names)
        return value

    async def autocomplete(
        self, itx: core.Interaction[core.Doom], value: str
    ) -> list[app_commands.Choice[str]]:
        return await cogs.autocomplete(
            value,
            (itx.client.map_cache.get(itx.namespace.map_code, None)).get(
                "choices", None
            ),
        )


class UserTransformer(app_commands.Transformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> int:
        if value not in map(str, itx.client.all_users.keys()):
            raise utils.UserNotFoundError
        return int(value)

    async def autocomplete(
        self, itx: core.Interaction[core.Doom], value: str
    ) -> list[app_commands.Choice[str]]:
        return await cogs.autocomplete(value, itx.client.users_choices)


class RecordTransformer(app_commands.Transformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> float:
        try:
            value = utils.time_convert(value)
        except ValueError:
            raise utils.IncorrectRecordFormatError
        return value


class URLTransformer(app_commands.Transformer):
    async def transform(self, itx: core.Interaction[core.Doom], value: str) -> str:
        value = value.strip()
        if not value.startswith("https://") and not value.startswith("http://"):
            value = "https://" + value
        async with itx.client.session.get(value) as resp:
            if resp.status != 200:
                raise utils.IncorrectURLFormatError
            return str(resp.url)


def time_convert(string: str) -> float:
    """Convert HH:MM:SS.ss string into seconds (float)."""
    negative = -1 if string[0] == "-" else 1
    time = string.split(":")
    match len(time):
        case 1:
            res = float(time[0])
        case 2:
            res = float((int(time[0]) * 60) + (negative * float(time[1])))
        case 3:
            res = float(
                (int(time[0]) * 3600)
                + (negative * (int(time[1]) * 60))
                + (negative * float(time[2]))
            )
        case _:
            raise ValueError("Failed to match any cases.")
    return res


def pretty_record(record: decimal.Decimal | float) -> str:
    """
    The pretty_record property takes the record time for a given
    document and returns a string representation of that time.
    The function is used to display the record times in an easily
    readable format on the leaderboard page.

    Returns:
        A string
    """
    record = float(record)
    negative = "-" if record < 0 else ""
    dt = datetime.datetime.min + datetime.timedelta(seconds=abs(record))
    hour_remove = 0
    seconds_remove = -4

    if dt.hour == 0 and dt.minute == 0:
        hour_remove = 6
        if dt.second < 10:
            hour_remove += 1

    elif dt.hour == 0:
        hour_remove = 3
        if dt.minute < 10:
            hour_remove = 4

    if dt.microsecond == 0:
        seconds_remove = -4

    return negative + dt.strftime("%H:%M:%S.%f")[hour_remove:seconds_remove]


def all_levels_records_embed(
    records: list[database.DotRecord],
    title: str,
    single: bool = False,
) -> list[Embed | DoomEmbed]:
    embed_list = []
    embed = utils.DoomEmbed(title=title)
    for i, record in enumerate(records):
        if not record.video:
            description = (
                f"┣ `Name` {record.nickname}\n"
                f"┗ `Record` [{pretty_record(record.record)}]"
                f"({record.screenshot}) "
                f"{utils.HALF_VERIFIED}\n"
            )
        else:
            description = (
                f"┣ `Name` {record.nickname}\n"
                f"┣ `Record` [{pretty_record(record.record)}]"
                f"({record.screenshot}) "
                f"{utils.VERIFIED}\n "
                f"┗ `Video` [Link]({record.video})\n"
            )
        embed.add_field(
            name=f"{utils.PLACEMENTS.get(i + 1, '')} {make_ordinal(record.rank_num)}"
            if single
            else record.level_name,
            value=description,
            inline=False,
        )
        if (
            (i != 0 and i % 10 == 0)
            or (i == 0 and len(records) == 1)
            or i == len(records) - 1
        ):
            embed = utils.set_embed_thumbnail_maps(record.map_name, embed)
            embed_list.append(embed)
            embed = utils.DoomEmbed(title=title)
    return embed_list


def pr_records_embed(
    records: list[database.DotRecord],
    title: str,
) -> list[Embed | DoomEmbed]:
    embed_list = []
    embed = utils.DoomEmbed(title=title)
    description = ""
    cur_code = f"{records[0].map_name} by {records[0].creators} ({records[0].map_code})"
    for i, record in enumerate(records):
        if cur_code != f"{record.map_name} by {record.creators} ({record.map_code})":
            embed.add_field(
                name=f"{cur_code}",
                value="┗".join(description[:-3].rsplit("┣", 1)),
                inline=False,
            )
            description = ""
            cur_code = f"{record.map_name} by {record.creators} ({record.map_code})"
        if not record.video:
            description += (
                f"┣ `Level` ***{record.level_name}***\n"
                f"┣ `Record` [{pretty_record(record.record)}]"
                f"({record.screenshot}) "
                f"{utils.HALF_VERIFIED}\n┃\n"
            )
        else:
            description += (
                f"┣ `Level` ***{record.level_name}***\n"
                f"┣ `Record` [{pretty_record(record.record)}]"
                f"({record.screenshot})"
                f"{utils.VERIFIED}\n "
                f"┣ `Video` [Link]({record.video})\n┃\n"
            )
        if (
            (i != 0 and i % 10 == 0)
            or (i == 0 and len(records) == 1)
            or i == len(records) - 1
        ):
            embed.add_field(
                name=f"{cur_code}",
                value="┗".join(description[:-3].rsplit("┣", 1)),
                inline=False,
            )
            description = ""
            cur_code = f"{record.map_name} by {record.creators} ({record.map_code})"
            embed_list.append(embed)
            embed = utils.DoomEmbed(title=title)
    return embed_list


def make_ordinal(n: int) -> str:
    """
    Convert an integer into its ordinal representation::
        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    """
    n = int(n)
    suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    return str(n) + suffix
