from pyrogram import Client
from pyrogram.enums import ParseMode
from config import Config
import asyncio
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
        
        # 👇 KOYEB FIX:
        try:
            print("🔄 Caching channels to prevent PeerIdInvalid error on Koyeb...")
            async for dialog in self.get_dialogs():
                pass 
            print("✅ All channels successfully cached in memory!")
        except Exception as e:
            print(f"⚠️ Error while caching channels: {e}")

    async def stop(self, *args):
        await super().stop()
        print("❌ 𝗕𝗼𝘁 𝗦𝘁𝗼𝗽𝗽𝗲𝗱!")

if __name__ == "__main__":
    bot = PremiumBot()
    bot.run()
