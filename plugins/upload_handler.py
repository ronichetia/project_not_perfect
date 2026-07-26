from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config, admin_filter
from database import db
import re
import secrets
import asyncio
import json

# Temporary dictionary for bot runtime
post_data = {} 
# Temporary storage for smart auto-batching
pending_uploads = {} 

# ⏱️ Helper function for parsing time
def parse_time(time_str):
    if not time_str or str(time_str).lower() in ["0", "off", "none"]: return 0
    time_str = str(time_str).lower()
    if time_str.endswith('s'): return int(time_str[:-1])
    if time_str.endswith('m'): return int(time_str[:-1]) * 60
    if time_str.endswith('h'): return int(time_str[:-1]) * 3600
    if time_str.endswith('d'): return int(time_str[:-1]) * 86400
    try: return int(time_str)
    except: return 0

# 🕰️ New Helper function: Converts 300 to "5 Minutes"
def get_readable_time(seconds):
    if seconds <= 0:
        return "Disabled"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    parts = []
    if h > 0: parts.append(f"{h} Hours")
    if m > 0: parts.append(f"{m} Minutes")
    if s > 0: parts.append(f"{s} Seconds")
    return " ".join(parts)

# 🔗 Helper function
def format_url(url):
    if not url: return None
    url = str(url).strip()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("tg://")):
        return f"https://{url}"
    return url

# 🔍 𝗦𝗺𝗮𝗿𝘁 𝗥𝗲𝗴𝗲𝘅 - 𝗘𝗽𝗶𝘀𝗼𝗱𝗲 𝗗𝗲𝘁𝗲𝗰𝘁𝗶𝗼𝗻
EP_REGEX = r"(?i)(?:s\d{1,2})?[\s_.\-:]*(?:ep|episode|epi|e)[\s_.\-:]*(\d+)(?:(?:\s*[-~]\s*|\s+to\s+)(\d+))?"


# --- 🟢 SMART FILE UPLOAD & AUTO-BATCH HANDLER ---

@Client.on_message((filters.document | filters.video) & admin_filter & filters.private)
async def handle_video_upload(client, message):
    user_id = message.from_user.id
    file_id = message.document.file_id if message.document else message.video.file_id
    caption = message.caption or "No Caption"

    if user_id not in pending_uploads:
        pending_uploads[user_id] = []

    pending_uploads[user_id].append({
        "file_id": file_id,
        "caption": caption,
        "msg_id": message.id,
        "chat_id": message.chat.id
    })

    files = pending_uploads[user_id]
    ep_numbers = []

    for f in files:
        match = re.search(EP_REGEX, f['caption'])
        if match:
            ep_numbers.append(int(match.group(1)))
            if match.group(2): 
                ep_numbers.append(int(match.group(2)))

    if ep_numbers:
        min_ep = min(ep_numbers)
        max_ep = max(ep_numbers)
        if min_ep == max_ep:
            btn_name = f"🎬 𝗘𝗣𝗜𝗦𝗢𝗗𝗘 {min_ep}"
        else:
            btn_name = f"🎬 𝗘𝗣𝗜𝗦𝗢𝗗𝗘 {min_ep} - {max_ep}"
    else:
        btn_name = f"📥 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 {len(files)} 𝗩𝗶𝗱𝗲𝗼𝘀" if len(files) > 1 else "📥 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗩𝗶𝗱𝗲𝗼"

    text = (
        f"✅ **File Added to Queue!**\n"
        f"**Total Files Pending:** `{len(files)}`\n"
        f"**Button Preview:** {btn_name}\n\n"
        f"👉 *Send more videos to add them to this batch, or click the button below to post them now.*"
    )

    buttons = [
        [InlineKeyboardButton("🚀 Post to Channel", callback_data="generate_post")],
        [InlineKeyboardButton("🗑 Cancel Upload", callback_data="cancel_upload")]
    ]

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), quote=True)


# --- 🟢 GENERATE LINK & SHOW CHANNELS ---

