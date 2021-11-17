from discord.ext import commands
import discord, re
from better_profanity import profanity

class Global(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command(brief = "wait for it to release")
  async def global_wip(self, ctx):
    await ctx.send("currently global chat is WIP for JDBot.")

  @commands.command(brief = "makes a global chat example message from your message", aliases = ["test_gc", "generate_message"])
  async def test_globalchat(self, ctx, *, args = None):

    args = args or "Test Content"

    for x in re.findall(r'<@!?([0-9]{15,20})>', args):
      user = await self.bot.try_user(int(x))
      args = args.replace(f"{re.match(rf'<@!?({x})>', args).group()}", f"@{user}")

    args = await commands.clean_content().convert(ctx, args)
    args = profanity.censor(args, censor_char = "#")
    
    embed = discord.Embed(title=f"{ctx.guild}",
    description = f"{args}", color = 15428885, timestamp = ctx.message.created_at)

    embed.set_author(name=f"{ctx.author}", icon_url = ctx.author.display_avatar.url)

    if ctx.guild: embed.set_thumbnail(url = ctx.guild.icon.url if ctx.guild.icon else "https://i.imgur.com/3ZUrjUP.png")

    if not ctx.guild: embed.set_thumbnail(url = "https://i.imgur.com/3ZUrjUP.png")
    
    await ctx.send(f"Here's what it would look like in Global Chat!", embed = embed)

  

def setup(bot):
  bot.add_cog(Global(bot))