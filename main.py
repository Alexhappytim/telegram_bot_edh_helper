import logging
import random

from telegram.ext import Application, MessageHandler, filters, \
    ConversationHandler
from config import BOT_TOKEN
from telegram.ext import CommandHandler
from scryfall_api import *
from why_lost import *

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
            text = "Найдено несколько карт, вот список:\n"
            for i in card[1]["data"]:
                text += f"\n{i}"
            await update.message.reply_text(
                text)
        else:
            await update.message.reply_text(
                "Я не нашел никаких карт, попробуйте еще")
        return 2
    else:
        text = f"""{card[1]["name"]} {card[1]["mana_cost"]}\n\n{card[1]["type_line"]}\n{card[1]["oracle_text"]}\n{card[1]["power"]}/{card[1]["toughness"]}"""
        await context.bot.send_photo(
            update.message.chat_id,
            card[1]["image_uris"]["normal"],
            caption=text
        )
        return 1


async def bot_get_rulings_1(update, context):
    await update.message.reply_text(
        "Введите название карты")
    return 3


async def bot_get_rulings_2(update, context):
    card = await get_card(update.message.text)
    if card[0] == "list":
        if card[1]["data"]:
            text = "Найдено несколько карт, вот список:\n"
            for i in card[1]["data"]:
                text += f"\n{i}"
            await update.message.reply_text(
                text)
        else:
            await update.message.reply_text(
                "Я не нашел никаких карт, попробуйте еще")
        return 2
    else:
        text = card[1]["name"] + "\n\n" + await get_rulings(card[1]["rulings_uri"])
        await context.bot.send_photo(
            update.message.chat_id,
            card[1]["image_uris"]["normal"],
            caption=text
        )
        return 1


async def bot_why_lost(update, context):
    await update.message.reply_text(
        random.choice(reason_why))
    return 1


async def bot_random_legend(update, context):
    t = random.choice(legends)
    card = await get_card(t)
    await context.bot.send_photo(
        update.message.chat_id,
        card[1]["image_uris"]["normal"],
        caption=f"Случайный командир для твоей колоды: {t}"
    )
    return 1


async def bot_help(update, context):
    await update.message.reply_text(
        "Вот список команд:\n"
        "/help - вывести это сообщение\n"
        "/card_info - по названию карты выводит ее оракл текст\n"
        "/card_rule - по названию карты выводит рулинги этой карты\n"
        "/new_commander - дает идеи для нового командира!\n"
        "/triturahuesos - дает отмазку почему ты слил эту партию")


async def stop(update, context):
    await update.message.reply_text("До следующего четверга!")
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [CommandHandler("help", bot_help),
                CommandHandler("card_info", bot_get_card_1),
                CommandHandler("card_rule", bot_get_rulings_1),
                CommandHandler("new_commander", bot_random_legend),
                CommandHandler("triturahuesos", bot_why_lost),
                ],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                               bot_get_card_2)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                               bot_get_rulings_2)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
