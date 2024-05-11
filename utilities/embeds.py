import discord


class EmbedFormatter:
    @staticmethod
    def _wrap_str_code_block(value: str) -> str:
        return f"` {value:>4} `"

    @classmethod
    def format(cls, values: dict[str, str]) -> str:
        res = ""
        filtered_values = {k: v for k, v in values.items() if v is not False and v is not None and v != ""}.items()
        for name, value in filtered_values:
            wrapped_name = cls._wrap_str_code_block(name)
            res += f"{wrapped_name} {value}\n"
        return ">>> " + res


class Embed(discord.Embed):
    def __init__(
        self,
        *,
        color: int | discord.Color | None = None,
        title: str | None = None,
        url: str | None = None,
        description: str | None = None,
        thumbnail: str | None = None,
        image: str | None = None,
    ):
        if not color:
            color = discord.Color.from_rgb(1, 1, 1)

        super().__init__(color=color, title=title, url=url, description=description)

        if not thumbnail:
            self.set_thumbnail(url="https://i.imgur.com/kxjwdYi.png")
        else:
            self.set_thumbnail(url=thumbnail)

        if not image:
            self.set_image(url="https://i.imgur.com/YhJokJW.png")
        else:
            self.set_image(url=image)

    def add_description_field(self, name: str, value: str):
        if not self.description:
            self.description = ""
        self.description += f"```ansi\n\u001b[1;37m{name}\n```{value}\n"  # \u001b[{format};{color}m


class ErrorEmbed(discord.Embed):
    def __init__(
        self,
        *,
        description: str,
        unknown: bool = False,
    ):
        if unknown:
            super().__init__(
                title="Uh oh! Something went wrong.",
                description=description,
                color=discord.Color.red(),
            )
            self.set_thumbnail(url="http://bkan0n.com/assets/images/icons/error.png")
        else:
            super().__init__(
                title="What happened?",
                description=description,
                color=discord.Color.yellow(),
            )

            self.set_footer(text="If you have any questions, message nebula#6662")
