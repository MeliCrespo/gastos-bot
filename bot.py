import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import json
import gspread
from google.oauth2.service_account import Credentials

creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

scopes = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

client = gspread.authorize(creds)

sheet = client.open("Gastos").sheet1

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN no está configurado")

print("Token cargado OK")

import re

def parse_message(text):
    pattern = r"(\w+)\s+(\w+\s+\d{4})\s+\$?([\d\.]+)"
    match = re.match(pattern, text)

    if not match:
        return None

    categoria, mes, monto = match.groups()
    return {
        "categoria": categoria,
        "mes": mes,
        "monto": float(monto)
    }


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    data = parse_message(text)

    if not data:
        await update.message.reply_text("Formato inválido😅")
        return
        
    sheet.append_row([
        data["mes"],
        data["categoria"],
        data["monto"]
    ])    
    
    await update.message.reply_text(
        f"Registrado:\n"
        f"Categoría: {data['categoria']}\n"
        f"Mes: {data['mes']}\n"
        f"Monto: {data['monto']}"
    )

try:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    print("Bot corriendo...")
    app.run_polling()

except Exception as e:
    print("ERROR REAL:", e)
    raise


