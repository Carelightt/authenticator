import base64
import urllib.parse
import pyotp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters

TELEGRAM_BOT_TOKEN = "7843763370:AAFngUVUd4oroByEotWcVyh_xQKvVI-t5Ng"
MIGRATION_URI = "otpauth-migration://offline?data=CksKCuRC3zgrq3wOpOgSImhhbmlmZWFybWFnYW43NEBnbWFpbC5jb20tQ29pbm8gVFIgASgBMAJCEzY0NzEwNTE3NTI4MjcyMzQxNzEKNwoKG9AA3QAr01X3SxIORW1yZSBLYXJhYnVsdXQgASgBMAJCEzlmZDczZTE3NTM3MDE0OTg4OTEKMgoK5enqo9%2Frgs0gyBIJRXpnaSBVc3RhIAEoATACQhNmNjYwMWYxNzUzNzAxNTk3MDUxCjIKCtzlkz%2Fgmu50%2FtcSCUFkZW0gxZ5hbCABKAEwAkITMjVlYTYwMTc1MzcwMjI4NzM0OQo8Cgp%2B%2BrPZmC6seV8jEhNBWcWeRSBCw5xZw5xLWUlMTUFaIAEoATACQhMxMTlmMDkxNzUzNzA4ODk2MTM4CjoKCstJuWM6AOw5qggSEcOWbWVyIFXEn3VyIEFsbWFzIAEoATACQhMzZDM4ZjExNzU0MDM5NjM1NDYzCjgKCj4LiKAJLq%2B1qMwSD09SS1VOIEVTRVJPxJ5MVSABKAEwAkITMzhmZjIyMTc1NDA0MDczOTY4MxACGAEgAA%3D%3D"  # QR linki buraya

# Hex isimlere karşılık gerçek isimler
name_map = {
    "471051752827234171": "HANİFE ARMAĞAN",
    "fd73e1753701498891": "EMRE KARABULUT",
    "6601f1753701597051": "EZGİ USTA",
    "5ea601753702287349": "ADEM ŞAL",
    "19f091753708896138": "AYŞE BÜYÜKYILMAZ"
}

def decode_migration_uri(uri):
    parsed = urllib.parse.urlparse(uri)
    query = urllib.parse.parse_qs(parsed.query)
    data_b64 = query['data'][0]
    return base64.b64decode(data_b64)

def parse_accounts(data):
    accounts = []
    i = 0
    while i < len(data):
        if data[i] == 10:  # length-delimited field
            length = data[i+1]
            chunk = data[i+2:i+2+length]
            name = ""
            secret = None
            issuer = ""
            j = 0
            while j < len(chunk):
                field = chunk[j] >> 3
                if field == 1:
                    slen = chunk[j+1]
                    secret = chunk[j+2:j+2+slen]
                    j += 2 + slen
                elif field == 2:
                    slen = chunk[j+1]
                    name = chunk[j+2:j+2+slen].decode('utf-8')
                    j += 2 + slen
                elif field == 3:
                    slen = chunk[j+1]
                    issuer = chunk[j+2:j+2+slen].decode('utf-8')
                    j += 2 + slen
                else:
                    j += 1
            if secret:
                accounts.append({"name": name, "secret": secret, "issuer": issuer})
            i += 2 + length
        else:
            i += 1
    return accounts

def get_codes():
    data = decode_migration_uri(MIGRATION_URI)
    accounts = parse_accounts(data)
    messages = []
    for acc in accounts:
        secret_b32 = base64.b32encode(acc["secret"]).decode()
        totp = pyotp.TOTP(secret_b32)
        code = totp.now()
        key = acc.get("name", "")
        display_name = name_map.get(key, key)
        messages.append(f"🔐 {display_name} kodu: {code}")
    return "\n".join(messages)

async def google(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Bu komut sadece grup içinde çalışır.")
        return
    codes = get_codes()
    await update.message.reply_text(codes, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("google", google, filters=filters.ChatType.GROUPS))
    app.run_polling()

if __name__ == "__main__":
    main()
