import emoji
import pandas as pd


def distinct_emoji_list():
    """
    Returns a list of simple, non-complex emojis. 
    Filters out emojis with special characters like skin tone modifiers or those that are composed of multiple code points.
    """
    def is_simple_emoji(emj):
        """
        Determines if an emoji is 'simple' by ensuring it does not contain special characters 
        or consist of multiple code points.
        """
        if '\\U000' in repr(emj):
            return False

        # Extended list of special characters and sequences that indicate complex emojis
        special_chars = [
            '\u200d',  # Zero-width joiner
            '\ufe0f',  # Variation selector for emoji style
            '\u0020',  # Space character
            '\u2640',  # Female sign
            '\u2642',  # Male sign
            '\U0001f3fb', '\U0001f3fc', '\U0001f3fd', '\U0001f3fe', '\U0001f3ff',  # Skin tone modifiers
            '\u200b',  # Zero-width space
            '\u200c',  # Zero-width non-joiner
            '\u200e',  # Left-to-right mark
            '\u200f',  # Right-to-left mark
            '\u2028',  # Line separator
            '\u2029',  # Paragraph separator
        ]

        # Check if emoji contains any of the special characters or is a sequence of multiple code points
        return not any(char in emj for char in special_chars) and len(emj) == len(emj.encode('utf-16', 'surrogatepass').decode('utf-16'))


    def is_non_letter_emoji(emj):
        """
        Filters out emojis that are regional indicator symbols (i.e., flag characters).
        """
        regional_indicator_range = range(0x1F1E6, 0x1F1FF + 1)

        return not all(ord(char) in regional_indicator_range for char in emj)


    emojis = pd.Series(emoji.unicode_codes.EMOJI_DATA.keys()).unique().tolist()
    emojis = [i for i in emojis if is_simple_emoji(i) and is_non_letter_emoji(i)]

    return emojis
