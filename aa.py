import base64
import urllib.parse
import pyotp
import asyncio
import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters

TELEGRAM_BOT_TOKEN = "7843763370:AAFngUVUd4oroByEotWcVyh_xQKvVI-t5Ng"

# Hesapları saklayacağımız JSON dosyası
ACCOUNTS_FILE = "accounts.json"

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
    data_b64 = query.get('data', [None])[0]
    if not data_b64:
        return None
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

def get_accounts_from_file():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    with open(ACCOUNTS_FILE, "r") as f:
        return json.load(f)

def save_accounts_to_file(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=2)

def get_codes():
    accounts = get_accounts_from_file()
    messages = []
    for name, uri in accounts.items():
        data = decode_migration_uri(uri)
        if not data:
            continue
        parsed_accounts = parse_accounts(data)
        for acc in parsed_accounts:
            secret_b32 = base64.b32encode(acc["secret"]).decode()
            totp = pyotp.TOTP(secret_b32)
            code = totp.now()
            key = acc.get("name", "")
            display_name = name_map.get(key, name)  # Öncelik json dosyasında verilen isim
            messages.append(f"🔐 {display_name} kodu: {code}")
    return "\n".join(messages)

async def google(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Bu komut sadece grup içinde çalışır.")
        return
    codes = get_codes()
    if codes == "":
        await update.message.reply_text("Şu an hesap bulunamadı.")
        return
    await update.message.reply_text(codes, parse_mode="Markdown")

async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Bu komut sadece grup içinde çalışır.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Kullanım: /add <isim> <otpauth-migration URI>")
        return

    name = args[0]
    uri = args[1]

    accounts = get_accounts_from_file()
    if name in accounts:
        await update.message.reply_text(f"'{name}' zaten var, önce /delete ile sil.")
        return

    accounts[name] = uri
    save_accounts_to_file(accounts)
    await update.message.reply_text(f"'{name}' başarıyla eklendi!")

async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Bu komut sadece grup içinde çalışır.")
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Kullanım: /delete <isim>")
        return

    name = args[0]

    accounts = get_accounts_from_file()
    if name not in accounts:
        await update.message.reply_text(f"'{name}' bulunamadı.")
        return

    del accounts[name]
    save_accounts_to_file(accounts)
    await update.message.reply_text(f"'{name}' başarıyla silindi!")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("google", google, filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("add", add_account, filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("delete", delete_account, filters=filters.ChatType.GROUPS))
    app.run_polling()

if __name__ == "__main__":
    main()
