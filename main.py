from aiogram import Bot
import asyncio
import feedparser
import os
import re
import hashlib
from difflib import SequenceMatcher

# ================= CONFIG =================

TOKEN = "8965358674:AAFxS_fde2c-EIltILySwB4rQmV1itTAUFA"
CHANNEL_ID = "@footballradar11"

RSS_FEEDS = [
    "https://www.championat.com/rss/news/football/",
    "https://www.soccer.ru/rss",
    "https://www.euro-football.ru/article/29/feed",
]

POST_DELAY = 1800
CHECK_DELAY = 60
MAX_POSTS_PER_RUN = 1

DEFAULT_IMAGE = "https://i.imgur.com/zYIlgBl.jpeg"

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

# ================= CLEAN =================

def strip_links(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"http\\S+", "", text)
    text = re.sub(r"www\\.\\S+", "", text)
    text = re.sub(r"\\s+", " ", text)

    return text.strip()

# ================= NORMALIZE =================

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"http\\S+", "", text)
    text = re.sub(r"[^a-zA-Zа-яА-Я0-9 ]", "", text)
    text = re.sub(r"\\s+", " ", text)
    return text.strip()

recent_titles = []

def is_duplicate(title):
    global recent_titles

    clean_title = normalize_text(title)

    for old in recent_titles:
        similarity = SequenceMatcher(None, clean_title, old).ratio()

        if similarity > 0.75:
            return True

    recent_titles.append(clean_title)
    recent_titles = recent_titles[-200:]

    return False

def make_id(title):
    return hashlib.md5(normalize_text(title).encode()).hexdigest()

# ================= FILTER =================

def is_football(text: str) -> bool:
    keywords = [
        "футбол",
        "матч",
        "гол",
        "лига",
        "uefa",
        "transfer",
        "goal",
        "league",
        "chelsea",
        "arsenal",
        "real madrid",
        "barcelona",
        "manchester"
    ]

    return any(k in text.lower() for k in keywords)

def is_transfer(text: str) -> bool:
    keywords = [
        "transfer",
        "signed",
        "loan",
        "deal",
        "контракт",
        "перешел",
        "трансфер"
    ]

    return any(k in text.lower() for k in keywords)

# ================= IMAGE =================

def get_image(entry):

    # media_content
    try:
        if "media_content" in entry:
            return entry.media_content[0]["url"]
    except:
        pass

    # media_thumbnail
    try:
        if "media_thumbnail" in entry:
            return entry.media_thumbnail[0]["url"]
    except:
        pass

    # enclosure
    try:
        if "links" in entry:
            for link in entry.links:
                if "image" in link.get("type", ""):
                    return link.href
    except:
        pass

    # from summary html
    try:
        summary = entry.summary
        img = re.search(r'<img.*?src="(.*?)"', summary)

        if img:
            return img.group(1)
    except:
        pass

    return DEFAULT_IMAGE

# ================= POSTS =================

def media_post(title, summary):

    summary = strip_links(summary)[:300]

    return f"""
⚽ BREAKING

<b>{title}</b>

📰 {summary}

🏟 Football Radar
"""

def romano_post(title, summary):

    summary = strip_links(summary)[:250]

    return f"""
🚨 TRANSFER UPDATE

<b>{title}</b>

📰 {summary}

🔥 Negotiations ongoing

🏟 Football Radar
"""

# ================= NEWS =================

async def check_news():

    posted = 0

    for url in RSS_FEEDS:

        print("CHECK:", url)

        feed = feedparser.parse(url)

        for entry in reversed(feed.entries[:20]):

            if posted >= MAX_POSTS_PER_RUN:
                return

            title = strip_links(entry.title)

            if is_duplicate(title):
                continue

            summary = strip_links(
                getattr(entry, "summary", "")
            )

            full_text = title + " " + summary

            if not is_football(full_text):
                continue

            news_id = make_id(title)

            if news_id in sent_news:
                continue

            image = get_image(entry)

            if is_transfer(full_text):
                text = romano_post(title, summary)
            else:
                text = media_post(title, summary)

            try:

                print("POST:", title)
                print("IMAGE:", image)

                await bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image,
                    caption=text,
                    parse_mode="HTML"
                )

                sent_news.add(news_id)
                save_sent(news_id)

                posted += 1

                print("SUCCESS")

            except Exception as e:

                print("ERROR:", e)

            await asyncio.sleep(POST_DELAY)

# ================= MAIN =================

async def main():

    print("⚽ BOT STARTED")

    while True:

        try:
            await check_news()

        except Exception as e:
            print("MAIN ERROR:", e)

        await asyncio.sleep(CHECK_DELAY)

asyncio.run(main())