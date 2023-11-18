import asyncio

from telegram import Bot

from settings import CONFIG


def send_direct_message(msg: str) -> None:
    async def send():
        bot = Bot(token=CONFIG.TELEGRAM_BOT_TOKEN)

        await bot.send_message(
            chat_id=CONFIG.TELEGRAM_CHAT_ID,
            text=msg,
            parse_mode="HTML",
        )

    asyncio.run(send())
