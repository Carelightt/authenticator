import base64
import urllib.parse
import pyotp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters

TELEGRAM_BOT_TOKEN = "8468644425:AAGJq2zEJiOSvrox8uqMv1VePrD9VsnrmDs"
MIGRATION_URI = "otpauth-migration://offline?data=CksKCuRC3zgrq3wOpOgSImhhbmlmZWFybWFnYW43NEBnbWFpbC5jb20tQ29pbm8gVFIgASgBMAJCE2ZlZWVmMTE3NTQwNjQ2MTQ4OTgKNwoKG9AA3QAr01X3SxIORW1yZSBLYXJhYnVsdXQgASgBMAJCEzA5ODVkYjE3NTQwNjQ2MTQ4OTgKMgoK5enqo9%2Frgs0gyBIJRXpnaSBVc3RhIAEoATACQhM1OWQ3NjQxNzU0MDY0NjE0ODk4CjIKCtzlkz%2Fgmu50%2FtcSCUFkZW0gxZ5hbCABKAEwAkITZjQ1YzEyMTc1NDA2NDYxNDg5OAo8Cgp%2B%2BrPZmC6seV8jEhNBWcWeRSBCw5xZw5xLWUlMTUFaIAEoATACQhNlMmRkNDQxNzU0MDY0NjE0ODk4CjoKCstJuWM6AOw5qggSEcOWbWVyIFXEn3VyIEFsbWFzIAEoATACQhM3ZWI1NTYxNzU0MDY0NjE0ODk4CjgKCgMDv3eP5nVGDhgSD09SS1VOIEVTRVJPxJ5MVSABKAEwAkITNDU3ZDZjMTc1NDA2NDYxNDg5OAqSAQoga21QOkRYI2csbUpRbyk6I2N4Knc%2BNlRPTFRFYlRPaXoSUzEyNGRiOGI4NTFhMmZhZmI4YTRiYjc4YzhmNGZlZDc3NjIyNmNmNGY5YTJjNmJmZWJlOWRlNTlmMDQ2MDNhZTkgKGFuZ2VsQHh3YWxsZS5jb20pIAEoATACQhNiMTk1NDUxNzU0ODM3NDkzODI2CjYKCl8pVpiOe%2BeB5ScSDVNFVkRBIFTEsMSeRUwgASgBMAJCEzk2NGRmNzE3NTUwMDI1MzEzMjkQAhgBIAA%3D"  # QR linki buraya

# ✅ EVİN BOZTEPE — tek hesap için ek QR (senin verdiğin link)
NEW_MIGRATION_URI = "otpauth-migration://offline?data=CjYKCtuhTUSAvnWVFccSDUVWxLBOIEJPWlRFUEUgASgBMAJCE2QzN2RkZjE3NTUwMzkzOTU5OTMQAhgBIAA%3D"

# Hex isimlere karşılık gerçek isimler
name_map = {
    "19545175483749382": "PANEL GİRİŞİ",
    "eeef11754064614898": "HANİFE ARMAĞAN",
    "985db1754064614898": "EMRE KARABULUT",
    "9d7641754064614898": "EZGİ USTA",
    "45c121754064614898": "ADEM ŞAL",
    "2dd441754064614898": "AYŞE BÜYÜKYILMAZ",
    "eb5561754064614898": "ÖMER UĞUR ALMAS",
    "57d6c1754064614898": "ORKUN ESEROĞLU",
    "64df71755002531329": "SEVDA TİĞEL"
}

# ✅ EVİN BOZTEPE görünür adı için sabit key ekledim
name_map.update({
    "manual_evin_boztepe": "EVİN BOZTEPE"
})

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
    # Mevcut toplu URI
    data = decode_migration_uri(MIGRATION_URI)
    accounts = parse_accounts(data)

    # ✅ EVİN BOZTEPE tek hesabını ekle (diğerleri bozulmaz)
    try:
        data_new = decode_migration_uri(NEW_MIGRATION_URI)
        new_accounts = parse_accounts(data_new)
        for acc in new_accounts:
            accounts.append({
                "name": "manual_evin_boztepe",           # sabit key
                "secret": acc["secret"],                  # QR'dan gelen ham secret
                "issuer": acc.get("issuer", "Authenticator")
            })
    except Exception:
        # Yeni QR okunamazsa sessiz geç (mevcudu bozma)
        pass

    messages = []
    for acc in accounts:
        secret_b32 = base64.b32encode(acc["secret"]).decode()
        totp = pyotp.TOTP(secret_b32)
        code = totp.now()
        key = acc.get("name", "")
        display_name = name_map.get(key, key)
        # HTML code block: tıklayınca kopyalanır
        messages.append(f"🔐 <b>{display_name}</b>\n<code>{code}</code>")
    return "\n\n".join(messages)

async def kod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Bu komut sadece grup içinde çalışır.")
        return
    codes = get_codes()
    await update.message.reply_text(codes, parse_mode="HTML")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("kod", kod, filters=filters.ChatType.GROUPS))
    app.run_polling()

if __name__ == "__main__":
    main()
