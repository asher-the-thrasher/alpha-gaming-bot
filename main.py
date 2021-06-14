# A Discord bot that analyzes OBS log files for the Alpha Gaming discord
# Contributors: Asher_The_Thrasher, Goldeneyes, Awkward Potato, Spartichaos

import os

from discord.ext import commands
from dotenv import load_dotenv

from cogs.log_analyzer import LogAnalyzer

# from keep_alive import keep_alive

# secret bot token
load_dotenv()
token = os.environ['token']

bot = commands.Bot(command_prefix="!")

bot.add_cog(LogAnalyzer(bot))


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


# keep_alive()
bot.run(token)
