from __future__ import annotations

import enum
import io
import os
import pathlib
import random
import sys
import zlib
from typing import TYPE_CHECKING, Any, NamedTuple

import aiohttp
import black
import discord
import tabulate

if TYPE_CHECKING:
    from ..main import JDBot


async def google_tts(bot: JDBot, text: str) -> discord.File:
    mp3_fp = io.BytesIO(
        await (
            await bot.session.get(
                "https://api.jdjgbot.com/api/tts",
                params={"text": text, "language": "en"},
            )
        ).read()
    )
    mp3_fp.seek(0)
    return discord.File(mp3_fp, "tts.mp3")


async def latin_google_tts(bot: JDBot, text: str) -> discord.File:
    mp3_fp = io.BytesIO(
        await (
            await bot.session.get(
                "https://api.jdjgbot.com/api/tts",
                params={"text": text, "language": "la"},
            )
        ).read()
    )
    mp3_fp.seek(0)
    return discord.File(mp3_fp, "latin_tts.mp3")


def reference(message) -> discord.MessageReference | None:
    reference = message.reference
    if reference and isinstance(reference.resolved, discord.Message):
        return reference.resolved.to_reference()

    return None


#: Address pairs used for RRGG, BB00 values.
_addr_pairs = [
    ("8107EC20", "8107EC22"),
    ("8107EC28", "8107EC2A"),
    ("8107EC38", "8107EC3A"),
    ("8107EC40", "8107EC42"),
    ("8107EC50", "8107EC52"),
    ("8107EC58", "8107EC5A"),
    ("8107EC68", "8107EC6A"),
    ("8107EC70", "8107EC72"),
    ("8107EC80", "8107EC82"),
    ("8107EC88", "8107EC8A"),
    ("8107EC98", "8107EC9A"),
    ("8107ECA0", "8107ECA2"),
]


def _colored_addr_pair(addr1: str, addr2: str) -> str:
    r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    return f"{addr1} {r:02X}{g:02X}\n{addr2} {b:02X}00"


def cc_generate() -> str:
    return "\n".join(_colored_addr_pair(*addrs) for addrs in _addr_pairs)


async def post(bot: JDBot, code: str) -> str:
    paste_body = {
        "title": "JDBot Paste",
        "content": code,
        "description": "posted from jdbot",
        "text_colour": "#FFFFFF",
        "background_colour": "#000000",
        "embed_colour": "#FFFFFF",
    }

    async with await bot.session.post(
        "https://api.senarc.net/paste",
        json=paste_body,
        headers={"accept": "application/json", "Content-Type": "application/json"},
    ) as response:
        json: dict = await response.json()
        return json.get("url")


async def get_paste(bot: JDBot, paste_id: str):
    async with await bot.session.get(
        f"https://api.senarc.net/bin/{paste_id}", headers={"accept": "application/json", "headless": "true"}
    ) as response:
        json: dict = await response.json()
        return json.get("content")


def groupby(iterable: list[Any], count: int) -> list[list[Any]]:
    return [iterable[i : i + count] for i in range(0, len(iterable), count)]


def npm_create_embed(data: dict) -> discord.Embed:
    e = discord.Embed(title=f"Package information for **{data.get('name')}**")
    e.add_field(
        name="**Latest Version:**", value=f"```py\n{data.get('latest_version', 'None Provided')}```", inline=False
    )
    e.add_field(name="**Description:**", value=f"```py\n{data.get('description', 'None Provided')}```", inline=False)
    formatted_author = ""

    if isinstance(data.get("authors"), list):
        for author_data in data["authors"]:
            formatted_author += f"Email: {author_data.get('email', 'None Provided')}\nName: {author_data['name']}\n\n"

    else:
        formatted_author += f"Email: {data['authors'].get('email', 'None Provided')}\n{data['authors']['name']}"

    e.add_field(name="**Author:**", value=f"```yaml\n{formatted_author}```", inline=False)
    e.add_field(name="**License:**", value=f"```\n{data.get('license', 'None Provided')}```", inline=False)
    dependencies = []
    for lib, min_version in data.get("dependencies", {}).items():
        dependencies.append([lib, min_version])

    e.add_field(
        name="Dependencies:",
        value=f"```py\n{tabulate.tabulate(dependencies, ['Library', 'Minimum version'])}```",
        inline=False,
    )
    if data.get("next_version", "None Provided"):
        e.add_field(name="**Upcoming Version:**", value=f"```py\n{data.get('next_version', 'None Provided')}```")

    return e


def get_required_npm(data) -> dict:
    latest = data["dist-tags"]["latest"]
    npm_next = data["dist-tags"].get("next")
    version_data = data["versions"][latest]
    name = version_data["name"]
    description = version_data["description"]
    authors = data.get("author", data.get("maintainers"))
    npm_license = version_data.get("license")
    _dependencies = version_data.get("dependencies", {})
    dependencies = {}
    for lib, ver in _dependencies.items():
        dependencies[lib] = ver.strip("^")
    return {
        "latest_version": latest,
        "next_version": npm_next,
        "name": name,
        "description": description,
        "authors": authors,
        "license": npm_license,
        "dependencies": dependencies,
    }


def formatter(code, boolean):
    src = code
    mode = black.Mode(line_length=120) if boolean else black.Mode()
    dst = black.format_str(src, mode=mode)
    black.dump_to_file = lambda *args, **kwargs: None
    return dst


