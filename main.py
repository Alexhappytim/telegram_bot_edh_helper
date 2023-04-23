import logging
import random
import sqlite3

from telegram.ext import Application, MessageHandler, filters, \
    ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import BOT_TOKEN
from telegram.ext import CommandHandler
from scryfall_api import *
from why_lost import *

card_range = range(1, 6)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
con = sqlite3.connect('data/statist.db')
cur = con.cursor()
cur.execute(f"""CREATE TABLE IF NOT EXISTS users(
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   nickname_id INTEGER,
   {','.join(f'card_{i} TEXT' for i in card_range)});
   """)
con.commit()


async def start(update, context):
    id_user = update.effective_user.id
    result = cur.execute("""SELECT nickname_id FROM users""").fetchall()
    if (id_user,) not in result:
        cur.execute(f"""INSERT INTO users(nickname_id)
        VALUES({id_user})""")
        con.commit()
    await update.message.reply_text(
        "Привет, я бот который помогает Едехашникам!\n"
        "Что бы узнать список команд напиши команду /help",
        reply_markup=ReplyKeyboardRemove()
    )

    return 1


async def bot_get_card_1(update, context):
    id_user = update.effective_user.id
    result = cur.execute(f"""SELECT {','.join(f'card_{i} TEXT' for i in card_range)} FROM users
        WHERE nickname_id = {id_user}""").fetchall()
    was, was_str = [], '\nПрошлые запросы:\n'
    for i in list(result[0]):
        if not (i is None) and i != 'None':
            was.append(i)
    if len(was) != 0:
        was_str += '\n'.join(i for i in was)
        keyboard = ReplyKeyboardMarkup([was], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "Введите название карты" + was_str,
            reply_markup=keyboard
        )

    else:
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
        text = f"""{card[1]["name"]} {card[1]["mana_cost"]}\n\n{card[1]["type_line"]}\n{card[1]["oracle_text"]}\n"""
        if 'power' in card[1]:
            text += f'{card[1]["power"]}/{card[1]["toughness"]}'
        await context.bot.send_photo(
            update.message.chat_id,
            card[1]["image_uris"]["normal"],
            caption=text,
            reply_markup=ReplyKeyboardRemove()
        )
        id_user = update.effective_user.id
        result = cur.execute(f"""SELECT {','.join(f'card_{i} TEXT' for i in card_range)} FROM users
                WHERE nickname_id = {id_user}""").fetchall()
        was = list(result[0])
        if card[1]["name"] not in was:
            new = [card[1]["name"], was[0], was[1], was[2], was[3]]
            cur.execute(f"""UPDATE users
            SET {','.join(f'card_{i} = "{new[i - 1]}"' for i in card_range)}
            WHERE nickname_id = {id_user}""")
            con.commit()

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
                "Я не нашел никаких карт, попробуйте еще"
            )
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
        "/triturahuesos - дает отмазку почему ты слил эту партию"
    )


async def stop(update, context):
    await update.message.reply_text("До следующего четверга!", reply_markup=ReplyKeyboardRemove())
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
