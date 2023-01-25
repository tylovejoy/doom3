import json
import math
import random

with open("assets/emoji-data.json", "r", encoding="utf8") as f:
    mapping = json.load(f)

common_words = [
    "a",
    "an",
    "as",
    "is",
    "if",
    "of",
    "the",
    "it",
    "its",
    "or",
    "are",
    "this",
    "with",
    "so",
    "to",
    "at",
    "was",
    "and",
]


def emojify(text: str) -> str:
    text = text.split()
    res = ""
    for raw in text:
        word = raw.lower()
        random_choice = random.random() * 100 <= 100
        is_common = word in common_words
        emojis = []

        temp_map = mapping.get(word, None)
        if temp_map:
            for emoji, freq in temp_map.items():
                emojis += [emoji] * freq

        if is_common or not random_choice or len(emojis) == 0:
            res += raw
        else:
            emojis = emojis[math.floor(random.random() * len(emojis))]
            res += f"{raw} {emojis}"
        res += " "
    return res


def uwuify(string: str) -> str:
    res = ""
    for ch in string:
        if ch in "lr":
            ch = "w"
        elif ch in "LR":
            ch = "W"
        res += ch

    return res
