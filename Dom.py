import requests
import random
import time
import os
import logging
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

# =============================================
#   ⚙️ الإعدادات الأساسية
# =============================================
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا")
AUTHOR      = "GASRI NADJI"
INSTAGRAM   = "@domx.54"
CLIENT_ID   = "87pIExRhxBb3_wGsA5eSEfyATloa"
CLIENT_SECRET = "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa"
BASE_URL    = "https://apim.djezzy.dz/mobile-api"
# =============================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent":    "MobileApp/3.0.0",
    "Accept":        "application/json",
    "Content-Type":  "application/json",
    "accept-language": "fr",
}

# ─── مراحل المحادثة ───────────────────────────
WAIT_FOLLOW, WAIT_PHONE, WAIT_OTP = range(3)

FOLLOW_CHECK_BTN = "✅ تابعت الحساب، تابع"

# ══════════════════════════════════════════════
#   🌟 رسالة الترحيب
# ══════════════════════════════════════════════
WELCOME_TEXT = (
    "╔══════════════════════╗\n"
    "║   أهلاً وسهلاً بك   ║\n"
    "╚══════════════════════╝\n\n"
    "✨ *مرحباً بك في بوت جيزي MGM*\n"
    "يُتيح لك هذا البوت الحصول على *1GB مجاناً* 🎁\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    f"👨‍💻 المطوّر: *{AUTHOR}*\n"
    f"📸 انستغرام: *{INSTAGRAM}*\n"
    "━━━━━━━━━━━━━━━━━━━━━━"
)

# ══════════════════════════════════════════════
#   📌 شرط متابعة الانستغرام
# ══════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📸 تابع الحساب على انستغرام", url="https://www.instagram.com/domx.54")],
        [InlineKeyboardButton(FOLLOW_CHECK_BTN, callback_data="followed")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        WELCOME_TEXT + "\n\n"
        "⚠️ *شرط الاستخدام:*\n"
        f"يجب متابعة حساب *{INSTAGRAM}* على انستغرام أولاً\n"
        "ثم اضغط الزر أدناه للمتابعة 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return WAIT_FOLLOW


# ══════════════════════════════════════════════
#   ✅ التحقق من المتابعة
# ══════════════════════════════════════════════
async def check_follow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "✅ *شكراً على متابعتك!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📱 *أدخل رقم هاتفك الجزائري*\n"
        "الصيغة المقبولة: `07XXXXXXXX` أو `213XXXXXXXXX`\n\n"
        "اكتب /cancel للإلغاء في أي وقت",
        parse_mode="Markdown",
    )
    return WAIT_PHONE


# ══════════════════════════════════════════════
#   📞 استقبال رقم الهاتف
# ══════════════════════════════════════════════
async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    if user_input.startswith("0") and len(user_input) == 10:
        my_phone = "213" + user_input[1:]
    elif user_input.startswith("213") and len(user_input) == 12:
        my_phone = user_input
    else:
        await update.message.reply_text(
            "❌ *صيغة الرقم غير صحيحة!*\n\n"
            "📌 أمثلة صحيحة:\n"
            "`0712345678`\n`213712345678`\n\n"
            "حاول مجدداً 👇",
            parse_mode="Markdown",
        )
        return WAIT_PHONE

    context.user_data["phone"] = my_phone

    await update.message.reply_text(
        f"📤 جاري إرسال رمز التحقق إلى `{user_input}`...\n"
        "⏳ الرجاء الانتظار لحظة",
        parse_mode="Markdown",
    )

    try:
        res = requests.post(
            f"{BASE_URL}/oauth2/registration",
            params={"msisdn": my_phone, "client_id": CLIENT_ID, "scope": "smsotp"},
            json={"consent-agreement": [{"marketing-notifications": False}], "is-consent": True},
            headers=HEADERS,
            timeout=15,
        )

        if res.status_code == 200:
            await update.message.reply_text(
                f"✅ *تم إرسال رمز SMS بنجاح!*\n\n"
                "📩 أرسل الرمز المكوّن من 4-6 أرقام الذي وصلك:",
                parse_mode="Markdown",
            )
            return WAIT_OTP
        else:
            await update.message.reply_text(
                "⚠️ *فشل إرسال الرمز.*\n\n"
                "تأكد من صحة الرقم ثم أعد المحاولة بـ /start",
                parse_mode="Markdown",
            )
            return ConversationHandler.END

    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "⏱️ انتهت مهلة الاتصال. تحقق من الشبكة وأعد المحاولة بـ /start",
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"receive_phone error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ غير متوقع. أعد المحاولة بـ /start")
        return ConversationHandler.END


