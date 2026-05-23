import asyncio
import os
import feedparser
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("BOT TOKEN NOT FOUND")
    raise SystemExit

CHANNEL_ID = "@footballradar11"

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

RSS_FEEDS = [
    "https://www.championat.com/rss/news/football/",
]

async def check_news():
    for url in RSS_FEEDS:

        print("CHECK RSS:", url)

        feed = feedparser.parse(url)

        for entry in feed.entries[:1]:

            title = entry.title

            print("NEWS:", title)

            try:
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=f"⚽ {title}"
                )

                print("MESSAGE SENT")

            except Exception as e:
                print("SEND ERROR:", e)

async def main():
    print("BOT STARTED")

    while True:
        try:
            await check_news()
        except Exception as e:
            print("MAIN ERROR:", e)

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
