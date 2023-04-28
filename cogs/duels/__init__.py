from __future__ import annotations

import typing

from cogs.duels.start_duel import Duels

if typing.TYPE_CHECKING:
    import core


async def setup(bot: core.Doom):
    await bot.add_cog(Duels(bot))
