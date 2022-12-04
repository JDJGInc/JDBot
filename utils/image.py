import textwrap
from io import BytesIO

import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageSequence

font = ImageFont.truetype("assets/fonts/verdana_edited.ttf", 35)
# should be able to place it here


def call_text(text) -> BytesIO:

    text = textwrap.fill(text, 33)
    f = BytesIO()

    with Image.open("assets/images/calling_template.jpg") as image:

        draw = ImageDraw.Draw(image)
        draw.text((5, 5), text, font=font, fill="black")

        image.save(f, "PNG")

    f.seek(0)
    return f


def gadget(text) -> BytesIO:

    text = textwrap.fill(text, 30)
    f = BytesIO()

    with Image.new("RGBA", (600, 800), "white") as canv:
        with Image.open("assets/images/gadget.png") as image:

            resized = image.resize((600, 600))
            canv.paste(resized, (0, 200))

            draw = ImageDraw.Draw(canv)
            draw.text((5, 5), text, font=font, fill="black")

            canv.save(f, "PNG")

    f.seek(0)
    return f


def invert(image) -> BytesIO:

    wrapped_image = BytesIO(image)
    f = BytesIO()

    frames = []
    durations = []

    with Image.open(wrapped_image) as img:
        for frame in ImageSequence.Iterator(img):
            durations.append(frame.info.get("duration", 50))
            frame = frame.convert("RGB")
            inverted = ImageOps.invert(frame)
            frames.append(inverted)

    if len(frames) < 2:
        frames[0].save(f, format="PNG")
        f.seek(0)
        file = discord.File(f, "inv.png")

    else:
        frames[0].save(f, format="GIF", append_images=frames[1:], save_all=True, duration=durations, disposal=2)
        f.seek(0)
        file = discord.File(f, "inv.gif")

    return file
