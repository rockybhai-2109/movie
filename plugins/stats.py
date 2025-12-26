from pyrogram import Client, filters
from pyrogram.types import Message
import time
from info import ADMINS
from utils import get_readable_time
from database.users_chats_db import db
from database.ia_filterdb import Media

BOT_START_TIME = time.time()

@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def bot_stats(client: Client, message: Message):
    try:
        total_files = await Media.count_documents({})
        total_users = await db.total_users_count()
        total_chats = await db.total_chat_count()
        uptime = get_readable_time(time.time() - BOT_START_TIME)

        stats_text = (
            "╭───[ 🤖 **Bot Status** ]───╮\n"
            f"├ 📁 **Total Files :** `{total_files}`\n"
            f"├ 👥 **Users:** `{total_users}`\n"
            f"├ 💬 **Groups/Channels:** `{total_chats}`\n"
            f"├ ⏱️ **Uptime:** `{uptime}`\n"
            "╰──────────────────────────╯\n"
            "✨ Powered by @Real_Pirates 🏴‍☠️"
        )

        await message.reply_text(stats_text)

    except Exception as e:
        await message.reply_text(f"❌ Error fetching stats:\n`{e}`")
