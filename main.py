from pyrogram import Client
from pyrogram.enums import ParseMode
from config import Config
import asyncio
import pyromod # ✅ ADDED FOR STEP-BY-STEP CONVERSATION
from flask import Flask
from threading import Thread

# ==========================================
# Koyeb Health Check Pass Karne Ke Liye Web Server
# ==========================================
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive and running!"

def run_server():
    app.run(host="0.0.0.0", port=8000)
# ==========================================


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

    async def stop(self, *args):
        await super().stop()
        print("❌ 𝗕𝗼𝘁 𝗦𝘁𝗼𝗽𝗽𝗲𝗱!")

if __name__ == "__main__":
    # Bot start hone se pehle dummy server ko alag thread me start karein
    Thread(target=run_server, daemon=True).start()
    
    bot = PremiumBot()
    bot.run()
