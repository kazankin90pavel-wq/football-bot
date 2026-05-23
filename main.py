import asyncio
import feedparser
import os
import re
import hashlib
from difflib import SequenceMatcher

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN", "8965358674:AAFxS_fde2c-EIltILySwB4rQmV1itTAUFA")
CHANNEL_ID = "@footballradar11"

RSS_FEEDS = [
    "https://www.championat.com/rss/news/football/",
    "https://www.soccer.ru/rss",
    "https://www.euro-football.ru/article/29/feed",
    "https://www.skysports.com/rss/12040",
]

POST_DELAY = 1800
MAX_POSTS_PER_RUN = 1

# ================= BOT INIT (ВАЖНО) =================

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()

# ================= STORAGE =================

sent_file = "sent_news.txt"

def load_sent():
    if not os.path.exists(sent_file):
        return set()
    with open(sent_file, "r", encoding="utf-8") as f:
        return set(f.read().splitlines())

def save_sent(news_id):
    with open(sent_file, "a", encoding="utf-8") as f:
        f.write(news_id + "\n")

sent_news = load_sent()

# ================= TEXT CLEAN =================

def strip_links(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ================= NORMALIZE =================

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    text = re.sub(r"[^a-zA-Zа-яА-Я0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

recent_titles = []

def is_duplicate(title):
    global recent_titles
    clean_title = normalize_text(title)

    for old in recent_titles:
        if SequenceMatcher(None, clean_title, old).ratio() > 0.75:
            return True

    recent_titles.append(clean_title)
    recent_titles = recent_titles[-200:]
    return False

def make_id(title):
    return hashlib.md5(normalize_text(title).encode()).hexdigest()

# ================= FILTER =================

def is_football(text: str) -> bool:
    keywords = ["футбол", "матч", "гол", "лига", "uefa", "transfer", "goal", "league"]
    return any(k in text.lower() for k in keywords)

def is_transfer(text: str) -> bool:
    keywords = ["transfer", "signed", "loan", "deal", "контракт", "перешел"]
    return any(k in text.lower() for k in keywords)

# ================= IMAGE =================

def get_image(entry):
    if hasattr(entry, "media_content"):
        try:
            return entry.media_content[0]["url"]
        except:
            pass

    if hasattr(entry, "media_thumbnail"):
        try:
            return entry.media_thumbnail[0]["url"]
        except:
            pass

    return None

# ================= POSTS =================

def media_post(title, summary):
    summary = strip_links(summary)[:350]
    return f"""⚽ BREAKING

<b>{title}</b>

📰 {summary}

🏟 Football Radar"""

def romano_post(title, summary):
    summary = strip_links(summary)[:300]
    return f"""🚨 TRANSFER UPDATE

<b>{title}</b>

📰 {summary}

🔥 Negotiations ongoing
🏟 Football Radar"""

# ================= CHECK NEWS =================

async def check_news():
    posted = 0

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in reversed(feed.entries[:20]):

            if posted >= MAX_POSTS_PER_RUN:
                return

            title = strip_links(entry.title)

            if is_duplicate(title):
                continue

            summary = strip_links(getattr(entry, "summary", ""))

            full_text = title + " " + summary

            if not is_football(full_text):
                continue

            news_id = make_id(title)

            if news_id in sent_news:
                continue

            image = get_image(entry)
            if not image:
                continue

            if is_transfer(full_text):
                text = romano_post(title, summary)
            else:
                text = media_post(title, summary)

            try:
                await bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image,
                    caption=text
                )

                sent_news.add(news_id)
                save_sent(news_id)

                posted += 1
                print("✔ Posted:", title)

            except Exception as e:
                print("ERROR:", e)

            await asyncio.sleep(POST_DELAY)

# ================= MAIN =================

async def main():
    print("⚽ BOT STARTED")

    while True:
        await check_news()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())