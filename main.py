import os
import logging
import discord

from urllib.parse import quote_plus as urlencode

from aiohttp import ClientResponseError
from asyncio import TimeoutError
from discord import Message, Embed, Colour
#from discord.ext.commands import Cog

from RateLimit import RateLimiter

#secret bot token
token = os.environ['token']

#
client = discord.Client()
limiter = None
cooldown = 5.0

_analysis_colour = 0x5a7474
_potato = '🥔'
_log_download_failed = '❗️'
_log_analyser_failed = '❌'

_filtered_log_needles = ('obs-streamelements.dll', 'ftl_stream_create')
_log_hosts = ('https://obsproject.com/logs/', 'https://hastebin.com/', 'https://pastebin.com/')

def __init__(bot, config):
  limiter = RateLimiter(config.get('cooldown', 20.0))
  bot = bot

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(msg: Message):
    if msg.author.bot: return; #Checks to see if the message is a bot message
    if not msg.attachments and not any(lh in msg.content for lh in _log_hosts):
        print("Not a log file")
        #await msg.channel.send("Not a log file")
        return
    
    tempText = msg.content.replace("https://hastebin.com/","")
    tempText.replace("https://obsproject.com/logs/", "")
    tempText.replace('https://pastebin.com/',"")

    if tempText=="": 
      print("Not a log file - Empty log") #Ensures it's not an empty log
      return


    #await msg.channel.send('it do be a log file')
    print("Message has log file: " + str(msg.content))
    
    # list of candidate tuples consisting of (raw_url, web_url)
    log_candidates = []
    # message attachments
    for attachment in msg.attachments:
        if attachment.url.endswith('.txt'):
            # collisions are possible here, but unlikely, we'll see if it becomes a problem
            #await msg.channel.send("it also do be a txt file")

            if not limiter.is_limited(attachment.filename):
                log_candidates.append(attachment.url)
            else:
                print(f'{msg.author} attempted to upload a rate-limited log.')

    # links in message
    for part in [p.strip() for p in msg.content.split()]:
        if any(part.startswith(lh) for lh in _log_hosts):
            if 'obsproject.com' in part:
                url = part
            elif 'hastebin.com' in part:
                hastebin_id = part.rsplit('/', 1)[1]
                if not hastebin_id:
                    continue
                url = f'https://hastebin.com/raw/{hastebin_id}'
            elif 'pastebin.com' in part:
                pastebin_id = part.rsplit('/', 1)[1]
                if not pastebin_id:
                    continue
                url = f'https://pastebin.com/raw/{pastebin_id}'
            else:
                continue
    
    if not log_candidates:
        return

    if len(log_candidates) > 3:
        print('Too many log url candidates, limiting to first 3')
        log_candidates = log_candidates[:3]

    async def react(emote):
        try:
            await msg.add_reaction(emote)
        except Exception as e:
            print(f'Adding reaction failed with "{repr(e)}')

    for log_url in log_candidates:
        # download log for local analysis
        try:
            log_content = await download_log(log_url)
            break
        except ValueError:  # not a valid OBS log
            continue
        except (ClientResponseError, TimeoutError):  # file download failed
            print(f'Failed retrieving log from "{log_url}"')
            await react(_log_download_failed)
        except Exception as e:  # catch everything else
            print(f'Unhandled exception when downloading log: {repr(e)}')
    else:
        return

    async with msg.channel.typing():
        log_analysis = None
        try:
            # fetch log analysis from OBS analyser
            log_analysis = await fetch_log_analysis(log_url)
        except ValueError:
            print(f'Analyser result for "{log_url}" is invalid.')
        except ClientResponseError:  # file download failed
            print(f'Failed retrieving log analysis from "{log_url}"')
        except TimeoutError:  # analyser failed to respond
            print(f'Analyser timed out for log file "{log_url}"')
        except Exception as e:  # catch everything else
            print(f'Unhandled exception when analysing log: {repr(e)}')
        finally:
            if not log_analysis:
                return await react(_log_analyser_failed)

        anal_url = f'https://obsproject.com/tools/analyzer?log_url={urlencode(log_url)}'
        embed = Embed(colour=Colour(0x5a7474), url=anal_url)

        def pretty_print_messages(msgs):
            ret = []
            for _msg in msgs:
                ret.append(f'- {_msg}')
            return '\n'.join(ret)

        if log_analysis['critical']:
          embed.add_field(name="🛑 Critical",
            value=pretty_print_messages(log_analysis['critical']))
        if log_analysis['warning']:
          embed.add_field(name="⚠️ Warning",
            value=pretty_print_messages(log_analysis['warning']))
        if log_analysis['info']:
          embed.add_field(name="ℹ️ Info",
            value=pretty_print_messages(log_analysis['info']))

        embed.add_field(name='Analyser Report', inline=False,
            value=f'[**Click here for solutions / full analysis**]({anal_url})')

          #include filtered log in case SE or FTL spam is detected
        if 'obsproject.com' in log_url and any(elem in log_content for elem in _filtered_log_needles):
          clean_url = log_url.replace('obsproject.com', 'obsbot.rodney.io')
          embed.description = f'*Log contains debug messages (browser/ftl/etc), for a filtered version [click here]({clean_url})*\n'
          return await msg.channel.send(embed=embed, reference=msg, mention_author=True)


async def fetch_log_analysis(self, url):
  async with self.bot.session.get('https://obsproject.com/analyzer-api/',
                                  rams=dict(url=url, format='json')) as r:
        if r.status == 200:
          j = await r.json()
          # check if analysis response is actually valid
          if not all(i in j for i in ('critical', 'warning', 'info')):
            raise ValueError('Analyser result invalid')
          return j
        else:
          r.raise_for_status()

async def download_log(self, url):
  async with self.bot.session.get(url) as r:
      if r.status == 200:
        try:
          log = await r.text()
        except UnicodeDecodeError:
          print('Decoding log failed, trying with ISO-8859-1 encoding forced...')
          log = await r.text(encoding='ISO-8859-1')

        if 'Stack' in log and 'EIP' in log or 'Anonymous UUID' in log or 'Fault address:' in log:
          raise ValueError('Log is crash log')

        if 'log file uploaded at' not in log:  # uploaded within OBS
          if 'Startup complete' not in log:  # not uploaded within OBS but still a log
            raise ValueError('Not a (valid) OBS log')

        return log
      else:
        # Raise if status >= 400
        r.raise_for_status()

client.run(token)                   
