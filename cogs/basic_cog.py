import discord
from discord.ext import commands
from replit import db



class factoids(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.keys = db.keys()
  

  @commands.command()
  async def add(self):
    print("here")

"""  @commands.Cog.listener()
  async def on_message(self, message):
    if message.author.bot:
      return
    if message.content.lower().startswith('!'):    
      msg_parts = message.content[1:].split()
      factoid_name = msg_parts[0].lower()
      try:
        factoid = db[f"{factoid_name}"] 
      except KeyError:
        return 


      reference = message.reference
      message_parts = message.content[1:].split()
      # attempt to delete the message requesting the factoid if it's within a reply and only contains command
      if message.reference and len(message_parts) == 1:
          await message.delete(delay=0.0)

      # if users are mentioned (but it's not a reply), mention them in the bot reply as well
      user_mention = None

      if message.mentions and not reference:
          user_mention = ' '.join(user.mention for user in message.mentions)

      embed=discord.Embed(title="", description=factoid, colour=0xf81af3)

      if message.reference and embed is not None:
        return await message.channel.send(embed=embed, reference=reference, mention_author=True)

      elif user_mention and embed is not None:
          return await message.channel.send(user_mention, embed=embed)
      else:
          return await message.channel.send(embed=embed)


    else:
      return

  @commands.command()
  @commands.has_permissions(manage_messages=True)
  async def add(self, ctx):# name: str.lower, *, message):
      print("here")
      
      if name in self.keys:
        return await ctx.send(f'The specified name ("{name}") already exists as factoid or alias!')

    
    db[f"{name}"] = f"{message}"

    return await ctx.send(f'Factoid "{name}" has been added.')

  @commands.command()
  async def mod(self, ctx, name: str.lower, *, message):
      if not self.bot.is_admin(ctx.author):
          return
      _name = name if name in self.factoids else self.alias_map.get(name)
      if not _name or _name not in self.factoids:
          return await ctx.send(f'The specified name ("{name}") does not exist!')

      # allow clearing message of embeds
      if self.factoids[_name]['embed'] and message == '""':
          message = ''

      await self.bot.db.exec(
          f'''UPDATE "{self.config["db_table"]}" SET message=$2 WHERE name=$1''',
          _name, message
      )

      await self.fetch_factoids(refresh=True)
      return await ctx.send(f'Factoid "{name}" has been updated.')

  @commands.command(name='del')
  async def _del(self, ctx, name: str.lower):
      if not self.bot.is_admin(ctx.author):
          return
      if name not in self.factoids:
          return await ctx.send(f'The specified factoid name ("{name}") does not exist '
                                f'(use base name instead of alias)!')

      await self.bot.db.exec(f'''DELETE FROM "{self.config["db_table"]}" WHERE name=$1''', name)
      await self.fetch_factoids(refresh=True)
      return await ctx.send(f'Factoid "{name}" has been deleted.')

  @commands.command()
  async def ren(self, ctx, name: str.lower, new_name: str.lower):
      if not self.bot.is_admin(ctx.author):
          return
      if name not in self.factoids and name not in self.alias_map:
          return await ctx.send(f'The specified name ("{name}") does not exist!')
      if new_name in self.factoids or new_name in self.alias_map:
          return await ctx.send(f'The specified new name ("{name}") already exist as factoid or alias!')

      # if name is an alias, rename the alias instead
      if name in self.alias_map:
          real_name = self.alias_map[name]
          # get list of aliases minus the old one, then append the new one
          aliases = [i for i in self.factoids[real_name]['aliases'] if i != name]
          aliases.append(new_name)

          await self.bot.db.exec(
              f'''UPDATE "{self.config["db_table"]}" SET aliases=$2 WHERE name=$1''',
              real_name, aliases
          )

          await self.fetch_factoids(refresh=True)
          return await ctx.send(f'Alias "{name}" for "{real_name}" has been renamed to "{new_name}".')
      else:
          await self.bot.db.exec(
              f'''UPDATE "{self.config["db_table"]}" SET name=$2 WHERE name=$1''',
              name, new_name
          )

          await self.fetch_factoids(refresh=True)
          return await ctx.send(f'Factoid "{name}" has been renamed to "{new_name}".')

  @commands.command()
  async def addalias(self, ctx, alias: str.lower, name: str.lower):
      if not self.bot.is_admin(ctx.author):
          return
      _name = name if name in self.factoids else self.alias_map.get(name)
      if not _name or _name not in self.factoids:
          return await ctx.send(f'The specified factoid ("{name}") does not exist!')
      if alias in self.factoids:
          return await ctx.send(f'The specified alias ("{alias}") is the name of an existing factoid!')
      if alias in self.alias_map:
          return await ctx.send(f'The specified alias ("{alias}") already exists!')

      self.factoids[_name]['aliases'].append(alias)

      await self.bot.db.exec(
          f'''UPDATE "{self.config["db_table"]}" SET aliases=$2 WHERE name=$1''',
          _name, self.factoids[_name]['aliases']
      )

      await self.fetch_factoids(refresh=True)
      return await ctx.send(f'Alias "{alias}" added to "{name}".')

  @commands.command()
  async def delalias(self, ctx, alias: str.lower):
      if not self.bot.is_admin(ctx.author):
          return
      if alias not in self.alias_map:
          return await ctx.send(f'The specified name ("{alias}") does not exist!')

      real_name = self.alias_map[alias]
      # get list of aliases minus the old one, then append the new one
      aliases = [i for i in self.factoids[real_name]['aliases'] if i != alias]

      await self.bot.db.exec(
          f'''UPDATE "{self.config["db_table"]}" SET aliases=$2 WHERE name=$1''',
          real_name, aliases
      )

      await self.fetch_factoids(refresh=True)
      return await ctx.send(f'Alias "{alias}" for "{real_name}" has been removed.')"""

    


def setup(client):
  client.add_cog(factoids(client))