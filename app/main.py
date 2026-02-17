import asyncio
from aiogram import Bot, Dispatcher

from app.config import load_settings
from app.db.connect import Db
from app.db.repo import ProductRepo
from app.services.catalog_service import CatalogService
from app.handlers import start
from app.handlers.catalog import bind as bind_catalog
from app.handlers.admin import bind_admin
from app.handlers.ui import bind_ui



async def main():
    settings = load_settings()

    db = Db(settings.db_path)
    await db.connect()

    bot = Bot(settings.bot_token)
    dp = Dispatcher()

    repo = ProductRepo(db.conn, page_size=settings.page_size)
    service = CatalogService(repo)

    dp.include_router(start.router)
    dp.include_router(bind_catalog(service))
    dp.include_router(bind_admin(repo, settings.admin_ids))
    dp.include_router(bind_ui(repo, settings.admin_ids))


    try:
        await dp.start_polling(bot)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
