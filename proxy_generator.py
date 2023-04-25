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


async def card_to_image(name):
    cards = await get_card(name)
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


async def decklist_to_pdf(deck):
    deck_img = []
    for i in deck:
        t = await card_to_image(i)
        for j in t:
            deck_img.append(j)
    deck_9 = []
    for i in range(0, len(deck_img), 9):
        deck_9.append(deck_img[i:min(i + 9, len(deck_img) - 1)])
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
