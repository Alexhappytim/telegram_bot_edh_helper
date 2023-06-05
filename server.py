import logging
import random
import sqlite3

from telegram.ext import Application, MessageHandler, filters, \
    ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InputMediaDocument, InputMediaPhoto
from config import BOT_TOKEN
from telegram.ext import CommandHandler

from proxy_generator import *
from scryfall_api import *
from why_lost import *
from google_api_combos import get_combos

combos = get_combos()
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

reply_keyboard = ReplyKeyboardMarkup(
    [["/help", "/card_info", "/card_rule"],
     ["/new_commander", "/triturahuesos", "/skill"],
     ["/random_combo", "/proxy","/ru_proxy"]],
    one_time_keyboard=False)


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
        reply_markup=reply_keyboard
    )

    return 1


async def games_1(update, context):
    await update.message.reply_text(
        "Правида игры такие\n"
        "Ты получишь имя, манакост и текст на карте, а нужно угадать ее характеристики \n"
        "Если угадываешь и силу и выносливость, то получаешь 2 балла,\n"
        "Если угадываешь силу или выносливость, то получаешь 1 балл,\n"
        "Если ничего, то 0. \n"
        "Баллы, которые ты потерял, зарабатывает бот\n"
        "Чтобы начать играть введите количество раундов, иначе cancel\n"
        "PS: Ответы вводить в формате 'сила/выносливость'"
    )

    return 4


async def games_1_1(update, context):
    number = update.message.text
    print(number)
    if (not number.isnumeric()) or int(float(number)) != float(number) or int(number) <= 0:
        await update.message.reply_text(
            "Введите натуральное число"
        )
        return 4
    context.user_data['answer_right'] = 0
    context.user_data['times'] = int(number)
    context.user_data['times_was'] = 0
    context.user_data['card_was'] = []
    card = random_card()
    card_test = await get_card(card)
    print(card_test)
    while 'power' not in card_test[1][0]:
        card = random_card()
        card_test = await get_card(card)
    context.user_data['card_was'].append(card)
    await update.message.reply_text(
        f"{card}\n"
        f'mana_cost: {card_test[1][0]["mana_cost"]}\n'
        f'oracle_text: {card_test[1][0]["oracle_text"]}'
    )
    return 5


