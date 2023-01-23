import json

import discord
from discord import app_commands


with open("assets/translations.json") as f:
    translations = json.load(f)


class DoomTranslator(app_commands.Translator):
    async def translate(
        self,
        string: app_commands.locale_str,
        locale: discord.Locale,
        context: app_commands.TranslationContext,
    ) -> str | None:
        locales = translations.get(string.message, None)
        if locales:
            return locales.get(locale.value)
        return None