@Client.on_callback_query(filters.regex(r"^generate_post$"))
async def process_generate_post(client, query: CallbackQuery):
    user_id = query.from_user.id
    
    if user_id not in pending_uploads or not pending_uploads[user_id]:
        return await query.answer("❌ No pending files found!", show_alert=True)
        
    files = pending_uploads[user_id]
    main_caption = files[0]['caption'] 
    
    ep_numbers = []
    file_data = [] # 👈 FIX: Ab sirf ID nahi, caption bhi store hoga
    msg_ids = []
    
    for f in files:
        # Ab JSON me dono cheezein list of dictionaries ban kar save hongi
        file_data.append({"file_id": f['file_id'], "caption": f['caption']})
        msg_ids.append(f['msg_id'])
        
        match = re.search(EP_REGEX, f['caption'])
        if match:
            ep_numbers.append(int(match.group(1)))
            if match.group(2):
                ep_numbers.append(int(match.group(2)))
                
    if ep_numbers:
        min_ep = min(ep_numbers)
        max_ep = max(ep_numbers)
        btn_name = f"🎬 𝗘𝗣𝗜𝗦𝗢𝗗𝗘 {min_ep}" if min_ep == max_ep else f"🎬 𝗘𝗣𝗜𝗦𝗢𝗗𝗘 {min_ep} - {max_ep}"
    else:
        btn_name = f"📥 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 {len(files)} 𝗩𝗶𝗱𝗲𝗼𝘀" if len(files) > 1 else "📥 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗩𝗶𝗱𝗲𝗼"

    file_hash = secrets.token_urlsafe(8)
    # Database me JSON ab naye format me jayega
    await db.save_file(json.dumps(file_data), file_hash, main_caption)
    
    bot_info = await client.get_me()
    start_link = f"https://t.me/{bot_info.username}?start={file_hash}"
    
    post_data[file_hash] = {
        "caption": main_caption,
        "btn_name": btn_name,
        "start_link": start_link,
        "msg_ids": msg_ids,       
        "chat_id": files[0]['chat_id'],
        "is_batch": len(files) > 1
    }
    
    del pending_uploads[user_id]
    
    await query.message.delete()
    await send_channel_selection(query.message, file_hash, main_caption, btn_name)