async def games_1_2(update, context):
    nickname = update.effective_user.username
    params = update.message.text.split('/')
    if len(params) != 2 or (not params[0].isnumeric()) or (not params[1].isnumeric()):
        await update.message.reply_text(
            "Неправильный формат ввода"
        )
        return 5
    else:
        context.user_data['times_was'] += 1
        card_test = await get_card(context.user_data['card_was'][-1])
        strength, endurance = params
        strength_r, endurance_r = card_test[1][0]['power'], card_test[1][0]['toughness']
        if strength == strength_r and endurance == endurance_r:
            context.user_data['answer_right'] += 1
            answer = "Абсолютно верно"
        elif strength == strength_r or endurance == endurance_r:
            context.user_data['answer_right'] += 0.5
            answer = f"Неплохо, наполовину от цели. Правильно: {strength_r}/{endurance_r}"
        else:
            context.user_data['answer_right'] += 0
            answer = f"Ай-ай-ай, какой из тебя игрок. Правильно: {strength_r}/{endurance_r}"
        await update.message.reply_text(
            answer
        )
    if context.user_data['times'] == context.user_data['times_was']:
        if context.user_data['answer_right'] > context.user_data['times'] * 0.5:
            won = nickname
        elif context.user_data['answer_right'] < context.user_data['times'] * 0.5:
            won = "Бот"
        else:
            won = 'никто'
        await update.message.reply_text(
            f"Счёт:\n"
            f"Бот: {(context.user_data['times'] - context.user_data['answer_right']) * 2}\n"
            f"{nickname}: {context.user_data['answer_right'] * 2}\n"
            f"Победил: {won}",
            reply_markup=reply_keyboard
        )
        return 1
    else:
        card = random_card()
        card_test = await get_card(card)
        print(card_test)
        while card in context.user_data['card_was'] or 'power' not in card_test[1][0]:
            card = random_card()
            card_test = await get_card(card)

        await update.message.reply_text(
            f"{card}"
            f'mana_cost: {card_test[1][0]["mana_cost"]}\n'
            f'oracle_text: {card_test[1][0]["oracle_text"]}'
        )
        context.user_data['card_was'].append(card)

        return 5


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
    cards = []
    if update.message.text in list(map(str, list(range(1, 21)))) and "found_cards" in context.user_data:
        cards = await get_card(context.user_data["found_cards"][int(update.message.text) - 1])
    else:
        cards = await get_card(update.message.text)
    if cards[0] == "list":
        if cards[1]["data"]:
            text = "Найдено несколько карт, вот список:\n" \
                   "Вы можете не вводить название, а указать номер из списка\n"
            keyboard_a = [[]]
            context.user_data["found_cards"] = cards[1]["data"]
            for i in range(len(cards[1]["data"])):
                text += f"\n{i + 1}) {cards[1]['data'][i]}"
                if len(keyboard_a[0]) > 9:
                    if len(keyboard_a) == 1:
                        keyboard_a.append([])
                    keyboard_a[1].append(str(i + 1))
                else:
                    keyboard_a[0].append(str(i + 1))
            keyboard = ReplyKeyboardMarkup(keyboard_a, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(
                text,
                reply_markup=keyboard)
        else:
            await update.message.reply_text(
                "Я не нашел никаких карт, попробуйте еще")
        return 2
    else:
        flag = 1
        for card in cards[1]:
            text = f"""{card["name"]} {card["mana_cost"]}\n\n{card["type_line"]}\n{card["oracle_text"]}\n"""
            if 'power' in card:
                text += f'{card["power"]}/{card["toughness"]}'
            await context.bot.send_photo(
                update.message.chat_id,
                card["image_uris"]["normal"],
                caption=text,
                reply_markup=reply_keyboard
            )
            id_user = update.effective_user.id
            result = cur.execute(f"""SELECT {','.join(f'card_{i} TEXT' for i in card_range)} FROM users
                    WHERE nickname_id = {id_user}""").fetchall()
            was = list(result[0])
            if card["name"] not in was and flag:
                new = [card["name"], was[0], was[1], was[2], was[3]]
                cur.execute(f"""UPDATE users
                SET {','.join(f'card_{i} = "{new[i - 1]}"' for i in card_range)}
                WHERE nickname_id = {id_user}""")
                con.commit()
                flag = 0

        return 1


async def bot_get_rulings_1(update, context):
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
    return 3


async def bot_get_rulings_2(update, context):
    if update.message.text in list(map(str, list(range(1, 21)))) and "found_cards" in context.user_data:
        cards = await get_card(context.user_data["found_cards"][int(update.message.text) - 1])
    else:
        cards = await get_card(update.message.text)
    if cards[0] == "list":
        if cards[1]["data"]:
            text = "Найдено несколько карт, вот список:\n" \
                   "Вы можете не вводить название, а указать номер из списка\n"
            keyboard_a = [[]]
            context.user_data["found_cards"] = cards[1]["data"]
            for i in range(len(cards[1]["data"])):
                text += f"\n{i + 1}) {cards[1]['data'][i]}"
                if len(keyboard_a[0]) > 9:
                    if len(keyboard_a) == 1:
                        keyboard_a.append([])
                    keyboard_a[1].append(str(i + 1))
                else:
                    keyboard_a[0].append(str(i + 1))
            keyboard = ReplyKeyboardMarkup(keyboard_a, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(
                text,
                reply_markup=keyboard)
        else:
            await update.message.reply_text(
                "Я не нашел никаких карт, попробуйте еще")
        return 3
    else:
        flag = 1
        for card in cards[1]:
            text = card["name"] + "\n\n" + await get_rulings(card["rulings_uri"])
            await context.bot.send_photo(
                update.message.chat_id,
                card["image_uris"]["normal"],
                caption=text,
                reply_markup=reply_keyboard
            )
            id_user = update.effective_user.id
            result = cur.execute(f"""SELECT {','.join(f'card_{i} TEXT' for i in card_range)} FROM users
                       WHERE nickname_id = {id_user}""").fetchall()
            was = list(result[0])
            if card["name"] not in was and flag:
                new = [card["name"], was[0], was[1], was[2], was[3]]
                cur.execute(f"""UPDATE users
                   SET {','.join(f'card_{i} = "{new[i - 1]}"' for i in card_range)}
                   WHERE nickname_id = {id_user}""")
                con.commit()
                flag = 0

        return 1


async def bot_why_lost(update, context):
    await update.message.reply_text(
        random.choice(reason_why),
        reply_markup=reply_keyboard)
    return 1


async def bot_random_legend(update, context):
    t = random.choice(legends)
    cards = await get_card(t)
    for card in cards[1]:
        await context.bot.send_photo(
            update.message.chat_id,
            card["image_uris"]["normal"],
            caption=f"Случайный командир для твоей колоды: {t}",
            reply_markup=reply_keyboard
        )
    return 1


async def bot_proxy_1(update, context):
    await update.message.reply_text(
        "Введите ссылку на деклист на Moxfield")
    return 6


async def bot_proxy_2(update, context):
    await update.message.reply_text(
        "Подождите немного, это может занять до минуты")
    try:
        await decklist_to_pdf(await mox_decklist_parse(update.message.text), "en")
        await context.bot.send_document(
            update.message.chat_id,
            document=open("out.pdf", "rb"),
            filename="out.pdf",
            caption="Обрати внимание на размер карт, при печати он может отличаться"
        )
        return 1
    except Exception as ex:
        await update.message.reply_text(
            "Не является действительнной ссылкой")
        return 6


async def bot_proxy_ru_1(update, context):
    await update.message.reply_text(
        "Введите ссылку на деклист на Moxfield")
    return 7


async def bot_proxy_ru_2(update, context):
    await update.message.reply_text(
        "Подождите немного, это может занять до минуты")
    try:
        await decklist_to_pdf(await mox_decklist_parse(update.message.text), "ru")
        await context.bot.send_document(
            update.message.chat_id,
            document=open("out.pdf", "rb"),
            filename="out.pdf",
            caption="Обрати внимание на размер карт, при печати он может отличаться"
        )
        return 1
    except Exception as ex:
        await update.message.reply_text(
            "Не является действительнной ссылкой")

        return 7


async def bot_random_combo(update, context):
    comb = random.choice(combos)
    cards = []
    for i in comb[1:11]:
        if i:
            t = await get_card(i)
            for card in t[1]:
                cards.append(card["image_uris"]["normal"])
    await context.bot.send_media_group(
        chat_id=update.message.chat_id,
        media=[InputMediaPhoto(media=i) for i in cards],
        caption=f"Итак, тебе попалась комба из таких вот карт.\n\n"
                f"Для нее жолжно выполнятся условия: {comb[12]}\n\n"
                f"Работает она вот так: {comb[13]}\n\n"
                f"Как итог - {comb[14]}"
    )
    print(comb)
    return 1


async def bot_help(update, context):
    await update.message.reply_text(
        "Вот список команд:\n"
        "/help - вывести это сообщение\n"
        "/card_info - по названию карты выводит ее оракл текст\n"
        "/card_rule - по названию карты выводит рулинги этой карты\n"
        "/new_commander - дает идеи для нового командира!\n"
        "/triturahuesos - дает отмазку почему ты слил эту партию\n"
        "/skill - проверь свой уровень знания силы и выносливости существ\n"
        "/random_combo - дает случайную комбо для твоей деки!\n"
        "/proxy - по ссылке на деклист на Moxfield.com возвращает пдфку с проксями\n"
        "/ru_proxy - если есть русский принт у карты, то будет он, а не английский\n"
        "/cancel - для выхода из другой команды",
        reply_markup=reply_keyboard
    )


async def stop(update, context):
    await update.message.reply_text("До следующего четверга!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def cancel(update, context):
    await update.message.reply_text("Возвращаюсь в главное меню", reply_markup=reply_keyboard)
    return 1


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
                CommandHandler("skill", games_1),
                CommandHandler("random_combo", bot_random_combo),
                CommandHandler("proxy", bot_proxy_1),
                CommandHandler("ru_proxy", bot_proxy_ru_1),
                CommandHandler("cancel", cancel),
                ],
            2: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                 bot_get_card_2)],
            3: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                 bot_get_rulings_2)],
            4: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                 games_1_1)],
            5: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                 games_1_2)],
            6: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                 bot_proxy_2)],
            7: [CommandHandler("cancel", cancel), MessageHandler(filters.TEXT & ~filters.COMMAND,
                                                                 bot_proxy_ru_2)],
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
