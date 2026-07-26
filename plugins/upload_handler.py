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

# â±ï¸ Helper function
def parse_time(time_str):
    if not time_str or str(time_str).lower() in ["0", "off", "none"]: return 0
    time_str = str(time_str).lower()
    if time_str.endswith('s'): return int(time_str[:-1])
    if time_str.endswith('m'): return int(time_str[:-1]) * 60
    if time_str.endswith('h'): return int(time_str[:-1]) * 3600
    if time_str.endswith('d'): return int(time_str[:-1]) * 86400
    try: return int(time_str)
    except: return 0

# ðŸ”— Helper function
def format_url(url):
    if not url: return None
    url = str(url).strip()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("tg://")):
        return f"https://{url}"
    return url

# ðŸ” ð—¦ð—ºð—®ð—¿ð˜ ð—¥ð—²ð—´ð—²ð˜… - ð—˜ð—½ð—¶ð˜€ð—¼ð—±ð—² ð——ð—²ð˜ð—²ð—°ð˜ð—¶ð—¼ð—» (Strictly fixed to avoid 720p/1080p bugs)
EP_REGEX = r"(?i)(?:s\d{1,2})?[\s_.\-:]*(?:ep|episode|epi|e)[\s_.\-:]*(\d+)(?:(?:\s*[-~]\s*|\s+to\s+)(\d+))?"


# --- ðŸŸ¢ SMART FILE UPLOAD & AUTO-BATCH HANDLER ---

@Client.on_message((filters.document | filters.video) & admin_filter & filters.private)
async def handle_video_upload(client, message):
    user_id = message.from_user.id
    file_id = message.document.file_id if message.document else message.video.file_id
    caption = message.caption or "No Caption"

    # Agar user ne pehli baar file bheji hai, to nayi list banayenge
    if user_id not in pending_uploads:
        pending_uploads[user_id] = []

    # File ko queue me add karna
    pending_uploads[user_id].append({
        "file_id": file_id,
        "caption": caption,
        "msg_id": message.id,
        "chat_id": message.chat.id
    })

    files = pending_uploads[user_id]
    ep_numbers = []

    # Queue me jitni bhi files hain, sabke episode numbers check karna
    for f in files:
        match = re.search(EP_REGEX, f['caption'])
        if match:
            ep_numbers.append(int(match.group(1))) # First Ep Number
            if match.group(2): # If explicit range exists in filename
                ep_numbers.append(int(match.group(2)))

    # Smart Button Naming
    if ep_numbers:
        min_ep = min(ep_numbers)
        max_ep = max(ep_numbers)
        if min_ep == max_ep:
            btn_name = f"ðŸŽ¬ ð—˜ð—£ð—œð—¦ð—¢ð——ð—˜ {min_ep}"
        else:
            btn_name = f"ðŸŽ¬ ð—˜ð—£ð—œð—¦ð—¢ð——ð—˜ {min_ep} - {max_ep}"
    else:
        btn_name = f"ðŸ“¥ ð——ð—¼ð˜„ð—»ð—¹ð—¼ð—®ð—± {len(files)} ð—©ð—¶ð—±ð—²ð—¼ð˜€" if len(files) > 1 else "ðŸ“¥ ð——ð—¼ð˜„ð—»ð—¹ð—¼ð—®ð—± ð—©ð—¶ð—±ð—²ð—¼"

    text = (
        f"âœ… **File Added to Queue!**\n"
        f"**Total Files Pending:** `{len(files)}`\n"
        f"**Button Preview:** {btn_name}\n\n"
        f"ðŸ‘‰ *Send more videos to add them to this batch, or click the button below to post them now.*"
    )

    buttons = [
        [InlineKeyboardButton("ðŸš€ Post to Channel", callback_data="generate_post")],
        [InlineKeyboardButton("ðŸ—‘ Cancel Upload", callback_data="cancel_upload")]
    ]

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), quote=True)


# --- ðŸŸ¢ GENERATE LINK & SHOW CHANNELS ---

@Client.on_callback_query(filters.regex(r"^generate_post$"))
async def process_generate_post(client, query: CallbackQuery):
    user_id = query.from_user.id
    
    if user_id not in pending_uploads or not pending_uploads[user_id]:
        return await query.answer("âŒ No pending files found!", show_alert=True)
        
    files = pending_uploads[user_id]
    main_caption = files[0]['caption'] # Pehli video ka caption use hoga
    
    ep_numbers = []
    file_ids = []
    msg_ids = []
    
    # Final data preparation
    for f in files:
        file_ids.append(f['file_id'])
        msg_ids.append(f['msg_id'])
        match = re.search(EP_REGEX, f['caption'])
        if match:
            ep_numbers.append(int(match.group(1)))
            if match.group(2):
                ep_numbers.append(int(match.group(2)))
                
    # Final Button Name
    if ep_numbers:
        min_ep = min(ep_numbers)
        max_ep = max(ep_numbers)
        btn_name = f"ðŸŽ¬ ð—˜ð—£ð—œð—¦ð—¢ð——ð—˜ {min_ep}" if min_ep == max_ep else f"ðŸŽ¬ ð—˜ð—£ð—œð—¦ð—¢ð——ð—˜ {min_ep} - {max_ep}"
    else:
        btn_name = f"ðŸ“¥ ð——ð—¼ð˜„ð—»ð—¹ð—¼ð—®ð—± {len(files)} ð—©ð—¶ð—±ð—²ð—¼ð˜€" if len(files) > 1 else "ðŸ“¥ ð——ð—¼ð˜„ð—»ð—¹ð—¼ð—®ð—± ð—©ð—¶ð—±ð—²ð—¼"

    # Secure Hash aur Link generate karna
    file_hash = secrets.token_urlsafe(8)
    await db.save_file(json.dumps(file_ids), file_hash, main_caption)
    
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
    
    # Queue ko clear karna jab kaam ho jaye
    del pending_uploads[user_id]
    
    await query.message.delete()
    await send_channel_selection(query.message, file_hash, main_caption, btn_name)


