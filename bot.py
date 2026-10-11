from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = "8569493021:AAFE6sy0FAHvNBLXcGrChmAz10KfM9_yc1A"

# Apni Telegram User ID yahan dalein (Telegram me @userinfobot se check karein)
ADMIN_ID = 7450836393

# Data structure
# candidates = {"Ram": {"votes": 10, "users": set()}, ...}
candidates = {}
active_message = {"chat_id": None, "message_id": None}


def is_admin(user_id):
    return user_id == ADMIN_ID


def build_keyboard():
    keyboard = []
    for name, data in candidates.items():
        total = data["votes"]
        btn_text = f"{name}  [{total} Votes]"
        keyboard.append(
            [InlineKeyboardButton(btn_text, callback_data=f"vote:{name}")]
        )
    return InlineKeyboardMarkup(keyboard)


async def update_panel(context: ContextTypes.DEFAULT_TYPE):
    """Jahan panel bheja gaya hai wahan buttons aur counts refresh karna"""
    if active_message["chat_id"] and active_message["message_id"]:
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=active_message["chat_id"],
                message_id=active_message["message_id"],
                reply_markup=build_keyboard(),
            )
        except Exception:
            pass


# 1. Panel bhejna: /panel
async def show_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Sirf Admin panel create kar sakta hai.")
        return

    if not candidates:
        await update.message.reply_text(
            "Abhi koi candidate nahi hai! Pehle `/add <name>` karein."
        )
        return

    msg = await update.message.reply_text(
        "🗳️ **LIVE CONTEST VOTING**\n\nNiche apne candidate ko select karke vote karein:",
        reply_markup=build_keyboard(),
        parse_mode="Markdown",
    )
    active_message["chat_id"] = msg.chat_id
    active_message["message_id"] = msg.message_id


# 2. Jab man kare naya name add karna: /add Ram
async def add_candidate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    name = " ".join(context.args).strip()
    if not name:
        await update.message.reply_text(
            "Format: `/add <name>`\nExample: `/add Ram`", parse_mode="Markdown"
        )
        return

    if name in candidates:
        await update.message.reply_text(f"`{name}` pehle se add hai.")
        return

    candidates[name] = {"votes": 0, "users": set()}
    await update.message.reply_text(f"✅ `{name}` add ho gaya!")
    await update_panel(context)


# 3. Kisi ka bhi vote khud badhana: /boost Ram 20
async def boost_votes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Format: `/boost <name> <number>`\nExample: `/boost Ram 25`",
            parse_mode="Markdown",
        )
        return

    name = context.args[0]
    try:
        count = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Vote count number hona chahiye!")
        return

    if name not in candidates:
        await update.message.reply_text(f"`{name}` list me nahi mila.")
        return

    candidates[name]["votes"] += count
    await update.message.reply_text(
        f"🚀 `{name}` ke vote me +{count} add kiya gaya. Ab total: {candidates[name]['votes']}"
    )
    await update_panel(context)


# 4. Kisi candidate ko delete karna: /remove Ram
async def remove_candidate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    name = " ".join(context.args).strip()
    if name in candidates:
        del candidates[name]
        await update.message.reply_text(f"❌ `{name}` remove ho gaya.")
        await update_panel(context)
    else:
        await update.message.reply_text(f"`{name}` nahi mila.")


# 5. Group/Channel members ke button dabane par
async def handle_user_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    target_name = query.data.split("vote:")[1]

    if target_name not in candidates:
        await query.answer("Ye option valid nahi hai!", show_alert=True)
        return

    # Check agar user pehle hi ise vote de chuka hai
    if user_id in candidates[target_name]["users"]:
        await query.answer("Aap pehle hi inko vote de chuke hain!", show_alert=True)
        return

    # Purana vote hatana agar kisi aur ko diya tha
    for name, data in candidates.items():
        if user_id in data["users"]:
            data["users"].remove(user_id)
            data["votes"] = max(0, data["votes"] - 1)

    # Naya vote add karna
    candidates[target_name]["users"].add(user_id)
    candidates[target_name]["votes"] += 1

    await query.answer(f"Aapne {target_name} ko vote diya! ✅")
    await query.edit_message_reply_markup(reply_markup=build_keyboard())


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("panel", show_panel))
    app.add_handler(CommandHandler("add", add_candidate))
    app.add_handler(CommandHandler("boost", boost_votes))
    app.add_handler(CommandHandler("remove", remove_candidate))
    app.add_handler(
        CallbackQueryHandler(handle_user_vote, pattern=r"^vote:.+$")
    )

    print("Contest & Admin Controller Bot chalu hai...")
    app.run_polling()


if __name__ == "__main__":
    main()
