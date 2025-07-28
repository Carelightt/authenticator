import base64
import urllib.parse
import pyotp
import asyncio
from telegram import Bot
from otp_migration_pb2 import MigrationPayload

TELEGRAM_BOT_TOKEN = "BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = 123456789  # senin ID

def decode_migration_uri(uri):
    parsed = urllib.parse.urlparse(uri)
    query = urllib.parse.parse_qs(parsed.query)
    data_b64 = query['data'][0]
    data_bytes = base64.b64decode(data_b64)
    return data_bytes

def parse_migration_payload(data_bytes):
    payload = MigrationPayload()
    payload.ParseFromString(data_bytes)
    return payload

async def send_totp_codes(bot, chat_id, accounts):
    last_codes = {name: None for name in accounts}
    while True:
        for name, secret in accounts.items():
            totp = pyotp.TOTP(secret)
            code = totp.now()
            if last_codes[name] != code:
                await bot.send_message(chat_id=chat_id, text=f"🔐 {name} kodu: `{code}`", parse_mode="Markdown")
                last_codes[name] = code
        await asyncio.sleep(1)

async def main():
    uri = input("otpauth-migration URI'sini gir: ")
    data_bytes = decode_migration_uri(uri)
    payload = parse_migration_payload(data_bytes)

    accounts = {}
    for otp in payload.otp_parameters:
        name = otp.name
        secret = base64.b32encode(otp.secret).decode('utf-8')
        accounts[name] = secret
        print(f"Hesap: {name} | Secret: {secret}")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await send_totp_codes(bot, TELEGRAM_CHAT_ID, accounts)

if __name__ == "__main__":
    asyncio.run(main())