@Client.on_callback_query(filters.regex(r"^cancel_upload$"))
async def cancel_upload_queue(client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id in pending_uploads:
        del pending_uploads[user_id]
    await query.message.edit("âŒ **Upload Cancelled. Queue cleared.**")


# Helper: Send Channel List
async def send_channel_selection(message, file_hash, caption, btn_name):
    channels = await db.get_channels()
    if not channels:
        return await message.reply_text("âŒ **No channels added yet.** Please add one using `/addchannel` first.")

    buttons = [[InlineKeyboardButton(ch.get('name', 'Channel'), callback_data=f"post:{file_hash}:{ch['_id']}")] for ch in channels]
    
    await message.reply_text(
        f"> ðŸ”— **ð—Ÿð—¶ð—»ð—¸ ð—šð—²ð—»ð—²ð—¿ð—®ð˜ð—²ð—± ð—¦ð˜‚ð—°ð—°ð—²ð˜€ð˜€ð—³ð˜‚ð—¹ð—¹ð˜†!**\n\n"
        f"**ð—™ð—¶ð—¹ð—²:** `{caption[:40]}...`\n"
        f"**ð—•ð˜‚ð˜ð˜ð—¼ð—» ð—¡ð—®ð—ºð—²:** {btn_name}\n\n"
        f"ðŸ‘‡ ð—¦ð—²ð—¹ð—²ð—°ð˜ ð—® ð—–ð—µð—®ð—»ð—»ð—²ð—¹ ð˜ð—¼ ð—½ð—¼ð˜€ð˜:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# --- ðŸŸ¢ FAST POSTING ---

@Client.on_callback_query(filters.regex(r"^post:"))
async def final_post_to_channel(client, query: CallbackQuery):
    data = query.data.split(":")
    file_hash = data[1]
    channel_id = int(data[2])
    
    p_data = post_data.get(file_hash)
    if not p_data:
        return await query.answer("âŒ Data expired! Please re-upload.", show_alert=True)
        
    await query.message.edit("> â³ **ð—£ð—¼ð˜€ð˜ð—¶ð—»ð—´ ð˜ð—¼ ð—–ð—µð—®ð—»ð—»ð—²ð—¹...**")
    
    channels = await db.get_channels()
    target_channel = next((ch for ch in channels if ch["_id"] == channel_id), None)
    
    if not target_channel:
        return await query.message.edit("âŒ **Channel not found in the Database!**")

    settings = await db.get_settings()
    post_mode = settings.get("post_mode", "Link").capitalize()
    auto_del_str = settings.get("auto_delete", "0")
    
    poster_id = target_channel.get("poster_id")
    description = target_channel.get("description", "")
    ch_title = target_channel.get("name", "")
    
    timer_seconds = parse_time(auto_del_str)
    sent_msg_ids = [] # Single or multiple post IDs
    
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
                await asyncio.sleep(1) # Batch copy rate-limit prevention
                
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
                btn_rows.append([InlineKeyboardButton("ðŸ’¬ ð—›ð—²ð—¹ð—½", url=f"https://t.me/{bot_username}")])
                
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
                
        await query.message.edit(f"> âœ… **ð—£ð—¼ð˜€ð˜ ð—¦ð˜‚ð—°ð—°ð—²ð˜€ð˜€ð—³ð˜‚ð—¹ð—¹ð˜† ð—¦ð—²ð—»ð˜!**\n\n**ð— ð—¼ð—±ð—²:** `{post_mode}`\n**ð—”ð˜‚ð˜ð—¼-ð——ð—²ð—¹ð—²ð˜ð—²:** `{auto_del_str}`")
        
    except Exception as e:
        return await query.message.edit(f"âŒ **Error While Posting:**\n`{e}`")

    # ðŸ—‘ï¸ Auto Delete Background Task
    if timer_seconds > 0:
        if sent_msg_ids:
            asyncio.create_task(delete_post_later(client, channel_id, sent_msg_ids, timer_seconds))
        
        asyncio.create_task(delete_post_later(client, p_data["chat_id"], p_data["msg_ids"], timer_seconds))
        asyncio.create_task(delete_post_later(client, query.message.chat.id, [query.message.id], timer_seconds))

# Background Helper Task (Supports both single ID and list of IDs)
async def delete_post_later(client, chat_id, msg_ids, delay):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id=chat_id, message_ids=msg_ids)
    except:
        pass
