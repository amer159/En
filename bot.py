from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import datetime
import os
import asyncio
import random
import psycopg2

# 🔑 جلب المتغيرات البيئية من السيرفر بشكل آمن
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

FREE_GROUP_LINK = "https://t.me/sabrin_englsh"
PREMIUM_GROUP_INFO = (
    "للانضمام إلى المجموعة المدفوعة أو الاستفسار عن الأسعار، "
    "يمكنك كتابة رسالتك وإرسالها هنا داخل هذا البوت مباشرة، "
    "وسيجيبك فريق الإدارة في أسرع وقت ممكن! 📬"
)
PAYMENT_TEXT = "💳 BaridiMob: 00799999002543176470\n📄 CCP: 0025431764/70"

# 🔒 معرفات المسؤولين والأدمن
PRIMARY_ADMIN = 5003264608       
ADMIN_IDS = [5003264608, 5028116353]  

# 📝 بنك الأسئلة المتتالية المستخرجة من ملف face2face الخاص بكِ
QUIZ_QUESTIONS = [
    {"q": "TOM: How are you?\nSTEVE: _________", "options": ["I'm fine, thanks", "I'm Steve", "Yes please."], "correct": 0, "exp": "الرد الطبيعي على السؤال عن الحال."},
    {"q": "LIZ: What are these?\nJANE: _________ my birthday cards.", "options": ["They're", "This is", "It's"], "correct": 0, "exp": "نستخدم They're لأن cards جمع."},
    {"q": "Are you married _________ single?", "options": ["and", "or", "but"], "correct": 1, "exp": "نستخدم or للاختيار بين شيئين."},
    {"q": "What's your email _________?", "options": ["address", "name", "number"], "correct": 0, "exp": "البريد الإلكتروني يسمى email address."},
    {"q": "Jim _________ have a car.", "options": ["doesn't", "isn't", "don't"], "correct": 0, "exp": "نفي الفعل المضارع مع المفرد (Jim) يكون بـ doesn't."},
    {"q": "I _________ to Italy for my holiday last year.", "options": ["went", "go", "was", "were"], "correct": 0, "exp": "بسبب وجود last year نختار الماضي من go وهو went."},
    {"q": "I didn't _________ TV last night.", "options": ["watched", "watching", "watch", "not watched"], "correct": 2, "exp": "بعد didn't يأتي الفعل في التصريف الأول (المصدر)."},
    {"q": "London is _________ expensive than New York.", "options": ["more", "very", "too", "quite"], "correct": 0, "exp": "في المقارنة بين صفتين طويلتين نستخدم more ... than."},
    {"q": "Have you ever _________ to Australia?", "options": ["been", "go", "be", "went"], "correct": 0, "exp": "مع المضارع التام (Have you ever) نستخدم التصريف الثالث been."},
    {"q": "You _________ to study hard if you want to pass your exams.", "options": ["must", "should", "have", "supposed"], "correct": 2, "exp": "الخيار الوحيد الذي يأتي بعده حرف الجر 'to' ليعطي معنى الإلزام هو have to."}
]

# 🎙️ مواضيع التحدث المقترحة 
SPEAKING_TOPICS = [
    {"id": "topic_1", "title": "👨‍👩‍👧‍👦 Talk about your family"},
    {"id": "topic_2", "title": "📅 Talk about your daily routine"},
    {"id": "topic_3", "title": "✈️ Talk about your last holiday"},
    {"id": "topic_4", "title": "💻 Talk about your dream job"}
]


def init_db():
    if not DATABASE_URL:
        print("❌ خطأ: لم يتم العثور على DATABASE_URL في المتغيرات البيئية!")
        return
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id VARCHAR(50) PRIMARY KEY,
                    status VARCHAR(20) DEFAULT 'active'
                );
            """)
            conn.commit()
    print("✅ تم فحص وإنشاء جدول قاعدة البيانات بنجاح.")


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


def save_user(user_id, status="active"):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (user_id, status) 
                    VALUES (%s, %s) 
                    ON CONFLICT (user_id) 
                    DO UPDATE SET status = EXCLUDED.status;
                """, (str(user_id), status))
                conn.commit()
    except Exception as e:
        print(f"خطأ في حفظ المستخدم في قاعدة البيانات: {e}")


def get_users_by_status(status="active"):
    users = []
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id FROM users WHERE status = %s;", (status,))
                rows = cur.fetchall()
                users = [row[0] for row in rows]
    except Exception as e:
        print(f"خطأ في جلب المستخدمين من قاعدة البيانات: {e}")
    return users


