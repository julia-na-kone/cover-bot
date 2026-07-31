import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from generator import generate_cover
import config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

COURSE, NAME, SCHEDULE, STATUS = range(4)


def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_IDS:
            await update.message.reply_text("У вас нет доступа.")
            return ConversationHandler.END
        return await func(update, context)
    return wrapper


@admin_only
async def cmd_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Шаг 1/4 — Введите предмет и преподавателя:\n"
        "Пример: <i>Грузинский язык с Давидом Гогиашвили</i>",
        parse_mode="HTML",
    )
    return COURSE


async def get_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["course"] = update.message.text.strip()
    await update.message.reply_text("Шаг 2/4 — Введите имя и фамилию ученика:")
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("Пропустить", callback_data="skip")]]
    await update.message.reply_text(
        "Шаг 3/4 — Введите дни и время занятий:\n"
        "Пример: <i>Пн, Ср, Пт · 18:00</i>\n\n"
        "Или нажмите «Пропустить»",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return SCHEDULE


async def get_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["schedule"] = None
        message = update.callback_query.message
    else:
        context.user_data["schedule"] = update.message.text.strip()
        message = update.message

    keyboard = [[
        InlineKeyboardButton("Онлайн", callback_data="онлайн"),
        InlineKeyboardButton("Офлайн", callback_data="офлайн"),
    ]]
    await message.reply_text(
        "Шаг 4/4 — Выберите формат:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return STATUS


async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    course = context.user_data["course"]
    name = context.user_data["name"]
    status = query.data

    await query.message.reply_text("Генерирую обложку...")

    schedule = context.user_data.get("schedule")
    image_buf = generate_cover(course, name, status, schedule)
    await query.message.reply_photo(
        photo=image_buf,
        caption=f"{name} · {status}",
    )
    await query.message.reply_text("Готово! /create — создать ещё одну.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено. /create — начать заново.")
    return ConversationHandler.END


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/create — создать обложку для чата\n"
        "/cancel — отменить текущее действие"
    )


def main():
    app = Application.builder().token(config.BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("create", cmd_create)],
        states={
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_course)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SCHEDULE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_schedule),
                CallbackQueryHandler(get_schedule, pattern="^skip$"),
            ],
            STATUS: [CallbackQueryHandler(get_status)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", cmd_help))
    app.run_polling()


if __name__ == "__main__":
    main()
