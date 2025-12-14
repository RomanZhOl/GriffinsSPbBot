from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.add_player import router as add_player_router
from handlers.list_players import router as list_players_router
from handlers.create_poll import router as create_poll_router
from handlers.update_players import router as update_players_router
from handlers.cancel import router as cancel_router
import logging

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(add_player_router)
dp.include_router(list_players_router)
dp.include_router(create_poll_router)
dp.include_router(update_players_router)
dp.include_router(cancel_router)

if __name__ == "__main__":
    import asyncio
    async def main():
        print("Bot started")
        await dp.start_polling(bot)
    asyncio.run(main())