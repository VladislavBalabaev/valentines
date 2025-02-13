from aiogram import Bot, Dispatcher

from configs.env_reader import config


bot = Bot(token=config.TG_BOT_TOKEN.get_secret_value())

dp = Dispatcher()
