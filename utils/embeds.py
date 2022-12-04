import collections
import io
import os
import random

import aiohttp
import asyncdagpi
import discord
import jeyyapi
import sr_api


async def roleinfo(ctx, role):
    role_members = collections.Counter([u.bot for u in role.members])
    role_bots = role_members[True]
    role_users = role_members[False]

    if role.tags:
        role_bot_id = role.tags.bot_id

    if not role.tags:
        role_bot_id = None

    role_time = f"{discord.utils.format_dt(role.created_at, style = 'd')}{discord.utils.format_dt(role.created_at, style = 'T')}"

    embed = discord.Embed(title=f"{role} Info:", color=random.randint(0, 16777215))
    embed.add_field(name="Mention:", value=f"{role.mention}")
    embed.add_field(name="ID:", value=f"{role.id}")
    embed.add_field(name="Created at:", value=f"{role_time}")

    embed.add_field(name="Member Count:", value=f"Bot Count : {role_bots} \nUser Count : {role_users}")

    embed.add_field(name="Position Info:", value=f"Position : {role.position} \nHoisted : {role.hoist}")

    embed.add_field(
        name="Managed Info:",
        value=f"Managed : {role.managed} \nBot : {role.is_bot_managed()} \nBot ID : {role_bot_id} \nDefault : {role.is_default()} \nBooster Role : {role.is_premium_subscriber()} \nIntegrated : {role.is_integration()} \nMentionable : {role.mentionable} ",
    )

    embed.add_field(name="Permissions:", value=f"{role.permissions.value}")
    embed.add_field(name="Color:", value=f"{role.colour}")

    embed.set_thumbnail(url="https://i.imgur.com/liABFL4.png")

    embed.set_footer(text=f"Guild: {role.guild}")

    await ctx.send(embed=embed)


async def cdn_upload(bot, bytes):
    form = aiohttp.FormData()
    form.add_field("file", bytes, content_type="application/octet-stream")
    # debate about the content_type exists, but it seems to be fine, so I will leave for now.
    resp = await bot.session.post(
        "https://cdn.jdjgbot.com/upload", data=form, headers={"Authorization": os.environ["cdn_key"]}
    )
    returned_data = await resp.json()
    url = f"https://cdn.jdjgbot.com/image/{returned_data.get('file_id')}.gif?opengraph_pass=true"
    # I have to do this opengraph pass thing because the cdn is a bit weird and doesn't like it if I don't
    # because opengraph is enabled, I have to do this.

    bot.images.append(returned_data.get("file_id"))

    return url


async def triggered_converter(url, ctx):
    sr_client = sr_api.Client(session=ctx.bot.session)
    image = sr_client.filter(option="triggered", url=str(url))

    url = await cdn_upload(ctx.bot, await image.read())

    embed = discord.Embed(color=random.randint(0, 16777215))
    embed.set_author(name=f"Triggered gif requested by {ctx.author}", icon_url=(ctx.author.display_avatar.url))
    embed.set_image(url=url)
    embed.set_footer(text="powered by some random api")
    return embed


async def headpat_converter(url, ctx):

    embed = discord.Embed(color=random.randint(0, 16777215))

    try:
        client = jeyyapi.JeyyAPIClient(session=ctx.bot.session)
        image = await client.patpat(url)

    except Exception as e:
        print(e)
        await ctx.send("the api failed on us. Please contact the Bot owner if this is a perstient issue.")

        embed.set_author(name=f"Image requested by {ctx.author}", icon_url=(ctx.author.display_avatar.url))
        embed.set_image(url=url)
        embed.set_footer(text="An Unexcepted Error Occured")
        return embed

    url = await cdn_upload(ctx.bot, image)
    # I am aware of the cdn issues, will be fixed soon
    # cdn stuff will change too cause the creator of imoog is making a better python version.
    embed.set_author(name=f"Headpat gif requested by {ctx.author}", icon_url=(ctx.author.display_avatar.url))
    embed.set_image(url=url)
    embed.set_footer(text="powered by some jeyyapi")

    return embed


def create_channel_permission(ctx):
    return ctx.author.guild_permissions.manage_channels


def clear_permission(ctx):
    if isinstance(ctx.channel, discord.TextChannel):
        return ctx.author.guild_permissions.manage_messages

    if isinstance(ctx.channel, discord.DMChannel):
        return False


async def invert_converter(url, ctx):

    embed = discord.Embed(color=random.randint(0, 16777215))

    try:
        sr_client = sr_api.Client(session=ctx.bot.session)
        source_image = sr_client.filter("invert", url=str(url))
        image = await source_image.read()
    except:
        await ctx.send("the api failed on us. Please contact the Bot owner if this is a perstient issue.")

        embed.set_author(name=f"Image requested by {ctx.author}", icon_url=(ctx.author.display_avatar.url))
        embed.set_image(url=url)
        embed.set_footer(text="An Unexcepted Error Occured")
        return embed

    url = await cdn_upload(ctx.bot, image)
    embed.set_author(name=f"Inverted Image requested by {ctx.author}", icon_url=(ctx.author.display_avatar.url))
    embed.set_image(url=url)
    embed.set_footer(text="powered by some random api")

    return embed


async def headpat_converter2(url, ctx):
    dagpi_client = asyncdagpi.Client(os.environ["dagpi_key"], session=ctx.bot.session)
    image = await dagpi_client.image_process(asyncdagpi.ImageFeatures.petpet(), str(url))

    url = await cdn_upload(ctx.bot, image.image)
    embed = discord.Embed(color=random.randint(0, 16777215))
    embed.set_author(name=f"Headpat gif requested by {ctx.author}", icon_url=(ctx.author.display_avatar.url))
    embed.set_image(url=url)
    embed.set_footer(text="powered by dagpi")
    return embed


async def invert_converter2(url, ctx):

    embed = discord.Embed(color=random.randint(0, 16777215))

    try:
        client = jeyyapi.JeyyAPIClient(session=ctx.bot.session)
        image = await client.half_invert(url)

    except:
        await ctx.send("the api failed on us. Please contact the Bot owner if this is a perstient issue.")

        embed.set_author(name=f"Image requested by {ctx.author}", icon_url=(ctx.author.display_avatar.url))
        embed.set_image(url=url)
        embed.set_footer(text="An Unexcepted Error Occured")
        return embed

    url = await cdn_upload(ctx.bot, image)

    embed.set_author(name=f"Inverted Image requested by {ctx.author}", icon_url=(ctx.author.display_avatar.url))
    embed.set_image(url=url)
    embed.set_footer(text="powered by some jeyyapi")

    return embed


async def jail_converter(url, ctx):
    dagpi_client = asyncdagpi.Client(os.environ["dagpi_key"], session=ctx.bot.session)
    image = await dagpi_client.image_process(asyncdagpi.ImageFeatures.jail(), str(url))
    url = await cdn_upload(ctx.bot, image.image)
    embed = discord.Embed(color=random.randint(0, 16777215))
    embed.set_author(name=f"Jail Image requested by {ctx.author}", icon_url=(ctx.author.display_avatar.url))
    embed.set_image(url=url)
    embed.set_footer(text="powered by dagpi")

    return embed
