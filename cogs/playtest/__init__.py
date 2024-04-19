from __future__ import annotations

from typing import TYPE_CHECKING

from .playtest import Playtesting, PlaytestButton

if TYPE_CHECKING:
    import core


async def setup(bot: core.Doom):
    await bot.add_cog(Playtesting(bot))
    bot.add_dynamic_items(PlaytestButton)
