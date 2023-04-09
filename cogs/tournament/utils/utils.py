from __future__ import annotations

import datetime
import typing

import dateparser

from cogs.tournament.utils import Category

if typing.TYPE_CHECKING:
    pass

TA_ROLE = 814532908638404618
MC_ROLE = 814532865672478760
HC_ROLE = 814532947461013545
BO_ROLE = 839952576866025543
TRIFECTA_ROLE = 814533106244649030
BRACKET_ROLE = 830425028839211028

ANNOUNCEMENTS = 774436274542739467

role_map = {
    Category.TIME_ATTACK: TA_ROLE,
    Category.MILDCORE: MC_ROLE,
    Category.HARDCORE: HC_ROLE,
    Category.BONUS: BO_ROLE,
}


def parse(value: str) -> datetime.datetime:
    return dateparser.parse(value, settings={"PREFER_DATES_FROM": "future"})