@Client.on_callback_query(filters.regex(r"^cancel_upload$"))
async def cancel_upload_queue(client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id in pending_uploads:
        del pending_uploads[user_id]
    await query.message.edit("❌ **Upload Cancelled. Queue cleared.**")


# Helper: Send Channel List
async def send_channel_selection(message, file_hash, caption, btn_name):
    channels = await db.get_channels()
    if not channels:
        return await message.reply_text("❌ **No channels added yet.** Please add one using `/addchannel` first.")

    buttons = [[InlineKeyboardButton(ch.get('name', 'Channel'), callback_data=f"post:{file_hash}:{ch['_id']}")] for ch in channels]
    
    await message.reply_text(
        f"> 🔗 **𝗟𝗶𝗻𝗸 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆!**\n\n"
        f"**𝗙𝗶𝗹𝗲:** `{caption[:40]}...`\n"
        f"**𝗕𝘂𝘁𝘁𝗼𝗻 𝗡𝗮𝗺𝗲:** {btn_name}\n\n"
        f"👇 𝗦𝗲𝗹𝗲𝗰𝘁 𝗮 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝘁𝗼 𝗽𝗼𝘀𝘁:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# --- 🟢 FAST POSTING ---

@Client.on_callback_query(filters.regex(r"^post:"))
async def final_post_to_channel(client, query: CallbackQuery):
    data = query.data.split(":")
    file_hash = data[1]
    channel_id = int(data[2])
    
    p_data = post_data.get(file_hash)
    if not p_data:
        return await query.answer("❌ Data expired! Please re-upload.", show_alert=True)
        
    await query.message.edit("> ⏳ **𝗣𝗼𝘀𝘁𝗶𝗻𝗴 𝘁𝗼 𝗖𝗵𝗮𝗻𝗻𝗲𝗹...**")
    
    channels = await db.get_channels()
    target_channel = next((ch for ch in channels if ch["_id"] == channel_id), None)
    
    if not target_channel:
        return await query.message.edit("❌ **Channel not found in the Database!**")

    settings = await db.get_settings()
    post_mode = settings.get("post_mode", "Link").capitalize()
    auto_del_str = settings.get("auto_delete", "0")
    
    poster_id = target_channel.get("poster_id")
    description = target_channel.get("description", "")
    ch_title = target_channel.get("name", "")
    
    timer_seconds = parse_time(auto_del_str)
    display_time = get_readable_time(timer_seconds) # 👈 FIX: Seconds converted to text
    sent_msg_ids = []
    
    try:
        if post_mode == "Forward":
            sent_msgs = await client.forward_messages(
                chat_id=channel_id,
                from_chat_id=p_data["chat_id"],
                message_ids=p_data["msg_ids"]
            )
            if not isinstance(sent_msgs, list):
                sent_msgs = [sent_msgs]
            sent_msg_ids = [m.id for m in sent_msgs]
            
        elif post_mode == "Copy":
            for mid in p_data["msg_ids"]:
                msg = await client.copy_message(
                    chat_id=channel_id,
                    from_chat_id=p_data["chat_id"],
                    message_id=mid
                )
                sent_msg_ids.append(msg.id)
                await asyncio.sleep(1) 
                
        else: # Link Mode
            btn_rows = [[InlineKeyboardButton(p_data["btn_name"], url=format_url(p_data["start_link"]))]]
            post_buttons = settings.get("post_buttons", [])
            
            if post_buttons:
                current_row = []
                for btn in post_buttons:
                    valid_url = format_url(btn.get("url", ""))
                    if valid_url: current_row.append(InlineKeyboardButton(btn["name"], url=valid_url))
                    if len(current_row) == 2:  
                        btn_rows.append(current_row)
                        current_row = []
                if current_row: btn_rows.append(current_row)
            else:
                bot_username = (await client.get_me()).username
                btn_rows.append([InlineKeyboardButton("💬 𝗛𝗲𝗹𝗽", url=f"https://t.me/{bot_username}")])
                
            keyboard = InlineKeyboardMarkup(btn_rows)
            post_text = f"**{ch_title}**\n\n" if ch_title else f"**{p_data['caption']}**\n\n"
            
            if description and description.lower() != "skipped":
                clean_genres = re.sub(r"(?i)^genres?:\s*", "", description)
                post_text += f"**Genres:** {clean_genres}"
                
            if poster_id:
                msg = await client.send_photo(channel_id, photo=poster_id, caption=post_text, reply_markup=keyboard)
            else:
                msg = await client.send_message(channel_id, text=post_text, reply_markup=keyboard)
            
            sent_msg_ids = [msg.id]
                
        # 👈 FIX: Ab '300' ki jagah '5 Minutes' show hoga
        await query.message.edit(f"> ✅ **𝗣𝗼𝘀𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗦𝗲𝗻𝘁!**\n\n**𝗠𝗼𝗱𝗲:** `{post_mode}`\n**𝗔𝘂𝘁𝗼-𝗗𝗲𝗹𝗲𝘁𝗲:** `{display_time}`")
        
    except Exception as e:
        return await query.message.edit(f"❌ **Error While Posting:**\n`{e}`")

    if timer_seconds > 0:
        if sent_msg_ids:
            asyncio.create_task(delete_post_later(client, channel_id, sent_msg_ids, timer_seconds))
        
        asyncio.create_task(delete_post_later(client, p_data["chat_id"], p_data["msg_ids"], timer_seconds))
        asyncio.create_task(delete_post_later(client, query.message.chat.id, [query.message.id], timer_seconds))

async def delete_post_later(client, chat_id, msg_ids, delay):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id=chat_id, message_ids=msg_ids)
    except:
        pass
