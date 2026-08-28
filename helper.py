SPECIAL_WORDS_MAP = {
    "3d": "3D",
    "uv2": "UV2",
    "2d": "2D"
}

def to_pascal_case(string: str) -> str:
    stripped = string.lstrip("_")
    leading_underscores = "_" * (len(string) - len(stripped))

    words = stripped.split("_")

    return (
        leading_underscores
        + "".join(
            SPECIAL_WORDS_MAP.get(
                word.lower(),
                word[:1].upper() + word[1:]
            )
            for word in words
        )
    )