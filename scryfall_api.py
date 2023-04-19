import aiohttp as aiohttp
import requests


async def get_response(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()


async def get_rulings(set, number):
    response = await get_response(f"""https://api.scryfall.com/cards/{set}/{number}/rulings""")
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
    print(res)
    ret = [0, 0]
    if res["object"] == "error":
        ret[0] = "list"
        ret[1] = await get_response(f"""https://api.scryfall.com/cards/autocomplete?q={card.replace(" ", "+")}""")
    else:
        ret[0] = "card"
        ret[1] = res
    return ret


# name = input()
# a = get_card(name)
# print(get_rulings(a[1]["set"], a[1]["collector_number"]))
