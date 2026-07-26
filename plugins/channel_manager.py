from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import Config, admin_filter # 👈 YAHAN admin_filter IMPORT KIYA HAI
import asyncio
import re

# ==================== 1. ADD CHANNEL COMMAND (Step-by-Step) ====================
@Client.on_message(filters.command("addchannel") & admin_filter) # 👈 YAHAN FILTER LAGA HAI
async def add_channel_step_by_step(client, message):
    chat = message.chat
    
    # 🔴 Red/Blue Buttons Format (Like Video)
    cancel_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="cancel_flow"),
         InlineKeyboardButton("❌ CLOSE", callback_data="cancel_flow")]
    ])

    try:
        # STEP 1: CHANNEL ID
        id_msg = await chat.ask(
            "✨ **Add a New Channel**\n\nPlease send the **Channel ID** (must be numeric, e.g., `-1001234567890`).\n\nSend /cancel to abort the process.",
            timeout=120
        )
        if id_msg.text.lower() == "/cancel":
            return await message.reply("🚫 **Action cancelled.**")
        ch_id = int(id_msg.text)

        # 🛡️ VERIFICATION STEP: Check if bot is an Admin in the channel (Peer ID Fix)
        try:
            verify_chat = await client.get_chat(ch_id)
        except Exception as e:
            return await message.reply(
                f"❌ **Error:** `Invalid Peer ID`\n\n"
                f"⚠️ **I cannot access this channel!**\n"
                f"Please make sure I am an **Admin** in the channel (`{ch_id}`) first, and then try adding it again.\n\n"
                f"**System Error:** `{e}`"
            )

        # STEP 2: TITLE
        fetched_title = verify_chat.title if verify_chat else "Unknown"
        title_msg = await chat.ask(
            f"📝 **Set Channel Title**\n\nPlease send a title for this channel (e.g., 'One Piece'):\n\n**ID:** `{ch_id}`\n**Fetched Title:** `{fetched_title}`",
            reply_markup=cancel_btn, timeout=120
        )
        if title_msg.text.lower() == "/cancel": return
        title = title_msg.text

        # STEP 3: GENRES (Replaced Description)
        genre_msg = await chat.ask(
            "🎭 **Set Channel Genres**\n\nSend the genres for this channel (e.g., Romance, Drama) or send `/skip`.\n\n*(Just type the names, no need to write 'Genres:')*",
            reply_markup=cancel_btn, timeout=120
        )
        if genre_msg.text.lower() == "/cancel": return
        
        desc = ""
        if genre_msg.text.lower() != "/skip":
            # Agar user ne galti se 'Genres: Drama' likha hai to automatically clean kar dega
            desc = re.sub(r"(?i)^genres?:\s*", "", genre_msg.text)

        # STEP 4: AUDIO
        audio_msg = await chat.ask(
            "🔊 **Set Audio Languages**\n\nSend the audio languages available (e.g., Hindi, English, Dual Audio) or send `/skip`.\n\n*(Just type the languages, no need to write 'Audio:')*",
            reply_markup=cancel_btn, timeout=120
        )
        if audio_msg.text.lower() == "/cancel": return
        
        audio = ""
        if audio_msg.text.lower() != "/skip":
            audio = re.sub(r"(?i)^audios?:\s*", "", audio_msg.text)

        # STEP 5: SUBTITLES
        sub_msg = await chat.ask(
            "📝 **Set Subtitles**\n\nSend the subtitle details (e.g., English, ESub, None) or send `/skip`.\n\n*(Just type the details, no need to write 'Subtitles:')*",
            reply_markup=cancel_btn, timeout=120
        )
        if sub_msg.text.lower() == "/cancel": return
        
        subtitles = ""
        if sub_msg.text.lower() != "/skip":
            subtitles = re.sub(r"(?i)^subtitles?:\s*", "", sub_msg.text)

        # 🚫 REMOVED POST MODE & AUTO-DELETE STEPS TO MATCH GLOBAL ADMIN SETTINGS

        # STEP 6: POSTER IMAGE
        poster_msg = await chat.ask(
            "🖼️ **Set Channel Poster**\n\nSend a cool poster image for this channel, or send `/skip` to bypass this step:",
            reply_markup=cancel_btn, timeout=120
        )
        
        poster_id = None
        if poster_msg.photo:
            poster_id = poster_msg.photo.file_id

        # SAVE FULL DATA TO MONGODB (Excluding mode and timer)
        channel_data = {
            "name": title,
            "description": desc,
            "audio": audio,
            "subtitles": subtitles,
            "poster_id": poster_id
        }
        await db.add_channel(ch_id, channel_data)

        # FINAL SUCCESS MESSAGE
        success_text = (
            "🎉 **Channel Successfully Added!**\n\n"
            f"🏷 **Title:** {title}\n"
            f"🆔 **ID:** `{ch_id}`\n"
            f"🎭 **Genres:** {desc if desc else 'Skipped'}\n"
            f"🔊 **Audio:** {audio if audio else 'Skipped'}\n"
            f"📝 **Subtitles:** {subtitles if subtitles else 'Skipped'}\n\n"
            "*(Note: Post Mode and Auto-Delete settings will be applied globally from the Admin Panel)*"
        )

        if poster_id:
            await message.reply_photo(photo=poster_id, caption=success_text)
        else:
            await message.reply_text(success_text)

    except asyncio.TimeoutError:
        await message.reply("⏰ **Time is up! The process has been reset. Please try again.**")
    except ValueError:
        await message.reply("❌ **Invalid ID provided! The Channel ID must be a numeric value.**")


# Button cancel handler for Add Channel flow
@Client.on_callback_query(filters.regex("cancel_flow"))
async def cancel_flow_handler(client, query):
    await query.message.edit_text("🚫 **Process safely closed by Admin.**")


# ==================== 2. DELETE CHANNEL COMMAND ====================
@Client.on_message(filters.command("delchannel") & admin_filter) # 👈 YAHAN FILTER LAGA HAI
async def del_channel(client, message):
    try:
        # Command se ID extract karega (e.g., /delchannel -100123456789)
        ch_id = int(message.text.split(" ")[1])
        await db.remove_channel(ch_id)
        await message.reply_text(f"> 🗑️ **Channel Removed Successfully:** `{ch_id}`")
    except IndexError:
        await message.reply_text("❌ **Invalid Format!**\n**Usage:** `/delchannel -100123456789`")
    except ValueError:
        await message.reply_text("❌ **Invalid ID!**\nThe Channel ID must contain only numbers.")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")