def get_total_users_count():
    count = 0
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users;")
                count = cur.fetchone()[0]
    except Exception as e:
        print(f"خطأ في حساب إجمالي المستخدمين: {e}")
    return count


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    save_user(user_id, "active")

    # إزالة زر المحادثة من القائمة الرئيسية لكي لا يظهر إلا بعد انتهاء الكتابي تماماً
    keyboard = [
        [InlineKeyboardButton("📚 المجموعة المجانية", callback_data="free")],
        [InlineKeyboardButton("💎 المجموعة المدفوعة", callback_data="premium")],
        [InlineKeyboardButton("📝 اختبر مستواك (كتابي)", callback_data="start_quiz")],
        [InlineKeyboardButton("📖 كلمة اليوم", callback_data="today")],
        [InlineKeyboardButton("💳 معلومات الدفع", callback_data="payment")],
    ]

    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم (الأدمن)", callback_data="admin_panel")])

    text = (
        "👋 مرحبًا بك في بوت الأستاذة صابرين لتعليم اللغة الإنجليزية.\n\n"
        "✨ يسعدني مساعدتك في تطوير لغتك الإنجليزية اليوم!\n"
        "الرجاء اختيار الخدمة التي تريدها من الأزرار التالية أو أرسل استفسارك مباشرة في الشات 👇:"
    )

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def send_next_question(chat_id, context: ContextTypes.DEFAULT_TYPE, user_data, update_query=None):
    current_index = user_data.get("current_question", 0)
    
    # عند انتهاء أسئلة الاختبار الكتابي بالكامل
    if current_index >= len(QUIZ_QUESTIONS):
        score = user_data.get("score", 0)
        total = len(QUIZ_QUESTIONS)
        
        # جلب بيانات الطالب لإرسالها للأدمن
        user_name = update_query.from_user.full_name if update_query else "مستعمل"
        username = f"@{update_query.from_user.username}" if update_query and update_query.from_user.username else "بدون يوزر"
        user_id = update_query.from_user.id if update_query else chat_id
        
        # إنشاء زر اختبار المحادثة ليظهر الآن فقط بعد انتهاء الكتابي
        speaking_keyboard = [[InlineKeyboardButton("🎙️ اختبر مستواك (محادثة)", callback_data="speaking_challenge")]]
        
        # 1. إشعار الطالب بالانتظار مع إظهار زر الانتقال لاختبار المحادثة
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🎉 **أحسنت! لقد أكملت الجزء الأول (الاختبار الكتابي) بنجاح.**\n\n"
                "يرجى انتظار رسالة من الأستاذة صابرين بها نتيجة امتحانك وتقييم مستواك الإجمالي! ⏳\n\n"
                "👇 والآن انتقل للجزء الثاني والأخير من اختبار تحديد المستوى بالضغط على الزر أدناه لإرسال رسالتك الصوتية:"
            ),
            reply_markup=InlineKeyboardMarkup(speaking_keyboard)
        )
        
        # 2. إرسال النتيجة إلى لوحة تحكم الأدمن فوراً
        admin_alert = (
            f"📊 **نتيجة اختبار كتابي جديدة**\n\n"
            f"👤 الطالب: {user_name}\n"
            f"🔗 اليوزر: {username}\n"
            f"🆔 ID: {user_id}\n\n"
            f"📈 النتيجة التلقائية: `{score}` من `{total}`\n"
            f"✍️ يمكنكِ الرد على هذه الرسالة لاحقاً لإرسال التقييم النهائي للطالب."
        )
        for admin in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin, text=admin_alert)
            except Exception:
                continue
                
        user_data.clear()
        return

    q_data = QUIZ_QUESTIONS[current_index]
    keyboard = []
    for idx, option in enumerate(q_data["options"]):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"answer_{idx}")])
        
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"📝 **السؤال {current_index + 1} من {len(QUIZ_QUESTIONS)}:**\n\n{q_data['q']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = context.user_data
    await query.answer()

    if query.data == "free":
        await query.message.reply_text(f"📚 المجموعة المجانية:\n{FREE_GROUP_LINK}")

    elif query.data == "premium":
        await query.message.reply_text(f"💎 {PREMIUM_GROUP_INFO}")

    elif query.data == "payment":
        await query.message.reply_text(PAYMENT_TEXT)

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

    # 📥 بدء اختبار تحديد المستوى (كتابي)
    elif query.data == "start_quiz":
        user_data["current_question"] = 0
        user_data["score"] = 0
        await query.message.reply_text("🚀 سيبدأ اختبار تحديد المستوى الآن! أجب على الأسئلة التالية:")
        await send_next_question(query.message.chat_id, context, user_data, query)

    # 📥 معالجة الإجابات للكتابي
    elif query.data.startswith("answer_"):
        if "current_question" not in user_data:
            await query.message.reply_text("❌ انتهى هذا الاختبار أو أصبح قديماً. يرجى الضغط على 'اختبر مستواك (كتابي)' للبدء مجدداً.")
            return
            
        selected_idx = int(query.data.split("_")[1])
        current_index = user_data["current_question"]
        q_data = QUIZ_QUESTIONS[current_index]
        
        if selected_idx == q_data["correct"]:
            user_data["score"] += 1
            feedback = "✅ تم تسجيل إجابتك بنجاح!"
        else:
            feedback = "✅ تم تسجيل إجابتك بنجاح!"
            
        await query.message.reply_text(feedback, parse_mode="Markdown")
        user_data["current_question"] += 1
        await send_next_question(query.message.chat_id, context, user_data, query)

    # 🎙️ اختبار تحديد المستوى (محادثة) - يظهر ويُستدعى بعد انتهاء الكتابي
    elif query.data == "speaking_challenge":
        keyboard = []
        for topic in SPEAKING_TOPICS:
            keyboard.append([InlineKeyboardButton(topic["title"], callback_data=f"select_{topic['id']}")])
            
        await query.message.reply_text(
            "🎙️ **مرحباً بك في اختبار تحديد مستوى المحادثة!**\n\n"
            "الرجاء اختيار أحد المواضيع التالية لكي تتحدث عنها 👇:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 🎙️ معالجة اختيار الموضوع للمحادثة
    elif query.data.startswith("select_"):
        topic_id = query.data.replace("select_", "")
        selected_topic = next((t["title"] for t in SPEAKING_TOPICS if t["id"] == topic_id), "موضوع غير معروف")
        
        user_data["chosen_topic"] = selected_topic
        
        await query.message.reply_text(
            f"🎯 لقد اخترت موضوع:\n*{selected_topic}*\n\n"
            f"قم الآن بتسجيل بصمة صوتية (Voice Note) تتكلم فيها بالإنجليزية حول هذا الموضوع (يفضل ألا تتجاوز دقيقتين).\n"
            f"سيرسل البوت تسجيلك للأستاذة صابرين لتقييم نطقك وقواعدك وتحديد مستواك! ⏳",
            parse_mode="Markdown"
        )

    # باقي كود لوحة تحكم الأدمن...
    elif query.data == "admin_panel":
        if user_id in ADMIN_IDS:
            words = load_words()
            active_users = get_users_by_status("active")
            blocked_users = get_users_by_status("blocked")
            total_users = get_total_users_count()
            active_pct = (len(active_users) / total_users * 100) if total_users > 0 else 0
            text = f"⚙️ **لوحة تحكم الإدارة المتقدمة**\n\n👥 إجمالي الطلاب: `{total_users}`.\n🟢 النشطين: `{len(active_users)}` ({active_pct:.1f}%)"
            admin_keyboard = [
                [InlineKeyboardButton("📥 تحميل ملف الكلمات", callback_data="backup_words")],
                [InlineKeyboardButton("📥 تحميل ملف المشتركين", callback_data="backup_users_list")]
            ]
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(admin_keyboard), parse_mode="Markdown")

    elif query.data == "backup_words":
        if user_id in ADMIN_IDS and os.path.exists("words.txt"):
            with open("words.txt", "rb") as doc:
                await context.bot.send_document(chat_id=user_id, document=doc, filename="words.txt", caption="📦 نسخة احتياطية لملف الكلمات.")

    elif query.data == "backup_users_list":
        if user_id in ADMIN_IDS:
            all_users = get_users_by_status("active") + get_users_by_status("blocked")
            if not all_users: return
            temp_filename = "users.txt"
            with open(temp_filename, "w", encoding="utf-8") as f:
                for u in all_users: f.write(f"{u}\n")
            with open(temp_filename, "rb") as doc:
                await context.bot.send_document(chat_id=user_id, document=doc, filename="users.txt")
            try: os.remove(temp_filename)
            except Exception: pass

    elif query.data.startswith("send_broadcast_"):
        if user_id not in ADMIN_IDS: return
        msg_id = int(query.data.split("_")[2])
        all_targets = get_users_by_status("active") + get_users_by_status("blocked")
        await query.message.reply_text(f"🔄 جاري بدء البث الجماعي...")
        success_count, fail_count = 0, 0
        for u_id in all_targets:
            if int(u_id) == user_id: continue
            try:
                await context.bot.copy_message(chat_id=int(u_id), from_chat_id=user_id, message_id=msg_id)
                success_count += 1
                save_user(u_id, "active")
                await asyncio.sleep(0.05)
            except Exception:
                fail_count += 1
                save_user(u_id, "blocked")
        await query.message.reply_text(f"✅ اكتمل الإرسال الجماعي!\nنجاح: `{success_count}`\nفشل: `{fail_count}`")


