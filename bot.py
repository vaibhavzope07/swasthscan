import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import io
import requests

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """You are SwasthScan — an expert food safety analyst for Indian food products.

Analyze the ingredients and respond in this exact format:

RATING: X/5
VERDICT: Safe / Moderate / Risky / Dangerous
VEG STATUS: Veg / Non-Veg / Unknown
RECOMMENDATION: Buy confidently / Buy occasionally / Avoid / Avoid entirely

SUMMARY:
(2 sentences max)

🚨 HARMFUL ADDITIVES:
• Additive name (CODE) — risk — HIGH/MEDIUM/LOW
(or "None detected" if clean)

🧪 ALLERGENS:
• Allergen — Present/Absent

🍬 NUTRITION CONCERNS:
• Sugar — High/Medium/Low — note
• Salt — High/Medium/Low — note
• Fat — High/Medium/Low — note

✅ POSITIVES:
• good thing 1
• good thing 2

Focus on Indian market and FSSAI regulations. Be accurate and concise."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔬 *Welcome to SwasthScan!*\n\n"
        "I analyze food ingredients and tell you if they are safe to eat.\n\n"
        "Send me:\n"
        "📸 A photo of the ingredients label\n"
        "✍️ Or type the ingredients list\n\n"
        "I will give you a full health rating instantly! 🇮🇳",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use SwasthScan:*\n\n"
        "1️⃣ Pick up any food packet\n"
        "2️⃣ Take a photo of the ingredients label\n"
        "3️⃣ Send it here\n"
        "4️⃣ Get instant health analysis!\n\n"
        "Or just type the ingredients directly.",
        parse_mode="Markdown"
    )


async def analyze_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text("🔬 Analyzing ingredients, please wait...")
    try:
        response = model.generate_content(
            SYSTEM_PROMPT + "\n\nAnalyze these ingredients: " + text
        )
        await update.message.reply_text(
            "📊 *SwasthScan Analysis*\n\n" + response.text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Text analysis error: {e}")
        await update.message.reply_text("❌ Analysis failed. Please try again.")


async def analyze_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Got your photo! Analyzing label, please wait...")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        response = requests.get(file.file_path)
        img = Image.open(io.BytesIO(response.content))
        gemini_response = model.generate_content([
            SYSTEM_PROMPT + "\n\nExtract the ingredients from this food label image and analyze them.",
            img
        ])
        await update.message.reply_text(
            "📊 *SwasthScan Analysis*\n\n" + gemini_response.text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Photo analysis error: {e}")
        await update.message.reply_text(
            "❌ Could not read the label clearly.\n"
            "Try typing the ingredients manually instead!"
        )


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_text))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_photo))
    logger.info("SwasthScan bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
