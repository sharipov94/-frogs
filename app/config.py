from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str
    db_path: str
    page_size: int
    admin_ids: tuple[int, ...]

def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is empty in .env")

    db_path = os.getenv("DB_PATH", "shop.db").strip()
    page_size = int(os.getenv("PAGE_SIZE", "5").strip())

    raw_admins = os.getenv("ADMIN_IDS", "").strip()
    admin_ids: tuple[int, ...] = tuple(
        int(x.strip()) for x in raw_admins.split(",") if x.strip()
    )
    if not admin_ids:
        raise RuntimeError("ADMIN_IDS is empty in .env")

    return Settings(
        bot_token=token,
        db_path=db_path,
        page_size=page_size,
        admin_ids=admin_ids,
    )
