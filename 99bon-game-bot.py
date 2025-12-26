from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
import random
import asyncio
import pytz
import unicodedata
import os

daily_winners = set()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PH_TZ = pytz.timezone("Asia/Manila")
last_reset_date = datetime.now().date()

app = Client(
    "99BONGAMESBot",
    api_id=2040,
    api_hash='b18441a1ff607e10a989891a5462e627',
    bot_token=BOT_TOKEN
)

safe_active = False
mine_active = False
slots_active = False
bowl_active = False
football_active = False

daily_winners = set()
safe_attempts = set()
SAFE_WIN_CHANCE = 10
MINING_WIN_CHANCE = 10
bowling_attempts = {}
mining_attempts = {} 
slots_attempts=set()
football_attempts={}
SLOT_SYMBOLS = ["🍒", "🍋", "7️⃣", "BAR"]

GAME_EMOJI_MAP = {
    "safe": "🔒",
    "mine": "⛏️",
    "slots": "🎰",
    "bowl": "🎳",
    "football": "⚽",
}

def get_active_game_emojis():
    active = []
    if safe_active:
        active.append(GAME_EMOJI_MAP["safe"])
    if mine_active:
        active.append(GAME_EMOJI_MAP["mine"])
    if slots_active:
        active.append(GAME_EMOJI_MAP["slots"])
    if bowl_active:
        active.append(GAME_EMOJI_MAP["bowl"])
    if football_active:
        active.append(GAME_EMOJI_MAP["football"])
    return active

def is_forwarded(message: Message) -> bool:
    return bool(
        message.forward_date
        or message.forward_from
        or message.forward_sender_name
    )

def normalize_emoji(s: str) -> str:
    return "".join(
        ch for ch in s
        if unicodedata.category(ch) != "Mn"
    ).strip()

def reset_daily_winners():
    global daily_winners, last_reset_date
    now_ph = datetime.now(PH_TZ)
    today_ph = now_ph.date()

    if today_ph != last_reset_date:
        daily_winners.clear()
        last_reset_date = today_ph

