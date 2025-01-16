from pyrogram import Client, filters
from pyrogram.types import Message
import time

# Bot konfiqurasiyası
bot_token = "7631661650:AAFyLxGS_2tTirwd8A1Jxn3QEi_FERqnREg"
API_ID = "28603118"
API_HASH = "35a400855835510c0a926f1e965aa12d"

# Botu yarat
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=bot_token)

# İstifadəçi məlumatlarını saxlamaq üçün bir lüğət
user_sessions = {}

@bot.on_message(filters.command(["start"]))
async def start(client, message: Message):
    await message.reply("Salam! Mənə API ID göndərin:")

@bot.on_message(filters.text & ~filters.command(["start"]))
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if user_id not in user_sessions:
        # İlk dəfə məlumat göndərir, API ID-ni saxla
        user_sessions[user_id] = {"step": "api_id", "api_id": text}
        await message.reply("API ID saxlanıldı! İndi API hash kodunu göndərin:")
    elif user_sessions[user_id]["step"] == "api_id":
        # API hash-ni saxla
        user_sessions[user_id]["api_hash"] = text
        user_sessions[user_id]["step"] = "api_hash"
        await message.reply("API hash saxlanıldı! İndi telefon nömrənizi göndərin:")
    elif user_sessions[user_id]["step"] == "api_hash":
        # Telefon nömrəsini saxla və doğrulama kodunu göndər
        user_sessions[user_id]["phone_number"] = text
        user_sessions[user_id]["step"] = "phone_number"

        # İstifadəçi üçün yeni Pyrogram müştərisini yarat
        user_client = Client(
            f"user_{user_id}",
            api_id=user_sessions[user_id]["api_id"],
            api_hash=user_sessions[user_id]["api_hash"]
        )

        await user_client.connect()
        try:
            response = await user_client.send_code(phone_number=user_sessions[user_id]["phone_number"])
            user_sessions[user_id]["phone_code_hash"] = response.phone_code_hash
            user_sessions[user_id]["code_sent_time"] = time.time()  # Kodun göndərilmə vaxtını saxla
            await message.reply("Doğrulama kodu göndərildi! Təsdiq kodunu göndərin:")
        except Exception as e:
            await message.reply(f"Doğrulama kodunu göndərmək mümkün olmadı: {e}")
        finally:
            await user_client.disconnect()
    elif user_sessions[user_id]["step"] == "phone_number":
        verification_code = text  # Kodu boşluqlardan təmizlə
        current_time = time.time()
        code_sent_time = user_sessions[user_id].get("code_sent_time")

        # Doğrulama kodunun süresi 2 dəqiqə (120 saniyə) olaraq təyin edilir
        if code_sent_time and current_time - code_sent_time > 120:
            await message.reply("Doğrulama kodunun müddəti bitmişdir. Yenidən başlaya bilərsiniz.")
            user_sessions.pop(user_id, None)  # İstifadəçi məlumatlarını sil
            return

        user_client = Client(
            f"user_{user_id}",
            api_id=user_sessions[user_id]["api_id"],
            api_hash=user_sessions[user_id]["api_hash"]
        )

        await user_client.connect()
        try:
            await user_client.sign_in(
                phone_number=user_sessions[user_id]["phone_number"],
                phone_code_hash=user_sessions[user_id]["phone_code_hash"],
                phone_code=verification_code  # Doğru parametr: phone_code
            )
            user_sessions[user_id]["verified"] = True
            user_sessions[user_id]["step"] = "verified"
            await message.reply("API məlumatlarınız təsdiq edildi! İndi qrupların ID-lərini göndərin:\nFormat: <source_chat_id> <target_chat_id>")
        except Exception as e:
            if "PHONE_CODE_EXPIRED" in str(e):
                await message.reply("Doğrulama kodunun müddəti bitmişdir. Yeni kod tələb edilir.")
                # Yenidən doğrulama kodu tələb et
                response = await user_client.send_code(phone_number=user_sessions[user_id]["phone_number"])
                user_sessions[user_id]["phone_code_hash"] = response.phone_code_hash
                user_sessions[user_id]["code_sent_time"] = time.time()  # Yeni kodun göndərilmə vaxtını saxla
                await message.reply("Yeni doğrulama kodu göndərildi! Təsdiq kodunu göndərin:")
            else:
                await message.reply(f"Doğrulama kodu səhvdir və ya istifadə müddəti bitmişdir: {e}")
        finally:
            await user_client.disconnect()
    elif user_sessions[user_id]["step"] == "verified":
        # Qrupların ID-lərini al və istifadəçiləri köçür
        args = text.split()
        if len(args) != 2:
            await message.reply("Zəhmət olmasa, qrupların ID-lərini düzgün formatda göndərin:\nFormat: <source_chat_id> <target_chat_id>")
            return

        source_chat_id = int(args[0])
        target_chat_id = int(args[1])

        user_client = Client(
            f"user_{user_id}",
            api_id=user_sessions[user_id]["api_id"],
            api_hash=user_sessions[user_id]["api_hash"]
        )

        await user_client.connect()
        try:
            async for member in user_client.iter_chat_members(source_chat_id):
                try:
                    await user_client.add_chat_members(target_chat_id, member.user.id)
                    await message.reply(f"İstifadəçi {member.user.id} uğurla köçürüldü!")
                except Exception as e:
                    await message.reply(f"İstifadəçi {member.user.id} köçürülə bilmədi: {e}")
        except Exception as e:
            await message.reply(f"Qrup üzvlərini əldə etmək mümkün olmadı: {e}")
        finally:
            await user_client.disconnect()

bot.run()
