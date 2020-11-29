from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import requests

def get_image_data(album_id, imgur_client):
    final = {}
    album = imgur_client.get_album(album_id)
    for image in album.images:
        final[image["description"]] = image["link"]
    return final

def create_card(upvotes, downvotes, name, avatar, template, colour, album_id, imgur_client):
    upvotes, downvotes = int(upvotes), int(downvotes)
    if colour == "light":
        textcolour = "#cecece"
    else:
        textcolour = "#333333"

    karma = upvotes-downvotes
    red_x1, red_y1, red_x2, red_y2 = 294, 113, 646, 159
    bar_size = [red_x2-red_x1, red_y2-red_y1]

    total_vote = int(upvotes)+int(downvotes)
    try:
        upvote_percentage = (upvotes/total_vote)
    except Exception:
        upvote_percentage = 0

    canvas = Image.new('RGBA', (700, 250), (0, 0, 0, 0))
    mask = Image.open("karma_card/mask.png")

    templates = get_image_data(album_id, imgur_client)
    try:
        template = Image.open(requests.get(templates[template], stream=True).raw)
    except (UnidentifiedImageError, KeyError):
        template = Image.open(requests.get(templates["rocky"], stream=True).raw)

    try:
        img = Image.open(requests.get(avatar, stream=True).raw)
    except Exception as e:
        img = Image.open(requests.get("https://cdn.discordapp.com/embed/avatars/1.png?size=1024", stream=True).raw)
    size = 226, 226
    img = img.resize(size)
    canvas.paste(img, (15, 12))

    canvas = Image.composite(template, canvas, mask)

    rimg_draw = ImageDraw.Draw(canvas)
    rimg_draw.rectangle((red_x1, red_y1, red_x2, red_y2), "#FF463D")

    if upvote_percentage > 0:
        green_x2 = red_x1+(bar_size[0]*upvote_percentage)
        rimg_draw.rectangle((red_x1, red_y1, green_x2, red_y2), "#70FF32")

    img = Image.open(f"karma_card/{colour}_bar_overlay.png").convert("RGBA")
    canvas.paste(img, (0, 0), img)

    img = Image.open(f"karma_card/{colour}_circle_overlay.png").convert("RGBA")
    canvas.paste(img, (0, 0), img)

###########################################################################

    if karma > 0:
        karma = "+"+str(karma)

    arial_font = ImageFont.truetype('arial.ttf', 40)
    rimg_draw.text((294, 60), f"{name} {karma}", textcolour, font=arial_font)

    karma_coords = (294, 168)
    arial_font = ImageFont.truetype('arial.ttf', 12)
    rimg_draw.text(karma_coords, f"{upvotes}", "#70FF32", font=arial_font)
    size_of_text = arial_font.getsize(f"{upvotes}")

    karma_coords = list(karma_coords)
    karma_coords[0] += size_of_text[0]
    karma_coords = tuple(karma_coords)
    rimg_draw.text(karma_coords, "|", textcolour, font=arial_font)
    size_of_text = arial_font.getsize("|")

    karma_coords = list(karma_coords)
    karma_coords[0] += size_of_text[0]
    karma_coords = tuple(karma_coords)
    rimg_draw.text(karma_coords, f"{downvotes}", "#FF463D", font=arial_font)

    canvas.save("card.png")
