import os
import discord
import time
import async_cse
import random
import cse
from discord.ext import commands
from difflib import SequenceMatcher
from discord.ext.commands.cooldowns import BucketType
import utils

from aiogifs.tenor import TenorClient, ContentFilter
from aiogifs.giphy import GiphyClient, AgeRating


class Order(commands.Cog):
    "Commands to get (images or gifs) or search results from very specific apis like tenor, giphy, and google custom search"

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):

        tenor_key = os.environ["tenor_key"]
        giphy_key = os.environ["giphy_token"]

        image_api_key = os.environ["image_api_key"]
        image_engine_key = os.environ["google_image_key"]

        self.image_client = async_cse.Search(image_api_key, engine_id=image_engine_key, session=self.bot.session)

        self.tenor_client = TenorClient(api_key=tenor_key, session=self.bot.session)
        self.giphy_client = GiphyClient(api_key=giphy_key, session=self.bot.session)

        self.google_engine = cse.Search(image_api_key, session=self.bot.session, engine_id=image_engine_key)

    @commands.cooldown(1, 30, BucketType.user)
    @commands.command(brief="searches from google images to find the closest google image")
    async def order(self, ctx, *, args=None):
        if not args:
            await ctx.send("You can't order nothing.")
            return ctx.command.reset_cooldown(ctx)

        view = utils.BasicShuffleQuestion(ctx)

        embed = discord.Embed(
            title="Order",
            color=random.randint(0, 16777215),
            description="Would you want to see results shuffled or closest to what you search ?\n\nIf you do not pick anything within 3 minutes, it will default to closest matches.",
        )

        msg = await ctx.send(
            embed=embed,
            view=view,
        )

        await view.wait()

        if view.value is None:
            await msg.edit("Finding the closest url")

        if not view.value:
            await msg.edit("Not using random results")

        if view.value:
            await msg.edit("Shuffled it is")

        time_before = time.perf_counter()

        try:
            results = await self.image_client.search(args, safesearch=True, image_search=True)

        except async_cse.search.NoResults:
            return await ctx.send("No results found :(")

        if not view.value:
            emoji_image = sorted(results, key=lambda x: SequenceMatcher(None, x.image_url, args).ratio())[-1]

        if view.value:
            emoji_image = random.choice(results)

        time_after = time.perf_counter()

        embed = discord.Embed(
            title=f"Item: {args}",
            description=f"{ctx.author} ordered a {args}",
            color=random.randint(0, 16777215),
            timestamp=ctx.message.created_at,
        )
        embed.set_author(name=f"order for {ctx.author}:", icon_url=(ctx.author.display_avatar.url))
        embed.add_field(name="Time Spent:", value=f"{int((time_after - time_before)*1000)}MS")
        embed.add_field(name="Powered by:", value="Google Images Api")

        embed.add_field(name="Image link:", value=f"[Image Link]({emoji_image.image_url})")

        embed.set_image(url=emoji_image.image_url)
        embed.set_footer(text=f"{ctx.author.id} \nCopyright: I don't know the copyright.")
        await msg.edit(
            content="Order has been logged for safety purposes(we want to make sure no unsafe search is sent)",
            embed=embed,
            view=None,
        )

        await self.bot.get_channel(855217084710912050).send(embed=embed)

    @commands.cooldown(1, 30, BucketType.user)
    @commands.command(brief="searches from tenor to find the closest image.")
    async def tenor(self, ctx, *, args=None):

        if not args:
            await ctx.send("You can't search for nothing")
            return ctx.command.reset_cooldown(ctx)

        view = utils.BasicShuffleQuestion(ctx)

        embed = discord.Embed(
            title="Tenor",
            color=random.randint(0, 16777215),
            description="Would you want to see results shuffled or closest to what you search ?\n\nIf you do not pick anything within 3 minutes, it will default to closest matches.",
        )

        msg = await ctx.send(
            embed=embed,
            view=view,
        )

        await view.wait()

        if view.value is None:
            await msg.edit("Finding the closest url")

        if not view.value:
            await msg.edit("Not using random results")

        if view.value:
            await msg.edit("Shuffled it is")

        time_before = time.perf_counter()

        safesearch_type = ContentFilter.high()
        results = await self.tenor_client.search(args, content_filter=safesearch_type, limit=10)

        if not results:
            return await ctx.send("I got no results from tenor.")

        results_media = [r for r in results.media if r]

        if not results_media:
            return await ctx.send("I got no gif results from tenor.")

        if not view.value:
            gifNearest = sorted(results_media, key=lambda x: SequenceMatcher(None, x.item_url, args).ratio())[-1]

        if view.value:
            gifNearest = random.choice(results_media)

        time_after = time.perf_counter()

        embed = discord.Embed(
            title=f"Item: {args}",
            description=f"{ctx.author} ordered a {args}",
            color=random.randint(0, 16777215),
            timestamp=ctx.message.created_at,
        )

        embed.set_author(name=f"order for {ctx.author}:", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Time Spent:", value=f"{int((time_after - time_before)*1000)}MS")
        embed.add_field(name="Powered by:", value="Tenor")

        if gifNearest.gif:
            embed.set_image(url=gifNearest.gif.url)
        else:
            embed.set_image("https://i.imgur.com/sLQzAiW.png")

        embed.set_footer(text=f"{ctx.author.id}")

        await msg.edit(
            content="Tenor has been logged for safety purposes(we want to make sure no unsafe search is sent)",
            embed=embed,
            view=None,
        )

        await self.bot.get_channel(855217084710912050).send(embed=embed)

    @commands.cooldown(1, 30, BucketType.user)
    @commands.command(brief="looks up an item from giphy.")
    async def giphy(self, ctx, *, args=None):

        if not args:
            await ctx.send("That doesn't have any value.")
            return ctx.command.reset_cooldown(ctx)

        view = utils.BasicShuffleQuestion(ctx)

        embed = discord.Embed(
            title="Giphy",
            color=random.randint(0, 16777215),
            description="Would you want to see results shuffled or closest to what you search ?\n\nIf you do not pick anything within 3 minutes, it will default to closest matches.",
        )

        msg = await ctx.send(
            embed=embed,
            view=view,
        )

        await view.wait()

        if view.value is None:
            await msg.edit("Finding the closest url")

        if not view.value:
            await msg.edit("Not using random results")

        if view.value:
            await msg.edit("Shuffled it is")

        time_before = time.perf_counter()
        safesearch_type = AgeRating.g()
        results = await self.giphy_client.search(args, rating=safesearch_type, limit=10)

        if not results:
            return await ctx.send("I got no results from giphy.")

        results_media = [r for r in results.media if r]

        if not results_media:
            return await ctx.send("I got no gif results from giphy.")

        if not view.value:
            gifNearest = sorted(results_media, key=lambda x: SequenceMatcher(None, x.url, args).ratio())[-1]

        if view.value:
            gifNearest = random.choice(results_media)

        time_after = time.perf_counter()

        embed = discord.Embed(
            title=f"Item: {args}",
            description=f"{ctx.author} ordered a {args}",
            color=random.randint(0, 16777215),
            timestamp=ctx.message.created_at,
        )

        embed.set_footer(text=f"{ctx.author.id}")

        embed.set_author(name=f"order for {ctx.author}:", icon_url=ctx.author.display_avatar.url)

        embed.add_field(name="Time Spent:", value=f"{int((time_after - time_before)*1000)}MS")
        embed.add_field(name="Powered by:", value="GIPHY")
        embed.set_image(url=f"https://media3.giphy.com/media/{gifNearest.id}/giphy.gif")

        await msg.edit(
            content="Giphy has been logged for safety purposes(we want to make sure no unsafe search is sent)",
            embed=embed,
            view=None,
        )

        await self.bot.get_channel(855217084710912050).send(embed=embed)

    @commands.cooldown(1, 30, BucketType.user)
    @commands.command(brief="can search a search result from google with safe search!")
    async def google(self, ctx, *, args=None):

        if not args:
            return await ctx.send("You can't search for nothing, as well you need a thing to lokup.")

        try:
            results = await self.google_engine.search(args, max_results=10, safe_search=True)

        except Exception as e:
            return await ctx.send(
                f"An error occured, error: {e}. Please give this to the owner. This was an error with results"
            )

        menu = utils.GoogleEmbed(results, ctx=ctx, delete_after=True)

        await menu.send()

    @commands.cooldown(1, 30, BucketType.user)
    @commands.command(brief="sends a gif of someone dancing to disco (animated)")
    async def disco(self, ctx):

        safesearch_type = ContentFilter.high()

        results = await self.tenor_client.search("disco", content_filter=safesearch_type, limit=10)

        if not results:
            return await ctx.send("I got no results from tenor.")

        results_media = [r for r in results.media if r]

        if not results_media:
            return await ctx.send("I got no gif results from tenor.")

        gifNearest = random.choice(results_media)

        embed = discord.Embed(
            title="Item: disco",
            description=f"Random Disco Gif:",
            color=random.randint(0, 16777215),
            timestamp=ctx.message.created_at,
        )

        embed.set_footer(text=f"{ctx.author.id}")

        embed.set_author(name=f"Random Disco Gif for {ctx.author}:", icon_url=ctx.author.display_avatar.url)

        embed.add_field(name="Powered by:", value="Tenor")

        if gifNearest.gif:
            embed.set_image(url=gifNearest.gif.url)
        else:
            embed.set_image("https://i.imgur.com/sLQzAiW.png")

        await ctx.send(
            content="Disco has been logged for safety purposes(we want to make sure no unsafe search is sent)",
            embed=embed,
        )

    @commands.cooldown(1, 30, BucketType.user)
    @commands.command(brief="sends a gif of someone dancing to all but disco(animated)")
    async def dance(self, ctx):

        safesearch_type = ContentFilter.high()

        results = await self.tenor_client.search("dance", content_filter=safesearch_type, limit=10)

        if not results:
            return await ctx.send("I got no results from tenor.")

        results_media = [r for r in results.media if r]

        if not results_media:
            return await ctx.send("I got no gif results from tenor.")

        gifNearest = random.choice(results_media)

        embed = discord.Embed(
            title="Item: dance",
            description=f"Random Dance Gif:",
            color=random.randint(0, 16777215),
            timestamp=ctx.message.created_at,
        )

        embed.set_footer(text=f"{ctx.author.id}")

        embed.set_author(name=f"Random Dance Gif for {ctx.author}:", icon_url=ctx.author.display_avatar.url)

        embed.add_field(name="Powered by:", value="Tenor")

        if gifNearest.gif:
            embed.set_image(url=gifNearest.gif.url)
        else:
            embed.set_image("https://i.imgur.com/sLQzAiW.png")

        await ctx.send(
            content="Dance has been logged for safety purposes(we want to make sure no unsafe search is sent)",
            embed=embed,
        )


async def setup(bot):
    await bot.add_cog(Order(bot))
