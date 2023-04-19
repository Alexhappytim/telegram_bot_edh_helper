import logging
from telegram.ext import Application, MessageHandler, filters, \
    ConversationHandler
from config import BOT_TOKEN
from telegram.ext import CommandHandler
from scryfall_api import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def echo(update, context):
    await update.message.reply_text(
        f"Я получил сообщение {update.message.text}")


async def start(update, context):
    await update.message.reply_text(
        "Привет, я бот который помогает Едехашникам!\n"
        "Что бы узнать список команд напиши команду /help")
    return 1


async def bot_get_card_1(update, context):
    await update.message.reply_text(
        "Введите название карты")
    return 2


async def bot_get_card_2(update, context):
    card = await get_card(update.message.text)
    if card[0] == "list":
        if card[1]["data"]:
            mes = "Найдено несколько карт, вот список:\n\n"
            for i in card[1]["data"]:
                mes += f"{i}\n"
            await update.message.reply_text(
                mes)
        else:
            await update.message.reply_text(
                "Я не нашел никаких карт, попробуйте еще")
        return 2
    else:
        await context.bot.send_photo(
            update.message.chat_id,
            card[1]["image_uris"]["normal"],
            caption=card[1]["name"]
        )
        return 1


async def bot_help(update, context):
    await update.message.reply_text(
        "Вот список команд:\n"
        "/help - вывести это сообщение\n")


async def stop(update, context):
    await update.message.reply_text("До следующего четверга!")
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [CommandHandler("help", bot_help), CommandHandler("card_info", bot_get_card_1)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                               bot_get_card_2)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
