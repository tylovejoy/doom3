import discord
from discord import app_commands


class MyCustomTranslator(app_commands.Translator):
    # async def load(self):
    #     # this gets called when the translator first gets loaded!
    #     ...
    #
    # async def unload(self):
    #     # in case you need to switch translators, this gets called when being removed
    #     ...

    async def translate(self, string: app_commands.locale_str, locale: discord.Locale,
                        context: app_commands.TranslationContext) -> str | None:
        """
        `locale_str` is the string that is requesting to be translated
        `locale` is the target language to translate to
        `context` is the origin of this string, eg TranslationContext.command_name, etc
        This function must return a string (that's been translated), or `None` to signal no available translation available, and will default to the original.
        """
        message_str = string.message

        # if message_str == "testing123" and locale == discord.Locale.german:
        #     return "tuesady"

        if locale == discord.Locale.british_english:
            british = {
                "submit-map": "subby-ey-mappa",
                "Submit your map to the database.": "OI, submib ya maappaaa.",
                "Overwatch share code": "Oivawatch share coyde",
                "Overwatch map": "Mappa name for Oivawatch",
            }
            return british.get(message_str, None)

        return None



