from pyrogram import Client
from pyrogram.enums import ParseMode
from config import Config
from database import db
from aiohttp import web
import asyncio
import os
import pyromod # ✅ ADDED FOR STEP-BY-STEP CONVERSATION

class PremiumBot(Client):
    def __init__(self):
        super().__init__(
            "PremiumAutoPoster",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins"), # Plug & Play Folder
            parse_mode=ParseMode.MARKDOWN
        )

    async def start(self):
        await super().start()
        print("✅ 𝗕𝗼𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗦𝘁𝗮𝗿𝘁𝗲𝗱 & 𝗣𝗹𝘂𝗴𝗶𝗻𝘀 𝗟𝗼𝗮𝗱𝗲𝗱!")
        
        # ==========================================
        # 1️⃣ KOYEB HEALTH CHECK FIX (Dummy Web Server)
        # ==========================================
        try:
            app = web.Application()
            app.router.add_get('/', lambda r: web.Response(text="Bot is running properly!"))
            runner = web.AppRunner(app)
            await runner.setup()
            # Koyeb default port 8000 bhejta hai, hum wahi use karenge
            port = int(os.environ.get("PORT", 8000)) 
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            print(f"🌐 Dummy web server started on port {port} to pass Koyeb Health Checks!")
        except Exception as e:
            print(f"⚠️ Web server error: {e}")

        # ==========================================
        # 2️⃣ PEER ID INVALID FIX (DB se Cache karna)
        # ==========================================
        try:
            print("🔄 Caching channels from Database to prevent PeerIdInvalid...")
            channels = await db.get_channels()
            if channels:
                for ch in channels:
                    try:
                        # Ye bot ko allow hai aur channel cache kar dega
                        await self.get_chat(ch["_id"]) 
                        print(f"✅ Cached Channel: {ch['_id']}")
                    except Exception as e:
                        print(f"⚠️ Could not cache {ch['_id']} (Admin privileges might be missing): {e}")
            print("✅ Channels caching process finished!")
        except Exception as e:
            print(f"⚠️ Error accessing database for caching: {e}")

    async def stop(self, *args):
        await super().stop()
        print("❌ 𝗕𝗼𝘁 𝗦𝘁𝗼𝗽𝗽𝗲𝗱!")

if __name__ == "__main__":
    bot = PremiumBot()
    bot.run()

