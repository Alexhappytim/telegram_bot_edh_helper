import aiohttp as aiohttp
import requests
import random


card_list = requests.get(f"https://api.scryfall.com/catalog/card-names/").json()
data_card_list = card_list["data"]
count_card = len(data_card_list)


async def get_response(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()


async def get_rulings(url):
    response = await get_response(url)
    ret = ""
    for i in response["data"]:
        if i["source"] == "wotc":
            ret += i["comment"] + "\n\n"
    return ret


async def get_card(card):
    """На вход получает название карты строкой,
     если есть точное совпадение возвращает список формата ["card", d], где d - словарь с данными о карте.
     Иначе ["list", d], где d словарь, d["data"] - список подходящий карт"""
    res = await get_response(f"""https://api.scryfall.com/cards/named?fuzzy={card.replace(" ", "+")}""")
    ret = [0, 0]
    if res["object"] == "error":
        ret[0] = "list"
        ret[1] = await get_response(f"""https://api.scryfall.com/cards/autocomplete?q={card.replace(" ", "+")}""")
    else:
        ret[0] = "card"
        if 'card_faces' in res:
            spis_json = []
            new_json = {}
            for i in res:
                if i != 'card_faces':
                    new_json[i] = res[i]
            for i in res['card_faces']:
                card = new_json.copy()
                for j in i:
                    card[j] = i[j]
                spis_json.append(card)
            ret[1] = spis_json
        else:
            ret[1] = [res]
    return ret


def random_card():
    return data_card_list[random.randrange(count_card)]


def one_ot_two(card):
    if 'card_faces' in card[1]:
        return