def linecount() -> str:
    prefix = sys.prefix.replace("\\", "/")
    to_ignore = (str(prefix.split("/")[-1]), "src") if str(prefix) != str(sys.base_prefix) else "src"

    p = pathlib.Path("./")
    im = cm = cr = fn = cl = ls = fc = 0
    for f in p.rglob("*.py"):
        if f.is_dir() or str(f).startswith(to_ignore):
            continue
        fc += 1
        with f.open() as of:
            for l in of.readlines():
                l = l.strip()
                if l.startswith("class "):
                    cl += 1
                elif l.startswith("def"):
                    fn += 1
                elif l.startswith("async def"):
                    cr += 1
                elif l.startswith(("from", "import")):
                    im += 1
                if "#" in l:
                    cm += 1
                ls += 1

    return f"Files: {fc}\nLines: {ls:,}\nClasses: {cl}\nFunctions: {fn}\nCoroutines: {cr}\nComments: {cm:,}\nImports: {im:,}"


# will require a better name and variables down below
class RtfmObject(NamedTuple):
    name: str
    url: str

    def __str__(self) -> str:
        return self.name


async def rtfm(bot: JDBot, url: str) -> list[RtfmObject]:
    # wip
    async with await bot.session.get(f"{url}objects.inv") as response:
        lines = (await response.read()).split(b"\n")

    first_10_lines = lines[:10]
    first_10_lines = [n for n in first_10_lines if not n.startswith(b"#")]

    lines = first_10_lines + lines[10:]
    joined_lines = b"\n".join(lines)
    full_data = zlib.decompress(joined_lines)
    normal_data = full_data.decode()
    new_list = normal_data.split("\n")

    results = []
    for x in new_list:
        try:
            name, python_type, number, fragment, *label = x.split(" ")
            # fixes shadowing tested with print(name, type, _)
            # ('discord.Activity.emoji', 'py:attribute', '1')

            text = " ".join(label)

            if text != "-":
                label = text

            else:
                label = name

        except:
            continue

        fragment = fragment.replace("$", name)
        results.append(RtfmObject(label, url + fragment))

    return results


async def asset_converter(ctx, assets):
    assets = list(assets)
    attachments = ctx.message.attachments

    if not attachments and not assets:
        assets.append(ctx.author)

    images = []

    for attachment in attachments:
        if attachment.content_type in ("image/png", "image/jpeg", "image/gif", "image/webp"):
            images.append(attachment)

    for asset in assets:
        if isinstance(asset, discord.PartialEmoji):
            images.append(asset)

        if isinstance(asset, (discord.User, discord.Member)):
            avatar = asset.display_avatar
            images.append(avatar)

        if isinstance(asset, aiohttp.ClientResponse):
            if asset.content_type in ("image/png", "image/jpeg", "image/gif", "image/webp"):
                images.append(asset)

        print(type(asset))

    if not images:
        images.append(ctx.author.display_avatar)

    return images[:10]


class TemperatureReadings(NamedTuple):
    celsius: float
    fahrenheit: float
    kelvin: float
    rankine: float


class Temperature(enum.Enum):
    celsius = "Celsius"
    fahrenheit = "Fahrenheit"
    kelvin = "Kelvin"
    rankine = "Rankine"

    def convert_to(self, value: float) -> TemperatureReadings:
        match self:
            case Temperature.celsius:
                c = value
                k = c + 273.15
                f = (c * 1.8) + 32
                r = f + 459.67

            case Temperature.fahrenheit:
                f = value
                c = (f - 32) * 0.5556
                k = c + 273.15
                r = f + 459.67

            case Temperature.kelvin:
                k = value
                c = k - 273.15
                f = (c * 1.8) + 32
                r = f + 459.67

            case Temperature.rankine:
                r = value
                f = r - 459.67
                c = (f - 32) * 0.5556
                k = c + 273.15

        return TemperatureReadings(round(c, 1), round(f, 1), round(k, 1), round(r, 1))


class SpeedReadings(NamedTuple):
    miles: float
    kilometers: float
    meters: float
    feet: float
    megameters: float
    light: float


class Speed(enum.Enum):
    miles = "Miles"
    kilometers = "Kilometers"
    meters = "Meters"
    feet = "Feet"
    megameters = "Megameters"
    light = "Light Speed"

    def convert_to(self, value: float) -> SpeedReadings:
        match self:
            case Speed.miles:
                miles = value
                kilometers = 1.609344 * miles
                meters = kilometers * 1000
                feet = 5280 * miles
                megameters = kilometers / 1000
                light = meters / 299792458
                # https://en.wikipedia.org/wiki/Speed_of_light

            case Speed.kilometers:
                kilometers = value
                meters = kilometers * 1000
                miles = kilometers / 1.609344
                feet = 5280 * miles
                megameters = kilometers / 1000
                light = meters / 299792458

            case Speed.meters:
                meters = value
                kilometers = meters / 1000
                megameters = kilometers / 1000
                light = meters / 299792458
                miles = kilometers / 1.609344
                feet = 5280 * miles

            case Speed.feet:
                feet = value
                miles = feet / 5280
                kilometers = miles * 1.609344
                meters = kilometers * 1000
                megameters = kilometers / 1000
                light = meters / 299792458

            case Speed.megameters:
                megameters = value
                kilometers = megameters * 1000
                meters = kilometers * 1000
                light = meters / 299792458
                miles = kilometers / 1.609344
                feet = 5280 * miles

            case Speed.light:
                light = value
                meters = light * 299792458
                kilometers = meters / 1000
                miles = kilometers / 1.609344
                feet = 5280 * miles
                megameters = kilometers / 1000

        return SpeedReadings(
            round(miles, 2),
            round(kilometers, 2),
            round(meters, 2),
            round(feet, 2),
            round(megameters, 2),
            round(light, 2),
        )


class InvalidateType(enum.IntEnum):
    everywhere = 0
    guild = 1
    dm = 2
    channel = 3
