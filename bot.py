import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import json
import gspread
from google.oauth2.service_account import Credentials

################
#Token telegram:

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN no está configurado")

print("Token cargado OK")

################
#Sheet:
creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

client = gspread.authorize(creds)

sheet = client.open_by_key("1kJoP9KJt8BqGVZLwCV96OtADYXBV1gP3oaiJOIZJ_gU").worksheet("Gastos")


#####################
#Parsear el Texto enviado
import re
from datetime import datetime

def detectar_categoria(texto):
    texto_lower = texto.lower()

    # categorías automáticas conocidas
    if any(x in texto_lower for x in ["uber", "taxi", "cabify"]):
        return "Transporte"
    elif any(x in texto_lower for x in ["super", "mercado"]):
        return "Supermercado"
    elif "alquiler" in texto_lower:
        return "Alquiler"
    #elif any(x in texto_lower for x in ["luz", "agua", "gas"]):
    #    return "Servicios"

    # 👇 NUEVO: usar primera palabra como categoría
    palabras = texto.strip().split()
    if len(palabras) > 0:
        return palabras[0].capitalize()

    return "Varios"


def detectar_fecha(texto):
    texto = texto.lower()
    hoy = datetime.now()

    if "hoy" in texto:
        return hoy.strftime("%Y-%m")

    meses = {
        "enero": "01", "febrero": "02", "marzo": "03",
        "abril": "04", "mayo": "05", "junio": "06",
        "julio": "07", "agosto": "08", "septiembre": "09",
        "octubre": "10", "noviembre": "11", "diciembre": "12"
    }

    for mes, num in meses.items():
        if mes in texto:
            return f"{hoy.year}-{num}"

    return hoy.strftime("%Y-%m")


def parse_message(text):
    # detectar monto
    monto_match = re.search(r"\$?(\d+[\.\d]*)", text)
    if not monto_match:
        return None

    monto = float(monto_match.group(1))

    # limpiar monto del texto
    texto_sin_monto = text.replace(monto_match.group(0), "").strip()

    categoria = detectar_categoria(texto_sin_monto)
    fecha = detectar_fecha(texto_sin_monto)

    return {
        "categoria": categoria,
        "mes": fecha,
        "monto": monto,
        "observacion": texto_sin_monto
    }

############################
#Responder y cargarlo en Drive
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    data = parse_message(text)

    if not data:
        await update.message.reply_text("Formato inválido😅")
        return
        
    sheet.append_row([
        data["mes"],
        data["categoria"],
        data["monto"],
        data["observacion"]
    ])
    
    await update.message.reply_text(
        f"Registrado:\n"
        f"Categoría: {data['categoria']}\n"
        f"Mes: {data['mes']}\n"
        f"Monto: {data['monto']}\n"
        f"Obs: {data['observacion']}"
    )

try:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    print("Bot corriendo...")
    app.run_polling()

except Exception as e:
    print("ERROR REAL:", e)
    raise


