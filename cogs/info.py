import asyncio
import base64
import contextlib
import functools
import io
import itertools
import os
import random
import re
import secrets
import textwrap
import typing
from difflib import SequenceMatcher, get_close_matches

import async_tio
import discord
import emoji
import github
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from jishaku.codeblocks import codeblock_converter

import utils
from utils import fuzzy


class Info(commands.Cog):
    """Provides information about data you are allowed to access"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        help="Gives you info about a guild",
        aliases=["server_info", "guild_fetch", "guild_info", "fetch_guild", "guildinfo"],
    )
    async def serverinfo(self, ctx, *, guild: typing.Optional[discord.Guild] = None):
        guild = guild or ctx.guild
        if not guild:
            return await ctx.send("Could not find the guild you were looking for.")

        embed = discord.Embed(title=str(guild), color=discord.Color.random(), timestamp=ctx.message.created_at)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else "https://i.imgur.com/3ZUrjUP.png")

        view = utils.GuildInfoView(ctx, guild)
        await ctx.send("Get More Information for the guild you selected", embed=embed, view=view)

    @commands.command(
        aliases=["user_info", "user-info", "ui", "whois"],
        brief="A command that gives information on users",
        help="This can work with mentions, ids, usernames, and even full names.",
    )
    async def userinfo(self, ctx, *, user: utils.SuperConverter = commands.Author):
        embed = discord.Embed(title=str(user), color=discord.Color.random(), timestamp=ctx.message.created_at)
        embed.set_image(url=user.display_avatar.url)

        view = utils.UserInfoSuper(ctx, user)
        await ctx.send("Please Note this is being upgraded to a cooler version(it is a bit broken right now)")
        await ctx.send(
            "Pick a way for Mutual Guilds to be sent to you or not if you really don't the mutualguilds",
            embed=embed,
            view=view,
        )

    @app_commands.command(description="Get info about a user", name="userinfo")
    async def userinfo_slash(
        self, interaction: discord.Interaction, user: typing.Optional[typing.Union[discord.Member, discord.User]] = None
    ):
        user = user or interaction.user
        if isinstance(user, discord.Member):
            user = await self.bot.try_member(user.guild, user.id)

        ctx = await self.bot.get_context(interaction)
        embed = discord.Embed(title=str(user), color=discord.Color.random(), timestamp=ctx.message.created_at)
        embed.set_image(url=user.display_avatar.url)

        view = utils.UserInfoSuper(ctx, user)
        await ctx.send(
            "Pick a way for Mutual Guilds to be sent to you or not if you really don't the mutualguilds",
            embed=embed,
            view=view,
        )

    @commands.command(brief="Uploads your emojis into a Senarc Bin link")
    async def look_at(self, ctx):
        if isinstance(ctx.message.channel, discord.TextChannel):
            message_emojis = " ".join(f"{x}\n" for x in ctx.guild.emojis)
            paste = await utils.post(self.bot, message_emojis)
            await ctx.send(paste)
        elif isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("We can't use that in DMS as it takes emoji regex and puts it into a paste.")

    @commands.command(help="Gives the id of the current guild or DM if you are in one.")
    async def guild_get(self, ctx):
        await ctx.send(ctx.guild.id if isinstance(ctx.channel, discord.TextChannel) else ctx.channel.id)

    @commands.command(brief="A command to tell you the channel id", aliases=["GetChannelId"])
    async def this(self, ctx):
        await ctx.send(ctx.channel.id)

    @commands.command(brief="Gives you mention info don't abuse(doesn't mention tho)")
    async def mention(self, ctx, *, user: utils.SuperConverter = commands.Author):
        await ctx.send(
            f"Discord Mention: {user.mention} \nRaw Mention: {discord.utils.escape_mentions(user.mention)}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.cooldown(1, 30, BucketType.user)
    @commands.command(help="Fetch invite details")
    async def fetch_invite(self, ctx, *invites: typing.Union[discord.Invite, str]):
        if not invites:
            await ctx.send("Please get actual invites to attempt grab")
            ctx.command.reset_cooldown(ctx)
            return

        menu = utils.InviteInfoEmbed(invites, ctx=ctx, delete_after=True)
        await menu.send()

        if len(invites) > 50:
            await ctx.send(
                "Reporting using more than 50 invites in this command. This is to prevent ratelimits with the api."
            )
            jdjg = await self.bot.try_user(168422909482762240)
            await self.bot.support_webhook.send(
                f"{jdjg.mention}.\n{ctx.author} causes a ratelimit issue with {len(invites)} invites"
            )

    @commands.command(brief="Gives info about a file")
    async def file(self, ctx):
        if not ctx.message.attachments:
            await ctx.send("No file submitted")
            return

        embed = discord.Embed(title="Attachment info", color=discord.Color.random())
        for a in ctx.message.attachments:
            embed.add_field(name=f"ID: {a.id}", value=f"[{a.filename}]({a.url})")
        embed.set_footer(text="Check on the url/urls to get a direct download to the url.")
        await ctx.send(embed=embed, content="That's good")

    @commands.command(
        brief="A command to get the avatar of a user",
        help="Using the userinfo technology it now powers avatar grabbing.",
        aliases=["pfp", "av"],
    )
    async def avatar(self, ctx, *, user: utils.SuperConverter = commands.Author):
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f"{user.name}'s avatar:", icon_url=user.display_avatar.url)
        embed.set_image(url=user.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.command(brief="This is a way to get the nearest channel.")
    async def find_channel(self, ctx, *, args=None):
        if not args:
            return await ctx.send("Please specify a channel")

        if isinstance(ctx.channel, discord.TextChannel):
            channel = discord.utils.get(ctx.guild.channels, name=args)
            if channel:
                await ctx.send(channel.mention)
            else:
                await ctx.send("Unfortunately we haven't found anything")
        elif isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("You can't use it in a DM.")

    @commands.command(brief="A command to get the closest user.")
    async def closest_user(self, ctx, *, args=None):
        if not args:
            return await ctx.send("Please specify a user")

        if not self.bot.users:
            return await ctx.send("There are no users cached :(")

        userNearest = discord.utils.get(self.bot.users, name=args)
        user_nick = discord.utils.get(self.bot.users, display_name=args)

        if userNearest is None:
            userNearest = max(self.bot.users, key=lambda x: SequenceMatcher(None, x.name, args).ratio())

        if user_nick is None:
            user_nick = max(self.bot.users, key=lambda x: SequenceMatcher(None, x.display_name, args).ratio())

        if isinstance(ctx.channel, discord.TextChannel):
            member_list = [x for x in ctx.guild.members if x.nick]
            nearest_server_nick = max(member_list, key=lambda x: SequenceMatcher(None, x.nick, args).ratio())
        else:
            nearest_server_nick = "You unfortunately don't get the last value(a nickname) as it's a DM."

        await ctx.send(f"Username: {userNearest} \nDisplay name: {user_nick} \nNickname: {nearest_server_nick}")

    @commands.command(help="Gives info on default emoji and custom emojis", name="emoji")
    async def emoji_info(
        self,
        ctx: commands.Context,
        *,
        emojis: typing.Annotated[utils.EmojiConverter.ConvertedEmojis, utils.EmojiConverter],
    ):
        menu = utils.EmojiInfoEmbed(emojis.all, ctx=ctx, delete_after=True)
        await menu.send()

    @commands.command(brief="Gives info on emoji_id and emoji image.")
    async def emoji_id(
        self,
        ctx,
        *,
        emoji: typing.Optional[typing.Union[discord.PartialEmoji, discord.Message, utils.EmojiBasic]] = None,
    ):
        if isinstance(emoji, discord.Message):
            emoji_message = emoji.content
            emoji = None

            with contextlib.suppress(commands.CommandError, commands.BadArgument):
                emoji = await utils.EmojiBasic.convert(
                    ctx, emoji_message
                ) or await commands.PartialEmojiConverter().convert(ctx, emoji_message)

        if emoji:
            embed = discord.Embed(description=f"Emoji ID: {emoji.id}", color=discord.Color.random())
            embed.set_image(url=emoji.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Not a valid emoji id.")

    @commands.command()
    async def fetch_content(self, ctx, *, args=None):
        if not args:
            return await ctx.send("Please send actual text")

        args = discord.utils.escape_mentions(args)
        args = discord.utils.escape_markdown(args, as_needed=False, ignore_links=False)

        for x in ctx.message.mentions:
            args = args.replace(x.mention, f"\\{x.mention}")

        emojis = emoji.emoji_lis(args)
        emojis_return = [d["emoji"] for d in emojis]

        for x in emojis_return:
            args = args.replace(x, f"\\{x}")

        for x in re.findall(r":\w*:\d*", args):
            args = args.replace(x, f"\\{x}")

        await ctx.send(args, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(brief="Gives info about a role.", aliases=["roleinfo"])
    async def role_info(self, ctx, *, role: typing.Optional[discord.Role] = None):
        if role:
            await utils.roleinfo(ctx, role)
        else:
            await ctx.send("The role you wanted was not found.")


class DevTools(commands.Cog):
    """Helpful commands for developers in general"""

    def __init__(self, bot):
        self.bot = bot
        self.TOKEN_RE = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{26}\w{1}")
        self.pool = self.bot.db

    async def cog_load(self):
        github_token = os.environ.get("github_token")
        self.github = await github.GHClient(username="JDJGBot", token=github_token)
        self.rtfm_dictionary = sorted(await self.bot.db.fetch("SELECT * FROM RTFM_DICTIONARY"))
        self.tio = async_tio.Tio(session=self.bot.session)

        self.invalidation_config = [
            utils.InvalidationConfig(record.entity_id, record.entity_type, self.bot)
            for record in await self.bot.db.fetch("SELECT * FROM invalidation_config")
        ]
        self.invalidation_opt_out = [
            utils.InvalidationConfig(record.entity_id, record.entity_type, self.bot)
            for record in await self.bot.db.fetch("SELECT * FROM invalidation_out")
        ]

    async def cog_unload(self):
        await self.github.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.guild.id != 1019027330779332660:
            return

        match = self.TOKEN_RE.findall(message.content)
        if match:
            gist = await self.github.create_gist(
                files=[github.File(fp="\n".join(match), filename="token.txt")],
                description="Token Detected, invalidated in process",
                public=True,
            )

            await message.channel.send(
                f"{message.author.mention} Token detected, invalidated in process.\nGist: <{gist.url}>"
            )

    @commands.command(brief="Tells bot if it should invalidate token.")
    async def token_snipper(self, ctx):
        embed = discord.Embed(
            title="Token Snipper Tool",
            description="It tells the bot if it should invalidate any discord tokens sent into chat",
            color=discord.Color.random(),
            timestamp=ctx.message.created_at,
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        embed.set_image(url="https://i.imgur.com/WPExfNr.gif")
        embed.set_footer(text="This snipper snipes tokens she sees in chat.")

        await ctx.send("Going to change to a slash command with explicit permissions for some options.")

    async def rtfm_lookup(self, url=None, *, args=None):
        if not args:
            return url

        unfiltered_results = await utils.rtfm(self.bot, url)
        results = fuzzy.finder(args, unfiltered_results, key=lambda t: t[0])

        if not results:
            return f"Could not find anything with {args}."

        return results

    async def rtfm_send(self, ctx, results):
        if isinstance(results, str):
            await ctx.send(results, allowed_mentions=discord.AllowedMentions.none())
        else:
            embed = discord.Embed(color=discord.Color.random())
            results = results[:10]
            embed.description = "\n".join(f"[`{result}`]({result.url})" for result in results)
            reference = utils.reference(ctx.message)
            await ctx

    @commands.command(
        aliases=["rtd", "rtfs", "rtdm"],
        invoke_without_command=True,
        brief="A RTFM command that allows you to lookup any supported library (using selects)",
    )
    async def rtfm(self, ctx, *, args=None):
        view = utils.RtfmChoice(ctx, self.rtfm_dictionary, timeout=15.0)
        await ctx.send("Please pick a library you want to parse", view=view)
        await view.wait()
        await ctx.typing()
        results = await self.rtfm_lookup(url=view.value, args=args)
        await self.rtfm_send(ctx, results)

    @app_commands.command(description="Looks up docs", name="rtfm")
    async def rtfm_slash(
        self,
        interaction: discord.Interaction,
        library: typing.Optional[str] = None,
        query: typing.Optional[str] = None
    ) -> None:
        """Looks up docs for a library with optionally a query."""
        libraries = dict(self.rtfm_dictionary)
        library = library or libraries["master"]
        if not query:
            await interaction.response.send_message(f"Alright, let's see\n{library}")
        else:
            await interaction.response.send_message(f"Alright, let's see\n{library + query}")

    @rtfm_slash.autocomplete("library")
    async def rtfm_library_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        libraries = dict(self.rtfm_dictionary)
        all_choices = [app_commands.Choice(name=name, value=link) for name, link in libraries.items()]
        startswith = [choice for choice in all_choices if choice.name.lower().startswith(current.lower())]
        return (startswith or all_choices)[:25]

    @rtfm_slash.autocomplete("query")
    async def rtfm_query_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        url = interaction.namespace.library or dict(self.rtfm_dictionary)["master"]
        unfiltered_results = await utils.rtfm(self.bot, url)
        all_choices = [app_commands.Choice(name=result.name, value=result.url.replace(url, "")) for result in unfiltered_results]

        if not current:
            return all_choices[:25]

        filtered_results = fuzzy.finder(current, unfiltered_results, key=lambda t: t.name)
        return [app_commands.Choice(name=result.name, value=result.url.replace(url, "")) for result in filtered_results][:25]

    @rtfm_slash.error
    async def rtfm_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f"An error occurred: {error}. Please report this to my developer.", ephemeral=True)
        print(f"Error in {interaction.command}: {error}")

    def charinfo_converter(self, char: str) -> str:
        digit = f"{ord(char):x}"
        name = unicodedata.name(char, "Unicode character not found")
        return f"`\\U{digit:>08}`: {name} - {char} \N{EM DASH} <http://www.fileformat.info/info/unicode/char/{digit}>"

    @commands.command(brief="Gives you data about characters (based on R.danny's command)")
    async def charinfo(self, ctx, *, characters: str):
        if not characters:
            return await ctx.send("Please provide characters to get information about.")

        values = "\n".join(map(self.charinfo_converter, set(characters)))
        content = textwrap.wrap(values, width=2000)
        menu = utils.charinfoMenu(content, ctx=ctx, delete_after=True)
        await menu.send()

    @commands.command(brief="View the RTFM database")
    async def rtfm_view(self, ctx):
        rtfm_dictionary = dict(self.rtfm_dictionary)
        pag = commands.Paginator(prefix="", suffix="")
        for name, url in rtfm_dictionary.items():
            pag.add_line(f"{name}: {url}")
        menu = utils.RtfmEmbed(pag.pages, ctx=ctx, delete_after=True)
        await menu.send()

    @commands.command(brief="Autoformat your Python code to PEP 8")
    async def pep8(self, ctx):
        modal = utils.CodeBlockView(ctx, timeout=180.0)
        message = await ctx.send(
            "Please submit the code block. Do you want to use Black's line formatter at 120 characters (i.e., black -l 120), or just use the default (i.e., black)?",
            view=modal,
        )
        await modal.wait()

        if not modal.value:
            return await ctx.reply("You need to provide code to format.", mention_author=False)

        code = codeblock_converter(argument=modal.value)

        use_special_formatting = modal.value2 is True
        await message.edit(content="Using special formatting (120 characters)" if use_special_formatting else "Using default formatting", view=None)

        try:
            formatted_code = await asyncio.to_thread(utils.formatter, code.content, use_special_formatting)
        except Exception as e:
            return await message.edit(content=f"An error occurred: {e}")

        embed = discord.Embed(
            title="Reformatted with Black",
            description=f"Formatted code:\n\n{formatted_code}",
            color=discord.Color.random(),
        )
        embed.set_footer(text="Make sure you use Python code, otherwise it may not work properly.")
        await message.edit(embed=embed)

    @commands.command(brief="Grab your profile picture")
    async def pfp_grab(self, ctx):
        avatar = ctx.author.display_avatar
        file_extension = ".gif" if avatar.is_animated() else ".png"
        file = await avatar.to_file(filename=f"pfp{file_extension}")
        
        try:
            await ctx.send("Here's your avatar:", file=file)
        except discord.HTTPException:
            await ctx.send("Unable to send the profile picture due to file size limitations.")

    @commands.command(brief="Gives info on PyPI packages")
    async def pypi(self, ctx, *, package_name: str = None):
        if not package_name:
            return await ctx.send("Please provide a package name to get information.")

        async with self.bot.session.get(f"https://pypi.org/pypi/{package_name}/json") as response:
            if not response.ok:
                return await ctx.send(f"Could not find package **{package_name}** on PyPI.", allowed_mentions=discord.AllowedMentions.none())

            pypi_data = (await response.json())["info"]

        embed = discord.Embed(
            title=f"{pypi_data.get('name', 'N/A')} {pypi_data.get('version', 'N/A')}",
            url=pypi_data.get('release_url', 'https://pypi.org'),
            description=pypi_data.get('summary', 'No summary provided'),
            color=discord.Color.random()
        )

        embed.set_thumbnail(url="https://i.imgur.com/oP0e7jK.png")

        embed.add_field(
            name="Author Info",
            value=f"**Name:** {pypi_data.get('author', 'N/A')}\n**Email:** {pypi_data.get('author_email', 'N/A')}",
            inline=False
        )
        embed.add_field(
            name="Package Info",
            value=f"**Download URL:** {pypi_data.get('download_url', 'N/A')}\n"
                  f"**Documentation:** {pypi_data.get('docs_url', 'N/A')}\n"
                  f"**Home Page:** {pypi_data.get('home_page', 'N/A')}\n"
                  f"**Keywords:** {pypi_data.get('keywords', 'N/A')}\n"
                  f"**License:** {pypi_data.get('license', 'N/A')}",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(brief="Make a quick bot invite with 0 permissions")
    async def invite_bot(self, ctx, *, user: discord.User = commands.Author):
        if not user.bot:
            return await ctx.send("That's not a valid bot.")

        invite = discord.utils.oauth_url(client_id=user.id, scopes=("bot",))
        slash_invite = discord.utils.oauth_url(client_id=user.id)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label=f"{user.name}'s Normal Invite", url=invite, style=discord.ButtonStyle.link))
        view.add_item(discord.ui.Button(label=f"{user.name}'s Invite With Slash Commands", url=slash_invite, style=discord.ButtonStyle.link))

        await ctx.send("Invite with slash commands and the bot scope or only with a bot scope:", view=view)

    @commands.command(brief="Puts the message time as a timestamp")
    async def message_time(self, ctx):
        embed = discord.Embed(title="Message Time", color=discord.Color.random(), timestamp=ctx.message.created_at)
        embed.set_footer(text=str(ctx.message.id))
        await ctx.send(content="Message timestamp:", embed=embed)

    @commands.command(brief="Converts info about colors for you.")
    async def color(self, ctx, *, color: utils.ColorConverter = None):
        if not color:
            return await ctx.send("You need to provide a color to use.")

        await ctx.send(f"Hexadecimal: {color}\nValue: {color.value}\nRGB: {color.to_rgb()}")

    @commands.command(brief="Tells a user's creation time.")
    async def created_at(self, ctx, *, user: utils.SuperConverter = commands.Author):
        creation_info = f"{discord.utils.format_dt(user.created_at, style='D')}\n{discord.utils.format_dt(user.created_at, style='T')}"
        await ctx.send(
            f"Name: {user}\n"
            f"Mention: {user.mention} was created:\n"
            f"{creation_info}\n"
            f"Raw Version: {creation_info}",
            allowed_mentions=discord.AllowedMentions.none()
        )

    @commands.command(brief="Makes a fake user ID based on the current time.")
    async def fake_user_id(self, ctx):
        await ctx.send(f"User ID: {utils.generate_snowflake()}")

    @commands.command(brief="Gives information on snowflakes")
    async def snowflake_info(self, ctx, *, snowflake: typing.Optional[utils.ObjectPlus] = None):
        if not snowflake:
            snowflake = await utils.ObjectPlusConverter().convert(ctx, argument=str(utils.generate_snowflake()))
            await ctx.send("Using current time for snowflake information.")

        embed = discord.Embed(title="❄️ Snowflake Info:", color=discord.Color.blue())
        embed.add_field(
            name="Created At:",
            value=f"{discord.utils.format_dt(snowflake.created_at, style='D')}\n{discord.utils.format_dt(snowflake.created_at, style='T')}"
        )
        embed.add_field(name="Worker ID:", value=str(snowflake.worker_id))
        embed.add_field(name="Process ID:", value=str(snowflake.process_id))
        embed.add_field(name="Increment:", value=str(snowflake.increment_id))
        embed.set_footer(text=f"Snowflake ID: {snowflake.id}")

        await ctx.send(embed=embed)

    @commands.command(brief="Generates a fake token from the current time")
    async def fake_token(self, ctx):
        discord_object = discord.Object(utils.generate_snowflake())

        first_bit = base64.b64encode(str(discord_object.id).encode()).decode().rstrip("=")
        timestamp = int(discord_object.created_at.timestamp() - 129384000)
        second_bit = base64.standard_b64encode(timestamp.to_bytes(4, "big")).decode().rstrip("=")
        last_bit = secrets.token_urlsafe(20)

        embed = discord.Embed(
            title="Newly Generated Fake Token",
            description=f"ID: `{discord_object.id}`\n"
                        f"Created at:\n"
                        f"{discord.utils.format_dt(discord_object.created_at, style='D')}\n"
                        f"{discord.utils.format_dt(discord_object.created_at, style='T')}"
        )
        embed.add_field(name="Generated Token:", value=f"`{first_bit}.{second_bit}.{last_bit}`")
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}")

        await ctx.send("We generated a fake token:", embed=embed)

    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.command(brief="Makes a request to add a bot to the test guild")
    async def addbot(self, ctx, *, user: discord.User = commands.Author):
        if not user.bot:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Please use a **bot** ID, not a **user** ID.")

        modal = utils.AddBotView(ctx, timeout=180.0)
        message = await ctx.send("Please tell us the reason you want to add your bot to the Test Guild:", view=modal)
        await modal.wait()

        if modal.value is None:
            ctx.command.reset_cooldown(ctx)
            return await message.edit(content="Please provide a reason why you want your bot added to the guild.")

        guild = self.bot.get_guild(438848185008390158)
        member = await self.bot.try_member(guild, ctx.author.id)
        if member is None:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Test Guild Invite", url="https://discord.gg/hKn8qgCDzK", style=discord.ButtonStyle.link))
            return await message.edit(
                content="Make sure to join the guild linked soon... then rerun the command. If you are in the guild, contact the owner (listed in the owner command).",
                view=view
            )

        embed = discord.Embed(
            title="Bot Request",
            colour=discord.Colour.blurple(),
            description=f"Reason:\n{modal.value}\n\n[Invite URL]({discord.utils.oauth_url(client_id=user.id, scopes=('bot',))})",
            timestamp=ctx.message.created_at
        )

        embed.add_field(name="Author", value=f"{ctx.author} (ID: {ctx.author.id})", inline=False)
        embed.add_field(name="Bot", value=f"{user} (ID: {user.id})", inline=False)
        embed.set_footer(text=str(ctx.author.id))
        embed.set_author(name=str(user.id), icon_url=user.display_avatar.with_format("png"))

        jdjg = self.bot.get_user(168422909482762240)
        await self.bot.get_channel(852897595869233182).send(content=jdjg.mention, embed=embed)

        await ctx.reply(
            f"Your bot request has been submitted. Please note:\n"
            f"• If you leave, your bot will be kicked unless you have an alt or a friend in the guild.\n"
            f"• Your bot will be reviewed by {jdjg}.\n"
            f"• Make sure to open your DMs to JDJG so he can contact you about the bot being added.\n"
            f"• If you don't add him, your bot will be denied."
        )

    @commands.command(brief="Checks if a URL is a valid image (requires embed permissions)")
    async def image_check(self, ctx):
        await ctx.send("Please wait for Discord to process your message...")
        await asyncio.sleep(5)

        images = [e for e in ctx.message.embeds if e.type == "image"]

        if not images:
            return await ctx.send("You need to provide a URL with an image. If you did, please try again.")

        await ctx.send(f"You have {len(images)} valid image link(s) out of {len(ctx.message.embeds)} total link(s).")

    @commands.command(brief="Gives info on npm packages")
    async def npm(self, ctx, *, args=None):
        if args:
            npm_response = await self.bot.session.get(f"https://registry.npmjs.com/{args}")

            if npm_response.ok:
                npm_response = await npm_response.json()

                data = utils.get_required_npm(npm_response)
                await ctx.send(embed=utils.npm_create_embed(data))

            else:
                await ctx.send(
                    f"Could not find package **{args}** on npm.", allowed_mentions=discord.AllowedMentions.none()
                )

        else:
            await ctx.send("Please look for a library to get the info of.")

    @commands.cooldown(1, 30, BucketType.user)
    @commands.command(
        brief="runs some code in a sandbox(based on Soos's Run command)", aliases=["eval", "run", "sandbox"]
    )
    async def console(self, ctx, *, code: codeblock_converter = None):
        if not code:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to give me some code to use, otherwise I can not determine what it is.")

        if not code.language:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You Must provide a language to use")

        if not code.content:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("No code provided")

        output = await self.tio.execute(f"{code.content}", language=f"{code.language}")

        text_returned = (
            f"```{code.language}\n{output}```"
            if len(f"{output}") < 200
            else await utils.post(self.bot, code=f"{output}")
        )

        embed = discord.Embed(
            title=f"Your code exited with code {output.exit_status}", description=f"{text_returned}", color=242424
        )

        embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)

        embed.set_footer(text="Powered by Tio.run")

        await ctx.send(content="I executed your code in a sandbox", embed=embed)


async def setup(bot):
    await bot.add_cog(Info(bot))
    await bot.add_cog(DevTools(bot))