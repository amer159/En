from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import datetime
import os
import asyncio

# قراءة التوكن بأمان من المتغيرات البيئية في Railway
TOKEN = os.getenv("TOKEN")

FREE_GROUP_LINK = "https://t.me/sabrin_englsh"
PREMIUM_GROUP_INFO = "للانضمام إلى المجموعة المدفوعة يرجى التواصل مع الإدارة."
PAYMENT_TEXT = "💳 BaridiMob: 00799999002543176470\n📄 CCP: 0025431764/70"
CONTACT_TEXT = "@amerhhk"

# قائمة معرفات الإدارة
ADMIN_IDS = [5003264608]  


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


# دالة لحفظ المشتركين الجدد في ملف نصي users.txt
def save_user(user_id):
    users = get_users()
    if str(user_id) not in users:
        with open("users.txt", "a", encoding="utf-8") as f:
            f.write(f"{user_id}\n")


# دالة لجلب قائمة المشتركين من الملف
def get_users():
    try:
        with open("users.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # حفظ المستخدم تلقائياً عند ضغط /start لرصد عدد المشتركين
    save_user(user_id)

    keyboard = [
        [InlineKeyboardButton("📚 المجموعة المجانية", callback_data="free")],
        [InlineKeyboardButton("💎 المجموعة المدفوعة", callback_data="premium")],
        [InlineKeyboardButton("📖 كلمة اليوم", callback_data="today")],
        [InlineKeyboardButton("💳 معلومات الدفع", callback_data="payment")],
        [InlineKeyboardButton("📞 التواصل", callback_data="contact")],
    ]

    # التحقق إذا كان المستخدم ضمن قائمة الإدارة
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم (الأدمن)", callback_data="admin_panel")])

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
    user_id = query.from_user.id
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

    # استجابة زر لوحة التحكم للأدمن فقط
    elif query.data == "admin_panel":
        if user_id in ADMIN_IDS:
            words = load_words()
            users = get_users()
            
            text = (
                f"⚙️ **لوحة تحكم الإدارة**\n\n"
                f"📊 **الإحصائيات الحالية:**\n"
                f"👥 عدد الطلاب المنضمين للبوت: `{len(users)}` مستخدم.\n"
                f"📝 إجمالي الكلمات المتاحة: `{len(words)}` كلمة.\n\n"
                f"📸 **طريقة الإرسال الجماعي (نصوص وصور):**\n"
                f"قم بإرسال أو توجيه (Forward) أي رسالة أو صورة مباشرة إلى البوت هنا، وسيظهر لك زر لتأكيد بثها لجميع الطلاب."
            )
            await query.message.reply_text(text, parse_mode="Markdown")
        else:
            await query.message.reply_text("❌ عذراً، هذه اللوحة خاصة بالمسؤول فقط.")

    # 🟢 تنفيذ البث الجماعي عند ضغط زر التأكيد
    elif query.data.startswith("send_broadcast_"):
        if user_id not in ADMIN_IDS:
            await query.message.reply_text("❌ عذراً، هذا الإجراء خاص بالإدارة فقط.")
            return

        msg_id = int(query.data.split("_")[2])
        users = get_users()

        if not users:
            await query.message.reply_text("❌ لا يوجد أي مشتركين حالياً.")
            return

        await query.message.reply_text(f"🔄 جاري بدء البث الجماعي إلى {len(users)} مستخدم...")

        success_count = 0
        fail_count = 0

        for u_id in users:
            try:
                # دالة copy_message تقوم بنسخ الرسالة الأصلية مهما كان نوعها (نص، صورة، إلخ)
                await context.bot.copy_message(chat_id=int(u_id), from_chat_id=user_id, message_id=msg_id)
                success_count += 1
                await asyncio.sleep(0.05)  # لتفادي حظر التليجرام
            except Exception:
                fail_count += 1
                continue

        await query.message.reply_text(
            f"✅ **اكتمل الإرسال الجماعي بنجاح!**\n\n"
            f"👍 تم التسليم إلى: `{success_count}` مستخدم.\n"
            f"👎 فشل التسليم إلى: `{fail_count}` مستخدم."
        )


# 🟢 استقبال أي رسالة أو صورة من الأدمن وتجهيزها للبث
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # التحقق من أن المرسل أدمن
    if user_id in ADMIN_IDS:
        msg_id = update.message.message_id
        
        keyboard = [
            [InlineKeyboardButton("📢 إرسال جماعي للكل", callback_data=f"send_broadcast_{msg_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel")]
        ]
        
        await update.message.reply_text(
            "📥 تم استلام الرسالة/الصورة بنجاح.\nهل تريد بثها لجميع الطلاب الآن؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# وظيفة فحص الوقت والإرسال التلقائي اليومي للكلمات لجميع المشتركين
async def daily_auto_send(app: Application):
    print("⏰ تم تشغيل نظام الإرسال التلقائي اليومي في الخلفية...")
    while True:
        try:
            now = datetime.datetime.now()
            if now.hour == 9 and now.minute == 0:
                words = load_words()
                users = get_users()
                
                if words and users:
                    day = now.timetuple().tm_yday
                    word = words[(day - 1) % len(words)]
                    
                    text = (
                        f"📢 **كلمة اليوم التلقائية** 📢\n\n"
                        f"🇬🇧 الكلمة: {word[0]}\n"
                        f"🇸🇦 المعنى: {word[1]}\n\n"
                        f"📝 المثال:\n{word[2]}"
                    )
                    
                    print(f"🔄 جاري إرسال كلمة اليوم تلقائياً إلى {len(users)} مستخدم...")
                    for u_id in users:
                        try:
                            await app.bot.send_message(chat_id=int(u_id), text=text, parse_mode="Markdown")
                            await asyncio.sleep(0.05)
                        except Exception:
                            continue
                    
                    print("✅ تم الإرسال اليومي التلقائي بنجاح لكافة الطلاب.")
                    await asyncio.sleep(3600)
        except Exception as e:
            print(f"خطأ في نظام الإرسال التلقائي: {e}")
            
        await asyncio.sleep(60)


async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    
    # 🟢 التقاط أي رسالة (نص، صورة، ملفات) مرسلة من الأدمن لتجهيز بثها
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_admin_message))

    print("🤖 Bot is running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    asyncio.create_task(daily_auto_send(app))

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
        
