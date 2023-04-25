from scryfall_api import *
import requests
from PIL import Image
from io import BytesIO

CARD_W = 812
CARD_H = 1124


async def mox_decklist_parse(url):
    id = url.split("/")[-1]
    response = await get_response(f"https://api.moxfield.com/v2/decks/all/{id}")
    return list(response["mainboard"].keys())


async def card_to_image(name, lang):
    cards = await get_card(name)
    if lang == "ru":
        t = await get_response(f"""https://api.scryfall.com/cards/search?q=!%22{name}%22+lang=ru&unique=prints""")
        if t["object"] != "error":
            for i in t["data"]:
                if i["image_status"] != "placeholder":
                    cards = ["1", [i]]
                    if 'card_faces' in i:
                        spis_json = []
                        new_json = {}
                        for j in i:
                            if j != 'card_faces':
                                new_json[j] = i[j]
                        for j in i['card_faces']:
                            card = new_json.copy()
                            for jj in j:
                                card[jj] = j[jj]
                            spis_json.append(card)
                        cards = ["1", spis_json]
                    else:
                        cards = ["1", [i]]
                    break
    img = []
    for card in cards[1]:
        url = card["image_uris"]["normal"]
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        width = CARD_W
        height = CARD_H
        image_width, image_height = image.size
        width_reduction_rate = width / image_width
        height_reduction_rate = height / image_height
        image = image.convert("RGB")
        image = image.resize((int(image_width * width_reduction_rate), int(image_height * height_reduction_rate)))
        img.append(image)
    return img


async def decklist_to_pdf(deck, lang):
    deck_img = []
    for i in deck:
        if i.lower() not in ["forest", "island", "swamp", "plains", "mountain"]:
            t = await card_to_image(i, lang)
            for j in t:
                deck_img.append(j)
    deck_9 = []
    for i in range(0, len(deck_img), 9):
        deck_9.append(deck_img[i:min(i + 9, len(deck_img))])
    collage_list = []
    for i in deck_9:
        collage = Image.new('RGB', (2550, 3580), color=(255, 255, 255, 0))
        ii = 0
        x = 80
        y = 140
        for col in range(3):
            for row in range(3):
                if ii < len(i):
                    collage.paste(i[ii], (x, y))
                ii += 1
                y += CARD_H
            x += CARD_W
            y = 140
        collage_list.append(collage)
    collage_list[0].save("out.pdf", save_all=True, append_images=collage_list[1:])
