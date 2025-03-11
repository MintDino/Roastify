import os
import asyncio
import random
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor

# ✅ Load environment variables
TOKEN = os.getenv("BOT_TOKEN")  # Set this in Railway
DATABASE_URL = os.getenv("DATABASE_URL")  # PostgreSQL URL from Railway
ADMIN_USERNAME = "Mint_Dino"  # Hardcoded admin username

# ✅ Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ✅ Connect to PostgreSQL Database
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# ✅ Create tables if they don't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS leaderboard (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    roasts_received INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS roasts (
    id SERIAL PRIMARY KEY,
    level TEXT,
    text TEXT
)
""")

conn.commit()

# ✅ Predefined Roast categories
ROASTS = {
    "mild": [
        "You're like a cloud... when you disappear, it's a beautiful day!",
        "You're not stupid; you just have bad luck thinking."
    ],
    "medium": [
        "You're proof that even evolution takes a break sometimes.",
        "You bring everyone so much joy… when you leave the room."
    ],
    "savage": [
        "You have something on your chin… no, the third one down.",
        "You're like a penny: two-faced and not worth much."
    ],
    "nuclear": [
        "Your secrets are safe with me. I never even listen when you tell me them.",
        "You're the reason why shampoo bottles have instructions."
    ]
}

# ✅ Function to get a roast
def get_roast(level):
    cursor.execute("SELECT text FROM roasts WHERE level = %s", (level,))
    results = cursor.fetchall()
    if results:
        return random.choice(results)[0]
    return random.choice(ROASTS.get(level, ["No roasts available!"]))

# ✅ Function to update leaderboard
def update_leaderboard(user_id, username):
    cursor.execute("SELECT roasts_received FROM leaderboard WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    if result:
        cursor.execute("UPDATE leaderboard SET roasts_received = roasts_received + 1 WHERE user_id = %s", (user_id,))
    else:
        cursor.execute("INSERT INTO leaderboard (user_id, username, roasts_received) VALUES (%s, %s, 1)", (user_id, username))
    conn.commit()

# ✅ /roast command
@dp.message_handler(commands=['roast'])
async def roast_user(message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Usage: /roast @username level (mild, medium, savage, nuclear)")
        return

    user = args[1]
    level = args[2].lower()
    if level not in ROASTS:
        await message.reply("Invalid roast level! Choose from mild, medium, savage, or nuclear.")
        return

    roast = get_roast(level)
    update_leaderboard(message.from_user.id, message.from_user.username)
    await message.reply(f"🔥 {user}, {roast}")

# ✅ /leaderboard command
@dp.message_handler(commands=['leaderboard'])
async def show_leaderboard(message: Message):
    cursor.execute("SELECT username, roasts_received FROM leaderboard ORDER BY roasts_received DESC LIMIT 10")
    top_users = cursor.fetchall()
    if not top_users:
        await message.reply("No roasts recorded yet!")
        return
    
    leaderboard_text = "🔥 **Roastify Leaderboard** 🔥\n\n"
    for rank, (username, count) in enumerate(top_users, start=1):
        leaderboard_text += f"{rank}. @{username} - {count} roasts received\n"
    
    await message.reply(leaderboard_text, parse_mode="Markdown")

# ✅ /addroast command (Admin only)
@dp.message_handler(commands=['addroast'])
async def add_roast(message: Message):
    if message.from_user.username != ADMIN_USERNAME:
        return await message.reply("🚫 You are not authorized to use this command.")
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        return await message.reply("Usage: /addroast level roast_text")
    
    level, text = args[1], args[2]
    cursor.execute("INSERT INTO roasts (level, text) VALUES (%s, %s)", (level, text))
    conn.commit()
    await message.reply(f"✅ Roast added to {level} category!")

# ✅ /resetleaderboard command (Admin only)
@dp.message_handler(commands=['resetleaderboard'])
async def reset_leaderboard(message: Message):
    if message.from_user.username != ADMIN_USERNAME:
        return await message.reply("🚫 You are not authorized to use this command.")
    
    cursor.execute("DELETE FROM leaderboard")
    conn.commit()
    await message.reply("✅ Leaderboard has been reset!")

# ✅ Start bot
async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
    
