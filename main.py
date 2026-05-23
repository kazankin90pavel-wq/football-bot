from aiogram import Bot
import asyncio
import feedparser
import os
import re
import random
import hashlib
from difflib import SequenceMatcher

# ================= CONFIG =================
TOKEN = "8965358674:AAFYv8_GXcYJ-biwnLN3gXzfXj0Tx1_6oCo"
CHANNEL_ID = "@footballradar11"

RSS_FEEDS = [
    "https://www.championat.com/rss/news/football/",
    "https://www.soccer.ru/rss",
    "https://www.euro-football.ru/article/29/feed",
    "https://www.skysports.com/rss/12040",
]

POST_DELAY = 1800  # 30 минут
MAX_POSTS_PER_RUN = 1

bot = Bot(token=TOKEN)

sent_file = "sent_news.txt"

# ================= STORAGE =================
def load_sent():
    if not os.path.exists(sent_file):
        return set()

    with open(sent_file, "r", encoding="utf-8") as f:
        return set(f.read().splitlines())


def save_sent(news_id):
    with open(sent_file, "a", encoding="utf-8") as f:
        f.write(news_id + "\n")


sent_news = load_sent()

# ================= RANDOM STYLES =================
MEDIA_HEADS = [
    "⚽ BREAKING",
    "📰 FOOTBALL NEWS",
    "🔥 MATCH UPDATE",
    "📢 REPORT",
    "⚡ LATEST NEWS"
]

TRANSFER_HEADS = [
    "🟥 TRANSFER UPDATE",
    "🚨 HERE WE GO STYLE",
    "⚡ BREAKING TRANSFER",
    "📢 DEAL NEWS",
    "🔥 TRANSFER LATEST"
]

FOOTER = [
    "🏟 Футбольный радар",
    "⚽ Live Football Feed",
    "📊 Match Intelligence"
]

# ================= CLEANER =================
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


# ================= TEXT NORMALIZER =================
def normalize_text(text):
    text = text.lower()

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)

    text = re.sub(r"[^a-zA-Zа-яА-Я0-9 ]", "", text)

    words_to_remove = [
        "official",
        "breaking",
        "report",
        "exclusive",
        "confirmed",
        "update",
        "football",
        "soccer",
        "fc",
        "cf"
    ]

    for word in words_to_remove:
        text = text.replace(word, "")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ================= DUPLICATE CHECK =================
recent_titles = []


def is_duplicate(title):
    global recent_titles

    clean_title = normalize_text(title)

    for old_title in recent_titles:
        similarity = SequenceMatcher(
            None,
            clean_title,
            old_title
        ).ratio()

        if similarity > 0.75:
            return True

    recent_titles.append(clean_title)

    # храним последние 200 новостей
    recent_titles = recent_titles[-200:]

    return False


# ================= HASH =================
def make_id(title):
    text = normalize_text(title)
    return hashlib.md5(text.encode()).hexdigest()


# ================= FOOTBALL FILTER =================
def is_football(text: str) -> bool:
    keywords = [
        "футбол",
        "матч",
        "гол",
        "лига",
        "чемпионат",
        "трансфер",
        "аренда",
        "контракт",
        "uefa",
        "fifa",
        "premier",
        "laliga",
        "bundesliga",
        "serie a",
        "champions league",
        "europa league",
        "transfer",
        "signed",
        "loan",
        "deal",
        "goal"
    ]

    t = text.lower()

    return any(k in t for k in keywords)


# ================= TRANSFER DETECTOR =================
def is_transfer(text: str) -> bool:
    keywords = [
        "transfer",
        "signed",
        "loan",
        "deal",
        "join",
        "joins",
        "agreement",
        "medical",
        "перешел",
        "перешёл",
        "трансфер",
        "аренда",
        "контракт"
    ]

    t = text.lower()

    return any(k in t for k in keywords)


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

    if hasattr(entry, "links"):
        for link in entry.links:
            if "image" in link.get("type", ""):
                return link.get("href")

    return None


# ================= POSTS =================
def media_post(title, summary):
    summary = strip_links(summary)

    if len(summary) > 350:
        summary = summary[:350] + "..."

    head = random.choice(MEDIA_HEADS)
    footer = random.choice(FOOTER)

    return f"""{head}

⚽ <b>{title}</b>

📰 {summary}

{footer}
"""


def romano_post(title, summary):
    summary = strip_links(summary)

    if len(summary) > 300:
        summary = summary[:300] + "..."

    head = random.choice(TRANSFER_HEADS)
    footer = random.choice(FOOTER)

    return f"""{head}

⚽ <b>{title}</b>

📰 {summary}

🚨 Negotiations ongoing, final details being discussed.

{footer}
"""


# ================= NEWS CHECK =================
async def check_news():
    posted = 0

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in reversed(feed.entries[:20]):

            if posted >= MAX_POSTS_PER_RUN:
                return

            title = strip_links(entry.title)

            # анти-дубликат
            if is_duplicate(title):
                continue

            raw_summary = ""

            if hasattr(entry, "content") and entry.content:
                raw_summary = entry.content[0].value
            else:
                raw_summary = getattr(entry, "summary", "")

            summary = strip_links(raw_summary)

            full_text = title + " " + summary

            # только футбол
            if not is_football(full_text):
                continue

            news_id = make_id(title)

            # защита от повторов
            if news_id in sent_news:
                continue

            image = get_image(entry)

            # без картинки не публикуем
            if not image:
                continue

            # выбор стиля
            if is_transfer(full_text):
                text = romano_post(title, summary)
            else:
                text = media_post(title, summary)

            try:
                await bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image,
                    caption=text,
                    parse_mode="HTML"
                )

                sent_news.add(news_id)
                save_sent(news_id)

                posted += 1

                print(f"✔ Опубликовано: {title}")

            except Exception as e:
                print("Ошибка публикации:", e)

            # пауза между постами
            await asyncio.sleep(POST_DELAY)


# ================= MAIN =================
async def main():
    print("⚽ Football Radar PRO STARTED")

    while True:
        try:
            await check_news()

        except Exception as e:
            print("Ошибка цикла:", e)

        # проверка RSS каждую минуту
        await asyncio.sleep(60)


asyncio.run(main())