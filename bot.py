from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import datetime
import os
import asyncio
import random

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


# دالة لحفظ أو تحديث حالة المشترك (active أو blocked)
def save_user(user_id, status="active"):
    users_dict = get_users_dict()
    users_dict[str(user_id)] = status
    
    with open("users.txt", "w", encoding="utf-8") as f:
        for u_id, stat in users_dict.items():
            f.write(f"{u_id}|{stat}\n")


# دالة لجلب قاموس المشتركين مع حالتهم
def get_users_dict():
    users_dict = {}
    try:
        with open("users.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) == 2:
                        users_dict[parts[0]] = parts[1]
                elif line:  # للتوافق مع الملفات القديمة التي تحتوي على ID فقط
                    users_dict[line] = "active"
    except FileNotFoundError:
        pass
    return users_dict


# دالة لجلب المشتركين حسب حالتهم
def get_users_by_status(status="active"):
    users_dict = get_users_dict()
    return [u_id for u_id, stat in users_dict.items() if stat == status]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # حفظ المستخدم كـ نشط وتحديث حالته إذا كان محظوراً سابقاً وعاد وضغط /start
    save_user(user_id, "active")

    keyboard = [
        [InlineKeyboardButton("📚 المجموعة المجانية", callback_data="free")],
        [InlineKeyboardButton("💎 المجموعة المدفوعة", callback_data="premium")],
        [
            InlineKeyboardButton("📖 كلمة اليوم", callback_data="today"), 
            InlineKeyboardButton("🧠 اختبار تفاعلي", callback_data="quiz")
        ],
        [InlineKeyboardButton("💳 معلومات الدفع", callback_data="payment")],
        [InlineKeyboardButton("📞 التواصل", callback_data="contact")],
    ]

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
        await query.message.reply_text(f"📚 المجموعة المجانية:\n{FREE_GROUP_LINK}")

    elif query.data == "premium":
        await query.message.reply_text(f"💎 {PREMIUM_GROUP_INFO}")

    elif query.data == "payment":
        await query.message.reply_text(PAYMENT_TEXT)

    elif query.data == "contact":
        await query.message.reply_text(f"📞 للتواصل:\n{CONTACT_TEXT}")

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

    elif query.data == "quiz":
        words = load_words()
        if len(words) < 4:
            await query.message.reply_text("❌ عذراً، يجب توفر 4 كلمات على الأقل في القاموس لتفعيل الاختبار التفاعلي.")
            return

        correct_word = random.choice(words)
        question = f"ما هو المعنى الصحيح للكلمة التالية؟\n\n 🤔  »  {correct_word[0].upper()}  «"
        wrong_meanings = list(set([w[1] for w in words if w[1] != correct_word[1]]))
        
        if len(wrong_meanings) < 3:
            await query.message.reply_text("❌ عذراً، لا توجد معانٍ مختلفة كافية لصنع خيارات الاختبار.")
            return

        selected_wrong = random.sample(wrong_meanings, 3)
        options = [correct_word[1]] + selected_wrong
        random.shuffle(options)
        correct_index = options.index(correct_word[1])
        
        explanation = f"المثال: {correct_word[2]}"
        if len(explanation) > 200:
            explanation = explanation[:197] + "..."

        await context.bot.send_poll(
            chat_id=query.message.chat_id,
            question=question,
            options=options,
            type="quiz",
            correct_option_id=correct_index,
            is_anonymous=False,
            explanation=explanation
        )

    # لوحة التحكم المتقدمة بالإحصائيات التفصيلية
    elif query.data == "admin_panel":
        if user_id in ADMIN_IDS:
            words = load_words()
            active_users = get_users_by_status("active")
            blocked_users = get_users_by_status("blocked")
            total_users = len(active_users) + len(blocked_users)
            
            # حساب النسبة المئوية للتفاعل
            active_pct = (len(active_users) / total_users * 100) if total_users > 0 else 0
            blocked_pct = (len(blocked_users) / total_users * 100) if total_users > 0 else 0

            text = (
                f"⚙️ **لوحة تحكم الإدارة المتقدمة**\n\n"
                f"📊 **التقرير الإحصائي المفصل:**\n"
                f"👥 إجمالي الطلاب المسجلين: `{total_users}` مستخدم.\n"
                f"🟢 الطلاب النشطين (الفعالين): `{len(active_users)}` ({active_pct:.1f}%)\n"
                f"🔴 قاموا بحظر البوت (Block): `{len(blocked_users)}` ({blocked_pct:.1f}%)\n"
                f"📝 إجمالي الكلمات المتاحة: `{len(words)}` كلمة.\n\n"
                f"📸 **طريقة الإرسال الجماعي (نصوص وصور):**\n"
                f"أرسل أو وجّه أي رسالة/صورة هنا للبث."
            )
            await query.message.reply_text(text, parse_mode="Markdown")
        else:
            await query.message.reply_text("❌ عذراً، هذه اللوحة خاصة بالمسؤول فقط.")

    elif query.data.startswith("send_broadcast_"):
        if user_id not in ADMIN_IDS:
            await query.message.reply_text("❌ عذراً، هذا الإجراء خاص بالإدارة فقط.")
            return

        msg_id = int(query.data.split("_")[2])
        active_users = get_users_by_status("active")
        blocked_users = get_users_by_status("blocked")
        all_targets = active_users + blocked_users

        if not all_targets:
            await query.message.reply_text("❌ لا يوجد أي مشتركين حالياً.")
            return

        await query.message.reply_text(f"🔄 جاري بدء البث الجماعي المتقدم إلى {len(all_targets)} مستخدم...")

        success_count = 0
        fail_count = 0

        for u_id in all_targets:
            try:
                await context.bot.copy_message(chat_id=int(u_id), from_chat_id=user_id, message_id=msg_id)
                success_count += 1
                save_user(u_id, "active")
                await asyncio.sleep(0.05)
            except Exception:
                fail_count += 1
                save_user(u_id, "blocked")
                continue

        await query.message.reply_text(
            f"✅ **اكتمل الإرسال الجماعي المتقدم!**\n\n"
            f"👍 تم التسليم بنجاح: `{success_count}` مستخدم نشط.\n"
            f"👎 فشل وتسجيل حظر: `{fail_count}` مستخدم تم تحويلهم لغير نشطين.\n"
            f"📈 تم تحديث الإحصائيات تلقائياً في لوحة التحكم."
        )


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in ADMIN_IDS:
        msg_id = update.message.message_id
        keyboard = [
            [InlineKeyboardButton("📢 إرسال جماعي للكل", callback_data=f"send_broadcast_{msg_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel")]
        ]
        await update.message.reply_text(
            "📥 تم استلام المحتوى.\nهل تريد بثه لجميع الطلاب مع تحديث الإحصائيات؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def daily_auto_send(app: Application):
    print("⏰ تم تشغيل نظام الإرسال التلقائي اليومي في الخلفية...")
    while True:
        try:
            now = datetime.datetime.now()
            if now.hour == 9 and now.minute == 0:
                words = load_words()
                users = get_users_by_status("active")
                
                if words and users:
                    day = now.timetuple().tm_yday
                    word = words[(day - 1) % len(words)]
                    
                    text = (
                        f"📢 **كلمة اليوم التلقائية** 📢\n\n"
                        f"🇬🇧 الكلمة: {word[0]}\n"
                        f"🇸🇦 المعنى: {word[1]}\n\n"
                        f"📝 المثال:\n{word[2]}"
                    )
                    
                    for u_id in users:
                        try:
                            await app.bot.send_message(chat_id=int(u_id), text=text, parse_mode="Markdown")
                            await asyncio.sleep(0.05)
                        except Exception:
                            save_user(u_id, "blocked")
                            continue
                    await asyncio.sleep(3600)
        except Exception as e:
            print(f"خطأ في نظام الإرسال التلقائي: {e}")
        await asyncio.sleep(60)


async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_admin_message))

    print("🤖 Bot is running with Advanced Stats...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    asyncio.create_task(daily_auto_send(app))

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
    
