from __future__ import annotations

import json
import typing

import discord
from discord import app_commands

if typing.TYPE_CHECKING:
    from core import DoomItx


with open("assets/translations.json", encoding="utf8") as f:
    translations = json.load(f)


class DoomTranslator(app_commands.Translator):
    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> str | None:
        if locales := translations.get(string.message, None):
            return locales.get(locale.value)
        return None


async def translate_helper(
    itx: DoomItx,
    string: str | app_commands.locale_str,
    *,
    locale: discord.Locale = discord.utils.MISSING,
    data: typing.Any = discord.utils.MISSING,
) -> str | None:
    _translate = await itx.translate(string, locale=locale, data=data)
    return string if _translate is None else _translate
