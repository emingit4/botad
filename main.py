from pyrogram import Client, filters
from pyrogram.types import Message

# Bot konfiqurasiyası
bot_token = "7631661650:AAGE9KqXFZ8WDyEJncr8J14FALQtiwanzDk"
API_ID = "28603118"
API_HASH = "35a400855835510c0a926f1e965aa12d"

# Botu yarat
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=bot_token)

# İstifadəçi sessiya məlumatlarını saxlamaq üçün bir lüğət
user_sessions = {}

@bot.on_message(filters.command(["start"]))
async def start(client, message: Message):
    await message.reply("Salam! Mənə session string göndərin:")

@bot.on_message(filters.text & ~filters.command(["start"]))
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    session_string = message.text.strip()

    if user_id not in user_sessions:
        # İstifadəçi üçün müvəqqəti sessiya saxla
        user_sessions[user_id] = {"session_string": session_string}
        try:
            # Müvəqqəti sessiya yarat
            user_client = Client(
                name=f"user_{user_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session_string
            )
            await user_client.start()
            user_sessions[user_id]["client"] = user_client
            await message.reply("Sessiya qəbul edildi və hesaba giriş edildi! İndi daşınacaq qrupun ID-sini göndərin:")
        except Exception as e:
            await message.reply(f"Hesaba giriş uğursuz oldu: {e}")
    elif "client" not in user_sessions[user_id]:
        await message.reply("Zəhmət olmasa, ilk öncə sessiya stringini düzgün formatda göndərin.")
    elif "source_chat_id" not in user_sessions[user_id]:
        try:
            source_chat_id = int(session_string)
            user_sessions[user_id]["source_chat_id"] = source_chat_id
            await message.reply("Daşınacaq qrup qəbul edildi! İndi istifadəçilərin əlavə ediləcəyi qrupun ID-sini göndərin:")
        except ValueError:
            await message.reply("Zəhmət olmasa, düzgün qrup ID-sini göndərin.")
    else:
        try:
            target_chat_id = int(session_string)
            user_sessions[user_id]["target_chat_id"] = target_chat_id
            user_client = user_sessions[user_id]["client"]
            source_chat_id = user_sessions[user_id]["source_chat_id"]
            added_users = []
            failed_users = []

            async for member in user_client.get_chat_members(source_chat_id):
                try:
                    await user_client.add_chat_members(target_chat_id, member.user.id)
                    added_users.append(member.user.id)
                except Exception as e:
                    failed_users.append((member.user.id, str(e)))

            result_message = f"İstifadəçilərin əlavə edilməsi tamamlandı!\n\nUğurla əlavə olunan istifadəçilər:\n{', '.join(map(str, added_users))}\n\nUğursuz olan istifadəçilər:\n"
            result_message += "\n".join([f"{user_id}: {reason}" for user_id, reason in failed_users])

            await message.reply(result_message)
        except ValueError:
            await message.reply("Zəhmət olmasa, düzgün qrup ID-sini göndərin.")

bot.run()
