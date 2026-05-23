import asyncio
import os
import feedparser
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

# ====== TOKEN ======
TOKEN = os.getenv("BOT_TOKEN")

if TOKEN is None:
    print("❌ BOT_TOKEN не найден в переменных окружения Railway")
    print("👉 Добавь BOT_TOKEN в Railway → Variables")
    raise SystemExit()

# ====== CONFIG ======
CHANNEL_ID = "@footballradar11"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

RSS_FEEDS = [
    "https://www.championat.com/rss/news/football/",
]

# ====== CHECK NEWS ======
async def check_news():
    for url in RSS_FEEDS:
        print("🔎 CHECK RSS:", url)

        feed = feedparser.parse(url)

        if not feed.entries:
            print("⚠️ Нет новостей в RSS")
            continue

        for entry in feed.entries[:1]:
            title = entry.get("title", "Без заголовка")

            print("📰 NEWS:", title)

            try:
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=f"⚽ {title}"
                )
                print("✅ MESSAGE SENT")

            except Exception as e:
                print("❌ SEND ERROR:", e)

# ====== MAIN LOOP ======
async def main():
    print("🚀 BOT STARTED")

    while True:
        try:
            await check_news()
        except Exception as e:
            print("❌ MAIN ERROR:", e)

        await asyncio.sleep(60)

# ====== START ======
if __name__ == "__main__":
    asyncio.run(main())