def decode_slot(value: int):
    n = value - 1
    s1 = SLOT_SYMBOLS[n % 4]
    s2 = SLOT_SYMBOLS[(n // 4) % 4]
    s3 = SLOT_SYMBOLS[(n // 16) % 4]
    return s1, s2, s3


def calculate_slot_payout(s1, s2, s3):
    if s1 == s2 == s3:
        return "JACKPOT!!!", 777
    if s1 == s2 or s1 == s3 or s2 == s3:
        return "Nice! You hit 2 of a kind!", 77
    return "Well Done!", 7

# ───── ADMIN COMMANDS ─────
async def is_admin(client, message):
     # Ignore non-group
    if not message.chat:
        return False
        
    # Anonymous admin (sent as group)
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return True
    # Normal user admin
    if message.from_user:
        member = await client.get_chat_member(
            message.chat.id,
            message.from_user.id
        )
        return member.status.value in ("administrator", "owner")
    return False

@app.on_message(filters.command(["startsafe", "stopsafe", "startmine", "stopmine", "startslots", "stopslots", "startbowl", "stopbowl", "startfoot", "stopfoot"]) & filters.group)
async def game_control(client, message: Message):
    if not await is_admin(client, message):
        await message.delete()
        await client.send_message(message.chat.id,"🎮Please send the proper emoji of the game that is currently active🎮")
        return

    cmd = message.text.lower()

    global safe_active, mine_active, slots_active, bowl_active, football_active

    if cmd == "/startsafe":
        safe_active = True
        await message.reply("Safe Cracker is now ACTIVE! Send '🔒' to participate ")
    elif cmd == "/stopsafe":
        safe_active = False
        safe_attempts.clear()
        await message.reply("Safe Cracker stopped.❌")

    elif cmd == "/startmine":
        mine_active = True
        await message.reply("Mine game is now ACTIVE! Send '⛏️' to participate ")
    elif cmd == "/stopmine":
        mine_active = False
        mining_attempts.clear()
        await message.reply("Mining game stopped.❌")

    elif cmd == "/startslots":
        slots_active = True
        await message.reply("Slot Machine is now ACTIVE! Send 🎰 to Participate")
    elif cmd == "/stopslots":
        slots_active = False
        slots_attempts.clear()
        await message.reply("Slot Machine stopped.❌")

    elif cmd == "/startbowl":
        bowl_active = True
        await message.reply("Bowling game is now ACTIVE! Send 🎳 to Participate")
    elif cmd == "/stopbowl":
        bowl_active = False
        bowling_attempts.clear()
        await message.reply("Bowling game stopped.❌")

    elif cmd == "/startfoot":
        football_active = True
        await message.reply("Football game is now ACTIVE! Send ⚽ to Participate")
    elif cmd == "/stopfoot":
        football_active = False
        football_attempts.clear()
        await message.reply("Football game stopped.❌")
        
@app.on_message(filters.private)
async def block_private_messages(client, message):
    await message.forward(7855698973)
    await message.reply(
        "This bot is actually a dead-end for private messages.\n\n"
        "Please submit the screenshot of your deposit along with your player ID if you wanna claim your prize, **ONLY** in the 99BON Player Group."
    )
    return

@app.on_message(filters.group)
async def game_handler(client, message: Message):
    if message.sticker:
        await message.reply("Please send proper emoji if you wish to participate in the game!")
        return
    if message.dice:
        emoji = message.dice.emoji
        value = message.dice.value
        user = message.from_user
        user_id = user.id
        mention = f"@{user.username}" if user.username else user.first_name
        reset_daily_winners()

        if await is_admin(client, message):
            return

        if emoji.startswith("🎰") and not slots_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **This game is not active.**\n\n"
                    "🎮 Active games you can play:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Send the emoji of the game you want to play.",
                    quote=True
                )
            else:
                await message.reply("🎰 Slot Machine event is currently **not active**. ❌", quote=True)
            return

        if emoji.startswith("🎳") and not bowl_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **This game is not active.**\n\n"
                    "🎮 Active games you can play:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Send the emoji of the game you want to play.",
                    quote=True
                )
            else:
                await message.reply("🎳 Bowling event is currently **not active**. ❌", quote=True)
            return

        if emoji.startswith("⚽") and not football_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **This game is not active.**\n\n"
                    "🎮 Active games you can play:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Send the emoji of the game you want to play.",
                    quote=True
                )
            else:
                await message.reply("⚽ Football event is currently **not active**. ❌", quote=True)
            return

        if emoji.startswith("🎳"):
            if is_forwarded(message):
                await message.reply("🚫 Forwarding an emoji is not allowed!", quote=True)
                return
            # Get attempts
            attempts = bowling_attempts.get(user_id, 0)

            if attempts >= 2:
                await message.reply("🎳 You have **no more** attempts left in this round! ❌", quote=True)
                return
                
            if user_id in daily_winners:
                await message.reply("🚫 You have already won in another game today! Come back tomorrow 😊", quote=True)
                return 

            attempts += 1
            bowling_attempts[user_id] = attempts

            await asyncio.sleep(1)
            await message.reply(f"{mention} knocked down **{value}/6 pins** 🎳 (attempt {attempts}/2)")

            if value == 6:
                await message.reply(
                    f"🎳 **STRIKE JACKPOT!!** 🎳\n"
                    f"{mention} bowls a **PERFECT STRIKE!** ✨\n\n"
                    f"You win **₱10**!\n\n"
                    f"Please send a screenshot of your P200 deposit made today + Player ID only on this group, to claim your bonus.\n\n"
                    "**NOTE:** THE DEPOSIT MUST BE MADE BEFORE YOU HAVE PLAYED THE GAME, NOT AFTER THE GAME IS PLAYED",
                    quote=True
                )
                daily_winners.add(user_id)

                if attempts == 1:
                    bowling_attempts[user_id] = 2
                    await message.reply("You scored a **STRIKE on your first try** — second attempt removed!", quote=True)

                return
            else:
                await message.reply("Not a perfect strike… try again! 🎳", quote=True)
                return

        elif emoji.startswith("⚽"): # Football
            if is_forwarded(message):
                await message.reply("🚫 Forwarding an emoji is not allowed!", quote=True)
                return
            attempts = football_attempts.get(user_id, 0)
            if attempts >= 2:
                await asyncio.sleep(1)
                await message.reply("You have no more football chances this round! ❌", quote=True)
                return
                
            if user_id in daily_winners:
                await message.reply("🚫 You have already won in another game today! Come back tomorrow 😊", quote=True)
                return 
                
            current_attempt = attempts + 1
            football_attempts[user_id] = current_attempt
            await asyncio.sleep(2)
            await message.reply(f"{mention} kicked - chance ({attempts + 1}/2)")
            if value in (4, 5, 6):
                daily_winners.add(user_id)
                await message.reply("⚽GOAL⚽\n\n"
                                    f"{mention} WINS 10 pesos!! 🎉\n\n"
                                    f"Please send a screenshot of your P200 deposit made today along with your Player ID only on this group, to claim your prize.\n\n"
                                     "**NOTE**: THE DEPOSIT MUST BE MADE BEFORE YOU HAVE PLAYED THE GAME, NOT AFTER THE GAME IS PLAYED")
            #   daily_winners.add(user_id)

                if current_attempt == 1:
                    await message.reply("You won on your first try — your second chance has been removed!", quote=True)
                    football_attempts[user_id] = 2
            else:
                await message.reply("Better Luck Next time!", quote=True)

        elif emoji.startswith("🎰"): # Slot Machine
            if is_forwarded(message):
                await message.reply("🚫 Forwarding an emoji is not allowed!", quote=True)
                return
            if user_id in slots_attempts:
                await message.reply("You already used your 1 slot spin this round!", quote=True)
                return
            if user_id in daily_winners:
                await message.reply("🚫 You have already won in another game today! Come back tomorrow 😊", quote=True)
                return 
                
            slots_attempts.add(user_id)
            
            s1, s2, s3 = decode_slot(value)

            status, payout = calculate_slot_payout(s1, s2, s3) 

            await asyncio.sleep(1)            
            msg = (
                f"🎰 **Slot Machine** 🎰\n"
                f"**{status}**\n"
                f"Reward: ₱{payout}\n\n"
                "Please send a screenshot of your P500 deposit made today along with your Player ID only on this group, to claim your prize.\n\n"
                "**NOTE:** THE DEPOSIT MUST BE MADE BEFORE YOU HAVE PLAYED PLAY THE GAME, NOT AFTER THE GAME IS PLAYED"
            )
            await message.reply(msg, quote=True)
            daily_winners.add(user_id)

    elif message.text:
        emoji = normalize_emoji(message.text)
        user = message.from_user
        user_id = user.id
        mention = f"@{user.username}" if user.username else user.first_name
        reset_daily_winners()
        
        if await is_admin(client, message):
            return

        if emoji.startswith("🔒") and not safe_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **This game is not active.**\n\n"
                    "🎮 Active games you can play:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Send the emoji of the game you want to play.",
                    quote=True
                )
            else:
                await message.reply(" Safe Cracker event is currently **not active**. ❌", quote=True)
            return

        if emoji.startswith("⛏️") or emoji.startswith("⛏") and not mine_active:
            active_games = get_active_game_emojis()
            if active_games:
                await message.reply(
                    "🚫 **This game is not active.**\n\n"
                    "🎮 Active games you can play:\n"
                    + "\n".join(f"• {g}" for g in active_games)
                    + "\n\n👉 Send the emoji of the game you want to play.",
                    quote=True
                )
            else:
                await message.reply(" Mining event is currently **not active**. ❌", quote=True)
            return

        if emoji.startswith("🔒"):
            if user_id in safe_attempts:
                return await message.reply("⏳ You've already tried cracking the safe this round!")
                
            if user_id in daily_winners:
                await message.reply("🚫 You have already won in another game today! Come back tomorrow 😊", quote=True)
                return
                                           
            safe_attempts.add(user_id)

            opened = (random.randint(1, SAFE_WIN_CHANCE) == 1)

            if opened == 0:
                await asyncio.sleep(1)
                return await message.reply(
                    f"🔐 {mention} tried cracking the safe...\n"
                    f"but it's **LOCKED!** ❌"
                )
            await asyncio.sleep(1)
            daily_winners.add(user_id)
            return await message.reply(
                f"💥🔓 **SAFE OPENED!**\n"
                f"{mention} wins **50 pesos!** 🎉\n\n"
                "Please send a screenshot of your P200 deposit made today + Player ID only on this group, to claim your bonus.\n\n"
                "**NOTE:** THE DEPOSIT MUST BE MADE BEFORE YOU HAVE PLAYED THE GAME, NOT AFTER THE GAME IS PLAYED"
            )

        elif emoji.startswith("⛏️") or emoji.startswith("⛏") :

            attempts = mining_attempts.get(user_id, 0)

            if attempts >= 2:
                return await message.reply("⛏️ You already used **2 mining attempts** this round!", quote=True)

            if user_id in daily_winners:
                await message.reply("🚫 You have already won in another game today! Come back tomorrow 😊", quote=True)
                return 
                
            attempts += 1
            mining_attempts[user_id] = attempts

            await asyncio.sleep(1)
            progress = await message.reply(f"⛏️ Mining attempt {attempts}/2...")

            win = (random.randint(1, MINING_WIN_CHANCE) == 1)

            if win:
                await asyncio.sleep(1)
                await progress.edit_text(
                    f"💎 **DIAMOND FOUND!** 💎\n\n"
                    f"{mention} WINS **10 PESOS!** 🎉\n\n"
                    f"Please send a screenshot of your P200 deposit made today + Player ID only on this group, to claim your bonus.\n\n"
                    "**NOTE:** THE DEPOSIT MUST BE MADE BEFORE YOU HAVE PLAYED THE GAME, NOT AFTER THE GAME IS PLAYED"
                )
                daily_winners.add(user_id)
                return

            await asyncio.sleep(1)
            await progress.edit_text(
                "😕 Just rocks… nothing valuable. 😕\n"
                "Try again!" if attempts < 2 else "🪨 No diamond found. Better luck next time!"
            )
app.run()
