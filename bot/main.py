from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.add_player import router as add_player_router
from handlers.list_players import router as list_players_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(add_player_router)
dp.include_router(list_players_router)

if __name__ == "__main__":
    import asyncio
    async def main():
        print("Bot started")
        await dp.start_polling(bot)
    asyncio.run(main())