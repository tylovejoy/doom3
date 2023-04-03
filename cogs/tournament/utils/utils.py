from __future__ import annotations

import datetime
import typing

import dateparser

from cogs.tournament.utils import Category

if typing.TYPE_CHECKING:
    pass

# TODO: Change these before prod
TA_ROLE = 841339455285886976
MC_ROLE = 841339569705844756
HC_ROLE = 841339590421381150
BO_ROLE = 841339621391859723
TRIFECTA_ROLE = 841378440078819378
BRACKET_ROLE = 841370294068576258

ANNOUNCEMENTS = 941737397316616192

role_map = {
    Category.TIME_ATTACK: TA_ROLE,
    Category.MILDCORE: MC_ROLE,
    Category.HARDCORE: HC_ROLE,
    Category.BONUS: BO_ROLE,
}


def parse(value: str) -> datetime.datetime:
    return dateparser.parse(value, settings={"PREFER_DATES_FROM": "future"})
