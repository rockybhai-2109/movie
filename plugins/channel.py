from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from info import CHANNELS, MOVIE_UPDATE_CHANNEL, ADMINS
from database.ia_filterdb import save_file, unpack_new_file_id
from utils import get_poster, temp, formate_file_name
from Script import script
from database.users_chats_db import db

import asyncio
import re

processed_movies = set()
media_filter = filters.document | filters.video


@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    media = getattr(message, message.media.value, None)
    if media and media.mime_type in ['video/mp4', 'video/x-matroska']:
        media.file_type = message.media.value
        media.caption = message.caption

        success_sts = await save_file(media)
        post_mode = await db.update_post_mode_handle()

        file_id, file_ref = unpack_new_file_id(media.file_id)

        if post_mode.get('all_files_post_mode', False) or success_sts == 'suc':
            await send_movie_updates(bot, file_name=media.file_name, file_id=file_id, post_mode=post_mode)


def name_format(file_name: str):
    file_name = file_name.lower()
    file_name = re.sub(r'http\S+', '', re.sub(r'@\w+|#\w+', '', file_name).replace('_', ' ').replace('[', '').replace(']', '')).strip()
    file_name = re.split(r's\d+|season\s*\d+|chapter\s*\d+', file_name, flags=re.IGNORECASE)[0]
    file_name = file_name.strip()
    words = file_name.split()[:7]
    imdb_file_name = ' '.join(words)
    return imdb_file_name


async def get_imdb(file_name, post_mode):
    def smart_clean_filename(file_name: str) -> str:
        file_name = file_name.lower()
        file_name = re.sub(r'\b(\d{3,4}p|x264|x265|hevc|aac|esub|hdrip|bluray|webrip|web-dl|hindi|english|dual audio|multi audio|uncut)\b', '', file_name)
        file_name = re.sub(r'http\S+|@\w+|#\w+', '', file_name)
        file_name = re.sub(r'\[.*?\]|\(.*?\)|_', ' ', file_name)
        file_name = re.sub(r'\b(movies4u|mlwbd|filmyzilla|hdhub4u|mkvcinemas|katmoviehd|movieverse|extramovies|amzn|netflix|hotstar|primevideo|disney|pbx|×|ᏚᎧƝU|𓆩)\b', '', file_name)
        file_name = re.split(r's\d+|season\s*\d+|chapter\s*\d+|ep\s*\d+|episode\s*\d+', file_name, flags=re.IGNORECASE)[0]
        file_name = re.sub(r'[^a-zA-Z0-9\s]', ' ', file_name)
        file_name = re.sub(r'\s+', ' ', file_name).strip()
        return file_name

    imdb_file_name = smart_clean_filename(file_name)
    words = imdb_file_name.split()
    search_queries = [' '.join(words[:3]), ' '.join(words[:5]), ' '.join(words[:7])]
    tried = []

    file_caption = f'File Name : <code>{formate_file_name(file_name)}</code>' if post_mode.get('single_post_mode', True) else ''

    for query in search_queries:
        if not query or query in tried:
            continue
        tried.append(query)

        imdb = await get_poster(query)
        if imdb:
            genres = imdb.get("genres", "")
            genre_emoji_map = {
                "Action": "💥", "Adventure": "🗺", "Comedy": "😂", "Crime": "🕵️",
                "Drama": "🎭", "Fantasy": "🧚", "Horror": "👻", "Romance": "❤️",
                "Sci-Fi": "👽", "Thriller": "🔪", "Mystery": "🧩", "Animation": "🎨"
            }

            genre_tags = []
            if isinstance(genres, str):
                genres = genres.split(",")
            for genre in genres:
                genre_clean = genre.strip().lower().replace(" ", "")
                emoji = genre_emoji_map.get(genre.strip(), "🎬")
                genre_tags.append(f"{emoji} #{genre_clean}")

            formatted_genres = ' '.join(genre_tags)

            caption = script.MOVIES_UPDATE_TXT.format(
                title=imdb.get("title"),
                rating=imdb.get("rating", "N/A"),
                genres=formatted_genres,
                description=imdb.get("plot", "No description available."),
                file_name=file_caption
            )

            if len(caption) > 1024:
                trimmed_plot = imdb.get("plot", "")[:300] + "..." if imdb.get("plot") else ""
                caption = script.MOVIES_UPDATE_TXT.format(
                    title=imdb.get("title"),
                    rating=imdb.get("rating", "N/A"),
                    genres=formatted_genres,
                    description=trimmed_plot,
                    file_name=file_caption
                )

            return imdb.get("title"), imdb.get("poster"), caption

    fallback_caption = f"🎬 <b>Unknown Movie</b>\n{file_caption}"
    return None, None, fallback_caption


async def send_movie_updates(bot, file_name, file_id, post_mode):
    imdb_title, poster_url, caption = await get_imdb(file_name, post_mode)

    if not post_mode.get('single_post_mode', False):
        if imdb_title in processed_movies:
            return
        processed_movies.add(imdb_title)

    if not poster_url or not caption:
        return

    buttons = [
        [
            InlineKeyboardButton('💎 𝐃𝐫𝐚𝐦𝐚 𝐋𝐨𝐯𝐞𝐫𝐬', url='https://t.me/+A81WyiBw-ExmMjBl'),
            InlineKeyboardButton('💎 𝐌𝐨𝐯𝐢𝐞 𝐏𝐢𝐫𝐚𝐭𝐞𝐬', url='https://t.me/+02e7v00GQ4o2MDA1')
        ],
        [
            InlineKeyboardButton("🪄 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐇𝐞𝐫𝐞 🏴‍☠️", url='https://t.me/+sIUXVrqvpwA2ODU1')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    movie_update_channel = await db.movies_update_channel_id()
    channels_to_post = [movie_update_channel] if movie_update_channel else MOVIE_UPDATE_CHANNEL

    if len(caption) > 1024:
        caption = caption[:1020] + "..."

    tasks = []
    for channel_id in channels_to_post:
        tasks.append(
            bot.send_photo(
                chat_id=int(channel_id),
                photo=poster_url,
                caption=caption,
                reply_markup=reply_markup,
                has_spoiler=True
            )
        )

    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        print('Error in send_movie_updates:', e)
