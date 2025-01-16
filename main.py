from pyrogram import Client, filters, StringSession

# Bot konfiqurasiyası
bot_token = "7631661650:AAGE9KqXFZ8WDyEJncr8J14FALQtiwanzDk"
API_ID = "28603118"
API_HASH = "35a400855835510c0a926f1e965aa12d"

# Botu yarat
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=bot_token)

# İstifadəçi məlumatlarını saxlamaq üçün bir lüğət
user_sessions = {}

@bot.on_message(filters.command(["start"]))
async def start(client, message: Message):
    await message.reply("Salam! Mənə session string göndərin:")

@bot.on_message(filters.text & ~filters.command(["start"]))
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    session_string = message.text.strip()
    
    if user_id not in user_sessions:
        # İstifadəçinin sessiya stringini saxla və yeni müştərini yarat
        user_sessions[user_id] = {"session_string": session_string}
        try:
            user_client = Client(StringSession(session_string), api_id=API_ID, api_hash=API_HASH)
            await user_client.start()
            user_sessions[user_id]["client"] = user_client
            await message.reply("Sessiya string qəbul edildi və hesaba giriş edildi! İndi qrupların ID-lərini göndərin:\nFormat: <source_chat_id> <target_chat_id>")
        except Exception as e:
            await message.reply(f"Hesaba giriş uğursuz oldu: {e}")
    elif "client" in user_sessions[user_id]:
        user_client = user_sessions[user_id]["client"]
        args = message.text.split()
        
        if len(args) != 2:
            await message.reply("Zəhmət olmasa, qrupların ID-lərini düzgün formatda göndərin:\nFormat: <source_chat_id> <target_chat_id>")
            return
        
        source_chat_id = int(args[0])
        target_chat_id = int(args[1])
        
        try:
            async for member in user_client.iter_chat_members(source_chat_id):
                try:
                    await user_client.add_chat_members(target_chat_id, member.user.id)
                    await message.reply(f"İstifadəçi {member.user.id} uğurla köçürüldü!")
                except Exception as e:
                    await message.reply(f"İstifadəçi {member.user.id} köçürülə bilmədi: {e}")
        except Exception as e:
            await message.reply(f"Qrup üzvlərini əldə etmək mümkün olmadı: {e}")
    else:
        await message.reply("Sessiya stringi qəbul edildikdən sonra davam edin.")

bot.run()
