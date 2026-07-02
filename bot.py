from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import datetime

import os

TOKEN = os.getenv("TOKEN")

FREE_GROUP_LINK = "https://t.me/sabrin_englsh"
PREMIUM_GROUP_INFO = "للانضمام إلى المجموعة المدفوعة يرجى التواصل مع الإدارة."
PAYMENT_TEXT = "💳 BaridiMob: 00799999002543176470\n📄 CCP: 0025431764/70"
CONTACT_TEXT = "@amerhhk"


def load_words():
    words = []
    try:
        with open("words.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) == 3:
                        words.append(parts)
    except FileNotFoundError:
        pass
    return words
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 المجموعة المجانية", callback_data="free")],
        [InlineKeyboardButton("💎 المجموعة المدفوعة", callback_data="premium")],
        [InlineKeyboardButton("📖 كلمة اليوم", callback_data="today")],
        [InlineKeyboardButton("💳 معلومات الدفع", callback_data="payment")],
        [InlineKeyboardButton("📞 التواصل", callback_data="contact")],
    ]

    text = (
        "👋 مرحبًا بك في بوت الأستاذة صبرين لتعليم اللغة الإنجليزية.\n\n"
        "📚 اختر إحدى الخدمات من الأزرار التالية:"
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "free":
        await query.message.reply_text(
            f"📚 المجموعة المجانية:\n{FREE_GROUP_LINK}"
        )

    elif query.data == "premium":
        await query.message.reply_text(
            f"💎 {PREMIUM_GROUP_INFO}"
        )

    elif query.data == "payment":
        await query.message.reply_text(
            PAYMENT_TEXT
        )

    elif query.data == "contact":
        await query.message.reply_text(
            f"📞 للتواصل:\n{CONTACT_TEXT}"
        )

    elif query.data == "today":
        words = load_words()

        if not words:
            await query.message.reply_text("❌ ملف words.txt فارغ أو غير موجود.")
            return

        day = datetime.datetime.now().timetuple().tm_yday
        word = words[(day - 1) % len(words)]

        text = (
            f"📖 كلمة اليوم\n\n"
            f"🇬🇧 الكلمة: {word[0]}\n"
            f"🇸🇦 المعنى: {word[1]}\n\n"
            f"📝 المثال:\n{word[2]}"
        )

        await query.message.reply_text(text)

import asyncio

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("🤖 Bot is running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
