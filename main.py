# A Discord bot that analyzes OBS log files for the Alpha Gaming discord
# Contributors: Asher_The_Thrasher, Goldeneyes, Awkward Potato, Spartichaos
import os
import discord
from discord.ext import commands
from utils.keep_alive import keep_alive
from utils.config import command_prefix
from utils.config import bot_activity
# secret bot token
token = os.environ['token']
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=command_prefix, intents=intents)
client.remove_command('help')

#import cogs
for file in os.listdir("cogs"):
  if file.endswith(".py"):
      client.load_extension(f"cogs.{file[:-3]}")




@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    activity = discord.Activity(name=bot_activity, type=discord.ActivityType.listening)
    await client.change_presence(activity=activity)


keep_alive()
client.run(token)