async def handle_user_and_admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.message.from_user.id
    user_name = update.message.from_user.full_name
    username = f"@{update.message.from_user.username}" if update.message.from_user.username else "بدون يوزر"
    user_data = context.user_data

    if user_id in ADMIN_IDS:
        if update.message.reply_to_message:
            reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
            if reply_text and "🆔 ID:" in reply_text:
                try:
                    target_user_id = int(reply_text.split("🆔 ID:")[1].strip().split("\n")[0])
                    if update.message.text:
                        await context.bot.send_message(chat_id=target_user_id, text=f"💬 **رد من الإدارة:**\n\n{update.message.text}")
                    else:
                        await context.bot.copy_message(chat_id=target_user_id, from_chat_id=user_id, message_id=update.message.message_id)
                    await update.message.reply_text("✅ تم إرسال ردك إلى المستخدم بنجاح.")
                    return
                except Exception as e:
                    await update.message.reply_text(f"❌ فشل إرسال الرد للمستخدم. الخطأ: {e}")
                    return

        msg_id = update.message.message_id
        keyboard = [
            [InlineKeyboardButton("📢 إرسال جماعي للكل", callback_data=f"send_broadcast_{msg_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel")]
        ]
        await update.message.reply_text("📥 تم استلام المحتوى. هل تريد بثه؟", reply_markup=InlineKeyboardMarkup(keyboard))

    else:
        save_user(user_id, "active")
        
        # تحقق من إرسال بصمة صوتية لاختبار تحديد مستوى المحادثة
        chosen_topic = user_data.get("chosen_topic", None)
        
        if chosen_topic and (update.message.voice or update.message.audio):
            info_header = f"🎙️ **إجابة اختبار تحديد مستوى المحادثة**\n🎯 الموضوع المختار: *{chosen_topic}*\n👤 الاسم: {user_name}\n🔗 اليوزر: {username}\n🆔 ID: {user_id}\n\n"
            user_data.pop("chosen_topic", None)
        else:
            info_header = f"📩 **رسالة جديدة من مستخدم**\n👤 الاسم: {user_name}\n🔗 اليوزر: {username}\n🆔 ID: {user_id}\n\n📝 **محتوى الرسالة:**\n"
        
        for admin in ADMIN_IDS:
            try:
                if update.message.text:
                    await context.bot.send_message(chat_id=admin, text=f"{info_header}{update.message.text}")
                else:
                    caption = f"{info_header}{update.message.caption if update.message.caption else ''}"
                    await context.bot.copy_message(chat_id=admin, from_chat_id=user_id, message_id=update.message.message_id, caption=caption)
            except Exception:
                continue
                
        await update.message.reply_text("📥 تم استلام مشاركتك وتوجيهها للأستاذة صابرين بنجاح. سيتم الرد عليك وتقييم مستواك هنا فور الاطلاع.")


async def daily_auto_send(context: ContextTypes.DEFAULT_TYPE):
    while True:
        try:
            now = datetime.datetime.now()
            if now.hour == 9 and now.minute == 0:
                words = load_words()
                users = get_users_by_status("active")
                if words and users:
                    day = now.timetuple().tm_yday
                    word = words[(day - 1) % len(words)]
                    text = f"📢 **كلمة اليوم التلقائية** 📢\n\n🇬🇧 الكلمة: {word[0]}\n🇸🇦 المعنى: {word[1]}\n\n📝 المثال:\n{word[2]}"
                    for u_id in users:
                        try:
                            await context.bot.send_message(chat_id=int(u_id), text=text, parse_mode="Markdown")
                            await asyncio.sleep(0.05)
                        except Exception:
                            save_user(u_id, "blocked")
                    await asyncio.sleep(3600)
        except Exception: pass
        await asyncio.sleep(60)


async def post_init(application: Application):
    asyncio.create_task(daily_auto_send(application))


def main():
    init_db()
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_user_and_admin_messages))
    print("🤖 Bot is running smoothly...")
    app.run_polling()


if __name__ == "__main__":
    main()
    