# ══════════════════════════════════════════════
#   🔑 استقبال رمز OTP
# ══════════════════════════════════════════════
async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp      = update.message.text.strip()
    my_phone = context.user_data.get("phone")

    if not otp.isdigit():
        await update.message.reply_text("❌ الرمز يجب أن يحتوي على أرقام فقط. حاول مجدداً:")
        return WAIT_OTP

    await update.message.reply_text("🔐 جاري التحقق من الرمز... انتظر لحظة ⏳")

    try:
        token_headers = HEADERS.copy()
        token_headers["Content-Type"] = "application/x-www-form-urlencoded"

        token_res = requests.post(
            f"{BASE_URL}/oauth2/token",
            data={
                "otp": otp,
                "mobileNumber": my_phone,
                "scope": "djezzyAppV2",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "mobile",
            },
            headers=token_headers,
            timeout=15,
        )

        if token_res.status_code == 200:
            token = token_res.json().get("access_token")
            if not token:
                raise ValueError("access_token not found in response")

            await update.message.reply_text(
                "🎯 *تم التحقق بنجاح!*\n\n"
                "🔄 جاري تفعيل مكافأة 1GB...\n"
                "قد تستغرق العملية بضع ثوانٍ، انتظر 🎁",
                parse_mode="Markdown",
            )

            success = await activate_reward(token, my_phone)

            if success:
                await update.message.reply_text(
                    "🎊 *تهانينا! تمّ التفعيل بنجاح* 🎊\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "🌐 *1GB مجاناً أُضيف لحسابك* ✅\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👨‍💻 المطوّر: *{AUTHOR}*\n"
                    f"📸 انستغرام: *{INSTAGRAM}*\n\n"
                    "شكراً لاستخدامك البوت 💙\n"
                    "اكتب /start لإعادة الاستخدام",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    "❌ *فشل التفعيل*\n\n"
                    "الأسباب المحتملة:\n"
                    "• استنفدت العروض المتاحة لهذا الرقم\n"
                    "• خدمة جيزي غير متاحة حالياً\n\n"
                    "حاول مجدداً لاحقاً بـ /start",
                    parse_mode="Markdown",
                )
        else:
            await update.message.reply_text(
                "❌ *الرمز غير صحيح أو منتهي الصلاحية*\n\n"
                "اكتب /start لطلب رمز جديد",
                parse_mode="Markdown",
            )

    except requests.exceptions.Timeout:
        await update.message.reply_text("⏱️ انتهت مهلة الاتصال. أعد المحاولة بـ /start")
    except Exception as e:
        logger.error(f"receive_otp error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ غير متوقع. أعد المحاولة بـ /start")

    return ConversationHandler.END


# ══════════════════════════════════════════════
#   🎁 تفعيل المكافأة
# ══════════════════════════════════════════════
async def activate_reward(token: str, phone: str) -> bool:
    auth_headers = HEADERS.copy()
    auth_headers["Authorization"] = f"Bearer {token}"

    max_attempts = 50

    for attempt in range(1, max_attempts + 1):
        target = "2137" + "".join([str(random.randint(0, 9)) for _ in range(8)])
        logger.info(f"محاولة {attempt}/{max_attempts} → {target}")

        try:
            inv = requests.post(
                f"{BASE_URL}/api/v1/services/mgm/send-invitation/{phone}",
                headers=auth_headers,
                json={"msisdnReciever": target},
                timeout=10,
            )

            if inv.status_code == 201:
                requests.post(
                    f"{BASE_URL}/oauth2/registration",
                    params={"msisdn": target, "client_id": CLIENT_ID, "scope": "smsotp"},
                    json={"consent-agreement": [{"marketing-notifications": False}], "is-consent": True},
                    headers=HEADERS,
                    timeout=10,
                )

                time.sleep(1.5)

                act = requests.post(
                    f"{BASE_URL}/api/v1/services/mgm/activate-reward/{phone}",
                    headers=auth_headers,
                    json={"packageCode": "MGMBONUS1Go"},
                    timeout=10,
                )

                if act.status_code == 200 or "successfully" in act.text.lower():
                    logger.info(f"✅ تم التفعيل في المحاولة {attempt}")
                    return True

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout في المحاولة {attempt}")
            continue
        except Exception as e:
            logger.warning(f"خطأ في المحاولة {attempt}: {e}")
            continue

    return False


# ══════════════════════════════════════════════
#   ❌ إلغاء
# ══════════════════════════════════════════════
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚫 *تم إلغاء العملية*\n\n"
        "يمكنك البدء من جديد في أي وقت بكتابة /start 😊",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ══════════════════════════════════════════════
#   ℹ️ أمر المساعدة
# ══════════════════════════════════════════════
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *دليل الاستخدام*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• /start - بدء تفعيل 1GB\n"
        "• /cancel - إلغاء العملية الحالية\n"
        "• /help - عرض هذه القائمة\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👨‍💻 المطوّر: *{AUTHOR}*\n"
        f"📸 انستغرام: *{INSTAGRAM}*",
        parse_mode="Markdown",
    )


# ══════════════════════════════════════════════
#   🚀 تشغيل البوت
# ══════════════════════════════════════════════
def main():
    if BOT_TOKEN == "ضع_توكن_البوت_هنا":
        print("=" * 50)
        print("❌ خطأ: لم يتم تعيين توكن البوت!")
        print("   الحل: ضع التوكن في متغير البيئة BOT_TOKEN")
        print("   أو عدّل القيمة الافتراضية في الكود")
        print("=" * 50)
        return

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAIT_FOLLOW: [CallbackQueryHandler(check_follow, pattern="^followed$")],
            WAIT_PHONE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
            WAIT_OTP:    [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_command))

    print("=" * 50)
    print(f"🚀 البوت يعمل الآن | المطوّر: {AUTHOR}")
    print(f"📸 انستغرام: {INSTAGRAM}")
    print("=" * 50)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
