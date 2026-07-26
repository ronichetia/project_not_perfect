from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from config import Config, admin_filter # ðŸ‘ˆ YAHAN admin_filter IMPORT KIYA HAI
import asyncio
import re

# ==================== 1. ADD CHANNEL COMMAND (Step-by-Step) ====================
@Client.on_message(filters.command("addchannel") & admin_filter) # ðŸ‘ˆ YAHAN FILTER LAGA HAI
async def add_channel_step_by_step(client, message):
    chat = message.chat
    
    # ðŸ”´ Red/Blue Buttons Format (Like Video)
    cancel_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("ðŸ”™ BACK", callback_data="cancel_flow"),
         InlineKeyboardButton("âŒ CLOSE", callback_data="cancel_flow")]
    ])

    try:
        # STEP 1: CHANNEL ID
        id_msg = await chat.ask(
            "âœ¨ **Add a New Channel**\n\nPlease send the **Channel ID** (must be numeric, e.g., `-1001234567890`).\n\nSend /cancel to abort the process.",
            timeout=120
        )
        if id_msg.text.lower() == "/cancel":
            return await message.reply("ðŸš« **Action cancelled.**")
        ch_id = int(id_msg.text)

        # ðŸ›¡ï¸ VERIFICATION STEP: Check if bot is an Admin in the channel (Peer ID Fix)
        try:
            verify_chat = await client.get_chat(ch_id)
        except Exception as e:
            return await message.reply(
                f"âŒ **Error:** `Invalid Peer ID`\n\n"
                f"âš ï¸ **I cannot access this channel!**\n"
                f"Please make sure I am an **Admin** in the channel (`{ch_id}`) first, and then try adding it again.\n\n"
                f"**System Error:** `{e}`"
            )

        # STEP 2: TITLE
        fetched_title = verify_chat.title if verify_chat else "Unknown"
        title_msg = await chat.ask(
            f"ðŸ“ **Set Channel Title**\n\nPlease send a title for this channel (e.g., 'One Piece'):\n\n**ID:** `{ch_id}`\n**Fetched Title:** `{fetched_title}`",
            reply_markup=cancel_btn, timeout=120
        )
        if title_msg.text.lower() == "/cancel": return
        title = title_msg.text

        # STEP 3: GENRES (Replaced Description)
        genre_msg = await chat.ask(
            "ðŸŽ­ **Set Channel Genres**\n\nSend the genres for this channel (e.g., Romance, Drama) or send `/skip`.\n\n*(Just type the names, no need to write 'Genres:')*",
            reply_markup=cancel_btn, timeout=120
        )
        if genre_msg.text.lower() == "/cancel": return
        
        desc = ""
        if genre_msg.text.lower() != "/skip":
            # Agar user ne galti se 'Genres: Drama' likha hai to automatically clean kar dega
            desc = re.sub(r"(?i)^genres?:\s*", "", genre_msg.text)

        # ðŸš« REMOVED POST MODE & AUTO-DELETE STEPS TO MATCH GLOBAL ADMIN SETTINGS

        # STEP 4: POSTER IMAGE
        poster_msg = await chat.ask(
            "ðŸ–¼ï¸ **Set Channel Poster**\n\nSend a cool poster image for this channel, or send `/skip` to bypass this step:",
            reply_markup=cancel_btn, timeout=120
        )
        
        poster_id = None
        if poster_msg.photo:
            poster_id = poster_msg.photo.file_id

        # SAVE FULL DATA TO MONGODB (Excluding mode and timer)
        channel_data = {
            "name": title,
            "description": desc,
            "poster_id": poster_id
        }
        await db.add_channel(ch_id, channel_data)

        # FINAL SUCCESS MESSAGE (Video Format)
        success_text = (
            "ðŸŽ‰ **Channel Successfully Added!**\n\n"
            f"ðŸ· **Title:** {title}\n"
            f"ðŸ†” **ID:** `{ch_id}`\n"
            f"ðŸŽ­ **Genres:** {desc if desc else 'Skipped'}\n\n"
            "*(Note: Post Mode and Auto-Delete settings will be applied globally from the Admin Panel)*"
        )

        if poster_id:
            await message.reply_photo(photo=poster_id, caption=success_text)
        else:
            await message.reply_text(success_text)

    except asyncio.TimeoutError:
        await message.reply("â° **Time is up! The process has been reset. Please try again.**")
    except ValueError:
        await message.reply("âŒ **Invalid ID provided! The Channel ID must be a numeric value.**")


# Button cancel handler for Add Channel flow
@Client.on_callback_query(filters.regex("cancel_flow"))
async def cancel_flow_handler(client, query):
    await query.message.edit_text("ðŸš« **Process safely closed by Admin.**")


# ==================== 2. DELETE CHANNEL COMMAND ====================
@Client.on_message(filters.command("delchannel") & admin_filter) # ðŸ‘ˆ YAHAN FILTER LAGA HAI
async def del_channel(client, message):
    try:
        # Command se ID extract karega (e.g., /delchannel -100123456789)
        ch_id = int(message.text.split(" ")[1])
        await db.remove_channel(ch_id)
        await message.reply_text(f"> ðŸ—‘ï¸ **Channel Removed Successfully:** `{ch_id}`")
    except IndexError:
        await message.reply_text("âŒ **Invalid Format!**\n**Usage:** `/delchannel -100123456789`")
    except ValueError:
        await message.reply_text("âŒ **Invalid ID!**\nThe Channel ID must contain only numbers.")
    except Exception as e:
        await message.reply_text(f"âŒ **Error:** `{e}`")
