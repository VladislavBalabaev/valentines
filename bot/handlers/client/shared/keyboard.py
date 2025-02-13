from aiogram import types


def create_reply_keyboard(choices, buttons_per_row = 3):
    """
    Creates a reply keyboard with the provided choices. Each choice is displayed as a button.
    The keyboard is resized for better display. A maximum of 3 buttons is allowed per row.
    """
    choices_list = list(choices)

    buttons = [
        [types.KeyboardButton(text=choice.value) for choice in choices_list[i:i + buttons_per_row]]
        for i in range(0, len(choices_list), buttons_per_row)
    ]
    
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def create_inline_board(choices):
    """
    Creates an inline keyboard with the provided choices. Each choice is displayed as a button,
    and each button is placed on a separate row.
    """
    choices_list = list(choices)

    # Create buttons and group each button into its own list (so that each button appears in a new row)
    buttons = [[types.InlineKeyboardButton(text=choice.value, callback_data=choice.value)] for choice in choices_list]

    # Set row_width to 1 to place each button on a separate row
    return types.InlineKeyboardMarkup(inline_keyboard=buttons, row_width=1)
