from discord.ext import commands
import discord, os, itertools, re, functools, typing, random
from utils import invert_func, EmojiBasic


testers_list =  [652910142534320148,524916724223705108,168422909482762240,742214686144987150,813445268624244778,700210850513944576,717822288375971900,218481166142013450,703674286711373914]

class Test(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.command()
  async def random_number(self,ctx,*numbers: typing.Union[int,str]):
    tmp = []
    for x in numbers:
      tmp.append(x)
    numbers = tmp
    for x in numbers:
      if isinstance(x, str) :
        numbers.remove(x)
    print(numbers)
    if len(numbers) > 1:
      pass
  
  @commands.command()
  async def role_info(self,ctx,*,role:typing.Optional[discord.Role]=None):
    await ctx.send(f"Role: {role}")

  @commands.command()
  async def jokeapi(self,ctx):
    jokeapi_grab=await self.client.session.get("https://v2.jokeapi.dev/joke/Programming,Miscellaneous,Pun,Spooky,Christmas?blacklistFlags=nsfw,religious,political,racist,sexist,explicit&type=single")
    await ctx.send(await jokeapi_grab.json())

  @commands.command()
  async def emoji_id(self,ctx,*, emoji: EmojiBasic=None):
    if emoji:
      embed = discord.Embed(description=f" Emoji ID: {emoji.id}",color=random.randint(0, 16777215))
      embed.set_image(url=emoji.url)
      await ctx.send(embed=embed)

    else:
      await ctx.send("Not a valid emoji id.")

  @jokeapi.error
  async def jokeapi_error(self,ctx,error):
    await ctx.send(error)

  @commands.command(brief="this command will error by sending no content")
  async def te(self,ctx):
    await ctx.send("")

  async def cog_check(self, ctx):
    return ctx.author.id in testers_list
  
  @commands.command(brief="a command to email you(work in progress)",help="This command will email your email, it will automatically delete in guilds, but not in DMs(as it's not necessary")
  async def email(self,ctx,*args):
    print(args)
    await ctx.send("WIP")

  @commands.command(brief="a command that can scan urls(work in progress), and files",help="please don't upload anything secret or send any secret url thank you :D")
  async def scan(self,ctx, *, args = None):
    await ctx.send("WIP")
    import vt
    vt_client = vt.Client(os.environ["virustotal_key"])
    used = None
    if args:
      used = True
      urls=re.findall(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",args)
      for x in urls:
        print(x)

    if len(ctx.message.attachments) > 0:
      await ctx.send("If this takes a while, it probably means it was never on Virustotal before")
      used = True
    for x in ctx.message.attachments:
      analysis = await vt_client.scan_file_async(await x.read(),wait_for_completion=True)
      object_info = await vt_client.get_object_async("/analyses/{}", analysis.id)
    
    if used:
      await ctx.send(content="Scan completed")
    await vt_client.close_async()
    
  @commands.command(brief="work in progress")
  async def invert(self,ctx):
    y = 0

    if len(ctx.message.attachments) > 0:
      for x in ctx.message.attachments:
        try:
          discord.utils._get_mime_type_for_image(await x.read())
          passes = True
        except commands.errors.CommandInvokeError:
          passes = False
        if passes is True:
          y = y + 1
          invert_time=functools.partial(invert_func,await x.read())
          file = invert_time()
          await ctx.send(file=file)
        if passes is False:
          pass

    if len(ctx.message.attachments) == 0 or y == 0:
      url = ctx.author.avatar_url_as(format="png")
      invert_time=functools.partial(invert_func,await url.read())
      file = invert_time()
      await ctx.send(file=file)

  @invert.error
  async def invert_error(self,ctx,error):
    await ctx.send(error)

def setup(client):
  client.add_cog(Test(client))