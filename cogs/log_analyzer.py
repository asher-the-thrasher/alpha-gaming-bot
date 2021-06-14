from asyncio import TimeoutError
from urllib.parse import quote_plus as urlencode

from aiohttp import ClientResponseError, ClientTimeout, ClientSession
from discord import Embed, Colour
from discord.ext.commands import Cog
from discord.ext.commands.bot import Bot

from RateLimit import RateLimiter

# channels to  whitelist
general_help = 473309543858962433
stream_software = 764008007658897439
pc_help = 599861596159737876
audio_help = 599861521543200789
testing_playroom = 744785084313501728
lights_camera_editing = 599861471874383882

channel_whitelist = [general_help, stream_software, pc_help, audio_help, testing_playroom, lights_camera_editing,
                     744333418724065373]


class LogAnalyzer(Cog):
    _analysis_colour = 0x5a7474
    _log_download_failed = '\U00002757'
    _log_analyser_failed = '\U0001F6AB'
    _filtered_log_needles = ('obs-streamelements.dll', 'ftl_stream_create')
    _log_hosts = ('https://obsproject.com/logs/', 'https://hastebin.com/',
                  'https://pastebin.com/')

    timeout = ClientTimeout(total=60)
    bot = Bot
    limiter = RateLimiter(20.0)

    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(timeout=self.timeout)

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            # Checks to see if the Message is a bot Message

        if message.channel.id not in channel_whitelist:
            return
            # we don't want bot in every channel

        if not message.attachments and not any(lh in message.content for lh in self._log_hosts):
            return
            # Returns if the message is not a log file

        # print("Message has log file: " + str(Message.content))

        # list of candidate tuples consisting of (raw_url, web_url)
        log_candidates = []

        # Message attachments
        for attachment in message.attachments:
            if attachment.url.endswith('.txt'):
                # collisions are possible here, but unlikely, we'll see if it becomes a problem

                if not self.limiter.is_limited(attachment.filename):
                    log_candidates.append(attachment.url)
                else:
                    print(f'{message.author} attempted to upload a rate-limited log.')

        # links in Message
        for part in [p.strip() for p in message.content.split()]:
            if any(part.startswith(lh) for lh in self._log_hosts):

                if 'obsproject.com' in part:
                    url = part
                    log_candidates.append(url)
                    continue
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

                if not self.limiter.is_limited(url):
                    log_candidates.append(url)
                else:
                    print(f'{message.author} attempted to post a rate-limited log.')

        if not log_candidates:
            # print("not log candidate")
            return

        if len(log_candidates) > 3:
            print('Too many log url candidates, limiting to first 3')
            log_candidates = log_candidates[:3]

        async def react(emote):
            try:
                await message.add_reaction(emote)
            except Exception as e:
                print(f'Adding reaction failed with "{repr(e)}')

        for log_url in log_candidates:
            try:
                log_content = await self.download_log(log_url)
                break
            except ValueError:  # not a valid OBS log
                continue
            except (ClientResponseError, TimeoutError):  # file download failed
                print(f'Failed retrieving log from "{log_url}"')
                await react(self._log_download_failed)
            except Exception as e:  # catch everything else
                print(f'Unhandled exception when downloading log: {repr(e)}')
        else:
            return

        async with message.channel.typing():
            log_analysis = None
            try:
                # fetch log analysis from OBS analyser
                log_analysis = await self.fetch_log_analysis(log_url)
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
                    return await react(self._log_analyser_failed)

                anal_url = f'https://obsproject.com/tools/analyzer?log_url={urlencode(log_url)}'
                embed = Embed(colour=Colour(0x5a7474), url=anal_url)

                # formatting Message
                def pretty_print_messages(messages):
                    ret = []
                    for _Message in messages:
                        ret.append(f'- {_Message}')
                    return '\n'.join(ret)

                if log_analysis['critical']:
                    embed.add_field(name="🛑 Critical",
                                    value=pretty_print_messages(
                                        log_analysis['critical']))
                if log_analysis['warning']:
                    embed.add_field(name="⚠️ Warning",
                                    value=pretty_print_messages(
                                        log_analysis['warning']))
                if log_analysis['info']:
                    embed.add_field(name="ℹ️ Info",
                                    value=pretty_print_messages(
                                        log_analysis['info']))

                embed.add_field(
                    name='Analyser Report',
                    inline=False,
                    value= f'[**Click here for solutions / full analysis**]({anal_url})')

                # include filtered log in case SE or FTL spam is detected
                if 'obsproject.com' in log_url and any(elem in log_content for elem in self._filtered_log_needles):
                    clean_url = log_url.replace('obsproject.com',
                                                'obsbot.rodney.io')
                    embed.description = f'*Log contains debug Messages (browser/ftl/etc), for a filtered version [click here]({clean_url})*\n'

                return await message.channel.send(embed=embed, reference=message, mention_author=True)

    async def fetch_log_analysis(self, url):
        async with self.session.get('https://obsproject.com/analyzer-api/', params=dict(url=url, format='json')) as r:
            if r.status == 200:
                j = await r.json()
                # check if analysis response is actually valid
                if not all(i in j for i in ('critical', 'warning', 'info')):
                    raise ValueError('Analyser result invalid')
                return j
            else:
                r.raise_for_status()

    async def download_log(self, url):
        async with self.session.get(url) as r:
            if r.status == 200:
                try:
                    log = await r.text()
                except UnicodeDecodeError:
                    print(
                        'Decoding log failed, trying with ISO-8859-1 encoding forced...'
                    )
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
