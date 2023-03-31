from __future__ import annotations

import typing

from .leaderboard import TournamentLeaderboards
from .missions import Missions

if typing.TYPE_CHECKING:
    import core
from .tournament_start import Tournament
from .submissions import TournamentSubmissions


async def setup(bot: core.Doom):
    await bot.add_cog(Tournament(bot))
    await bot.add_cog(TournamentSubmissions(bot))
    await bot.add_cog(TournamentLeaderboards(bot))
    await bot.add_cog(Missions(bot))