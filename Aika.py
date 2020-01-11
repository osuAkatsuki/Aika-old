# -*- coding: utf-8 -*-

from typing import Union, Optional, List, Tuple, Dict
import discord, asyncio
from discord.ext import commands
import mysql.connector
from mysql.connector import errorcode
from time import time
from datetime import datetime
from json import loads, dump
from os import path
from requests import get
import re

from helpers import osuHelper

from colorama import init, Fore as colour
init(autoreset=True)

""" Configuration. """

# Hardcoded version numbers.
global __version, __abns_version
__version          = 4.68 # Aika (This bot).
__abns_version     = 3.00 # Akatsuki's Beatmap Nomination System (#rank-request(s)).
__config_path: str = f'{path.dirname(path.realpath(__file__))}/config.json'

# Check for mismatching hardcoded version - config version.
global mismatch
mismatch = 0
with open(__config_path, 'r+', encoding='ascii') as tmp_file:
    tmp_config = loads(tmp_file.read())

    # TODO: check if server build, would not matter for a test env.

    if tmp_config['version'] != __version: # If mismatch, update the old config but store the mismatched version for announce.
        mismatch = tmp_config['version']
        tmp_config['version'] = __version

    if tmp_config['abns_version'] != __abns_version:
        tmp_config['abns_version'] = __abns_version

    tmp_file.seek(0)

    dump(obj=tmp_config, fp=tmp_file, sort_keys=True, indent=4)
    del tmp_config

    tmp_file.truncate()

# Now read the config file for real.
with open(__config_path, 'r', encoding='ascii') as f:
    config = loads(f.read())

# Version numbers from config.
version:      float = config['version']
abns_version: float = config['abns_version']

# Aika's discord token.
discord_token: str = config['discord_token']

# Akatsuki's server/channel IDs.
# [S] = Server. [T] = Text channel. [V] = Voice channel.
akatsuki_server_id:           int = config['akatsuki_server_id']           # [S] | ID for osu!Akatsuki.
akatsuki_general_id:          int = config['akatsuki_general_id']          # [T] | ID for #general.
akatsuki_help_id:             int = config['akatsuki_help_id']             # [T] | ID for #help.
akatsuki_verify_id:           int = config['akatsuki_verify_id']           # [T] | ID for #verify.
akatsuki_player_reporting_id: int = config['akatsuki_player_reporting_id'] # [T] | ID for #player_reporting.
akatsuki_rank_request_id:     int = config['akatsuki_rank_request_id']     # [T] | ID for #rank-request (User).
akatsuki_reports_id:          int = config['akatsuki_reports_id']          # [T] | ID for #reports.
akatsuki_rank_requests_id:    int = config['akatsuki_rank_requests_id']    # [T] | ID for #rank-requests (Staff).
akatsuki_botspam_id:          int = config['akatsuki_botspam_id']          # [T] | ID for #botspam.
akatsuki_nsfw_id:             int = config['akatsuki_nsfw_id']             # [T] | ID for #nsfw.

akatsuki_friends_only:        int = config['akatsuki_friends_only']        # [T] | ID for #friends-only.
akatsuki_drag_me_in_voice:    int = config['akatsuki_drag_me_in_voice']    # [V] | ID for Drag me in (VC).
akatsuki_friends_only_voice:  int = config['akatsuki_friends_only_voice']  # [V] | ID for ✨cmyui (VC).


mirror_address: str = config['mirror_address']        # Akatsuki's beatmap mirror (used in ABNS system).
discord_owner:  int = config['discord_owner_userid']  # Assign discord owner value.
server_build:  bool = config['server_build']          # If we're running a server build.
command_prefix: str = config['command_prefix']
embed_colour:   int = int(config['embed_colour'], 16) # Must be casted to int because JSON does not support hex format.
akatsuki_logo:  str = config['akatsuki_logo']
crab_emoji:     str = config['crab_emoji']

# A list of filters.
# These are to be used to wipe messages that are deemed inappropriate,
# or break rules. For the most part, these are of other private servers,
# as required by rule #2 of the Akatsuki Discord & Chat Rules
# (https://akatsuki.pw/doc/rules).
filters:           List[str] = config['filters']           # Direct word for word strcmp.
substring_filters: List[str] = config['substring_filters'] # Find string in message.

# Max amt of characters where if combined with unicode,
# the user is probably trying to crash Discord clients.
crashing_intent_length: int = config['crashing_intent_length']

# A list of message (sub)strings that we will use to deem
# a quantifiable value for the "quality" of a message.
low_quality:  List[str] = config['low_quality']  # Deemed a "low-quality" message  (usually profanity).
high_quality: List[str] = config['high_quality'] # Deemed a "high-quality" message (usually professionality & proper grammar).


""" Attempt to connect to MySQL. """
try: cnx = mysql.connector.connect(
        user       = config['mysql_user'],
        password   = config['mysql_passwd'],
        host       = config['mysql_host'],
        database   = config['mysql_database'],
        autocommit = True,
        use_pure   = True)
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        raise Exception('Something is wrong with your username or password.')
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        raise Exception('Database does not exist.')
    else: raise Exception(err)
else: SQL = cnx.cursor()

""" Compile regex patterns. """
regex = {
    'beatmap': re.compile(r'^((http)?s?://)?(www\.)?((gatari|akatsuki)\.pw|(old|osu)\.ppy\.sh|ripple\.moe)/b/(?P<beatmap_id>\d+)(/|\?mode=\d)?$', re.IGNORECASE),
    'beatmapset': re.compile(r'^((http)?s?://)?(www\.)?((gatari|akatsuki)\.pw|(old|osu)\.ppy\.sh|ripple\.moe)/(s|d)/(?P<beatmapset_id>\d+)(/|\?mode=\d)?$', re.IGNORECASE),
    'discussion': re.compile(r'^((http)?s?://)?(www\.)?((gatari|akatsuki)\.pw|(old|osu)\.ppy\.sh|ripple\.moe)/beatmapset/(?P<beatmapset_id>\d+)/discussion/(?P<beatmap_id>\d+)/?$', re.IGNORECASE)
}

""" Functions. """
def get_prefix(client, message: discord.Message):
    return commands.when_mentioned_or(*[config['command_prefix']])(client, message)

def is_admin(author: discord.Member) -> bool:
    return author.guild_permissions.manage_messages

client = discord.Client(
    max_messages      = 2500,
    heartbeat_timeout = 20
)

bot = commands.Bot(
    command_prefix   = get_prefix,
    case_insensitive = True,
    help_command     = None,
    self_bot         = False,
    owner_id         = discord_owner
)

[bot.load_extension(i) for i in ['cogs.staff', 'cogs.user']]

@bot.event
async def on_ready() -> None:
    print('=' * 40,
          f'Logged in as {bot.user.name}\n',
          f'UserID: {bot.user.id}',
          f'Version: {version}',
          f'ABNS Version: {abns_version}',
          f'Owner: {discord_owner}',
          f'Filters: {filters.__len__()} | {substring_filters.__len__()}',
          '=' * 40,
          end = '\n\n',
          sep = '\n'
    )

    if server_build and mismatch:
        # Configure, and send the embed to #general.
        announce_online = discord.Embed(
            title       = f"Aika has been updated to v{__version:.2f}. (Previous: v{mismatch:.2f})",
            description = "Ready for commands <3\n\n"
                          "Aika is osu!Akatsuki's [open source](https://github.com/osuAkatsuki/Aika) discord bot.\n\n"
                          "[Akatsuki](https://akatsuki.pw)\n"
                          "[Support Akatsuki](https://akatsuki.pw/support)",
            color       = 0x00ff00)                                     \
        .set_footer(icon_url=crab_emoji, text="Thank you for playing!") \
        .set_thumbnail(url=akatsuki_logo)

        await bot.get_channel(akatsuki_general_id).send(embed=announce_online)
    return


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member) -> None:
    """
    Called when a Member updates their profile.

    This is called when one or more of the following things change:
      - status
      - activity
      - nickname
      - roles

    Parameters
        before (Member) – The updated member’s old info.
        after (Member) – The updated member’s updated info.
    """
    if before.nick == after.nick or not after.nick:
        return

    non_ascii: int = 0
    for i in after.nick:
        if ord(i) > 127:
            non_ascii += 1

    if non_ascii < len(after.nick) / 2:
        return

    try:
        await after.edit(nick=before.nick)
        # Perhaps send the user a message if changed?
    except discord.errors.Forbidden:
        print(f"{colour.LIGHTRED_EX}Insufficient permissions to change new nickname '{after.nick}'.")
    return


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message) -> None:
    if after.channel.id != akatsuki_botspam_id:
        col: Optional[int] = None
        if not after.guild:                         col = colour.GREEN
        elif 'cmyui' in after.content.lower():      col = colour.CYAN
        elif after.guild.id == akatsuki_server_id:  col = colour.YELLOW

        m_start: str = f'[EDIT] [{datetime.now():%H:%M%p} #{after.channel}]  {after.author}:\n'

        m_end: Union[List[str], str] = []
        for line in after.clean_content.split('\n'): m_end.append(f'{4 * " "}{line}') # I know theres a better way to do this in py, I just can't remember it.
        m_end = '\n'.join(m_end)

        with open(f'{path.dirname(path.realpath(__file__))}/discord.log', 'a+') as log: log.write(f'\n{m_start}{m_end}')

        print(f'{col}{m_start}{colour.RESET}{m_end}\n')

    # Ignore any member with discord's "manage_messages" permissions.
    # Filter messages with our filters & substring_filters.
    if not is_admin(after.author):
        for split in after.content.lower().split(' '):
            if any(i == split for i in filters) or any(i in after.content.lower() for i in substring_filters):
                await after.delete()

                print(f'{colour.LIGHTYELLOW_EX}^ Autoremoved message ^')
                try:
                    await after.author.send(
                        'Hello,\n\n'
                        'Your message in osu!Akatsuki has been removed as it has been deemed unsuitable.\n\n'
                        f'If you have any questions, please ask <@{discord_owner}>.\n'
                        '**Do not try to evade this filter as it is considered fair ground for a ban**.\n\n'
                        f'```{f"{after.author.name}: {after.clean_content}".replace("`", "")}```'
                    )
                except: print(f'{colour.LIGHTRED_EX}Could not warn {after.author.name}.')

                cnx.ping(reconnect=True, attempts=2)

                SQL.execute('INSERT INTO profanity_logs (id, user, content, datetime) VALUES (NULL, %s, %s, %s)',
                    [after.author.id, after.content.encode('ascii', errors='ignore'), time()])

                return


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None: # TODO: check if they left dragmein, and delete embed.. if that's even possible..

    # Only use this event for the "drag me in" voice channel.
    if not after.channel or after.channel.id != akatsuki_drag_me_in_voice: return

    # Create our vote embed.
    embed = discord.Embed(
        title       = f'{member} wants to be dragged in.',
        description = 'Please add a reaction to determine their fate owo..',
        color       = 0x00ff00)                                             \
    .set_footer(icon_url = crab_emoji, text = 'Only one vote is required.') \
    .set_thumbnail(url   = akatsuki_logo)

    # Assign friends-only chat and voice channel as constants.
    friends_only_text  = bot.get_channel(akatsuki_friends_only)
    friends_only_voice = bot.get_channel(akatsuki_friends_only_voice)

    # Send our embed, and add our base 👍.
    msg: Optional[discord.Message] = await friends_only_text.send(embed=embed)
    await msg.add_reaction('👍')

    def check(reaction: discord.Reaction, user: discord.Member) -> bool: # TODO: safe
        if user in [member, bot.user]: return False
        return reaction.emoji == '👍' and user.voice.channel == friends_only_voice

    # Wait for a 👍 from a "friend". Timeout: 5 minutes.
    try:
        _, user = await bot.wait_for('reaction_add', timeout=5 * 60, check=check)
    except asyncio.TimeoutError: # Timed out. Remove the embed.
        await friends_only_text.send(f"Timed out {member}'s join query.")
        await msg.delete()
        return

    try: await member.move_to(channel=friends_only_voice, reason='Voted in.')
    except discord.errors.HTTPException: await msg.delete(); return

    # Send our vote success, and delete the original embed.
    await friends_only_text.send(f'{user} voted {member} in.')
    await msg.delete()
    return


@bot.event
async def on_message(message: discord.Message) -> None:

    # Message is either empty, sent by the bot, or is not in a guild.
    if not message.content or message.author == bot.user or not message.guild:
        return

    # Regular user checks.
    if not await bot.is_owner(message.author):

        # Verification channel.
        if message.channel.id == akatsuki_verify_id:
            if not message.content.split()[-1].isdigit(): # bot
                await message.author.add_roles(discord.utils.get(message.guild.roles, name='Members'))
                await bot.get_channel(akatsuki_general_id).send(f'Welcome to osu!Akatsuki <@{message.author.id}>!')

            await message.delete() # Delete all messages posted in #verify.
            return

        # If we have unicode in a long message,
        # it's probably either with crashing intent,
        # or is just low quality to begin with?
        if  any(ord(char) > 127 for char in message.content) \
        and len(message.content) >= crashing_intent_length:
            await message.delete()
            return

    else: # Owner checks.
        if  len(message.content) > 5 \
        and message.content[1:7] == 'reload':
            cog_name: str = message.content[9:].lower()
            if cog_name in ('staff', 'user'):
                bot.reload_extension(f'cogs.{cog_name}')
                await message.channel.send(f'Reloaded extension {cog_name}.')
            else:
                await message.channel.send(f'Invalid extension {cog_name}.')
            return


    if message.channel.id == akatsuki_nsfw_id: # NSFW channel checks (deleting non-images from #nsfw).
        if not (re.match(r'^https?://', message.content, re.IGNORECASE) or message.attachments):
            await message.delete()
        return


    # Message sent in #rank-request, move to #rank-requests.
    elif message.channel.id == akatsuki_rank_request_id:
        await message.delete()

        input_id: int
        res: Optional[Tuple[float, int, str]]
        cnx.ping(reconnect=True, attempts=2)

        if regex['beatmap'].match(message.content):
            input_id = regex['beatmap'].match(message.content).group('beatmap_id')
            SQL.execute('SELECT beatmap_id AS id, beatmapset_id AS sid, mode, ranked, song_name, ar, od, max_combo, bpm FROM beatmaps WHERE beatmap_id = %s', [input_id])
            res = SQL.fetchone()

            if not res:
                await message.author.send('The beatmap could not be found in our database.')
                return

        elif regex['beatmapset'].match(message.content):
            input_id = int(regex['beatmapset'].match(message.content).group('beatmapset_id'))
            SQL.execute('SELECT beatmap_id AS id, beatmapset_id AS sid, mode, ranked, song_name, ar, od, max_combo, bpm FROM beatmaps WHERE beatmap_id = (SELECT beatmap_id FROM beatmaps WHERE beatmapset_id = %s)', [input_id])

        elif regex['discussion'].match(message.content):
            input_id = regex['discussion'].match(message.content).group('beatmap_id')
            SQL.execute('SELECT beatmap_id AS id, beatmapset_id AS sid, mode, ranked, song_name, ar, od, max_combo, bpm FROM beatmaps WHERE beatmap_id = %s', [input_id])
            res = SQL.fetchone()

            if not res:
                await message.author.send('The beatmap could not be found in our database.')
                return

        else:
            await message.author.send(f'The request format was incorrect.\n\nPlease simply send the beatmap link in <#{akatsuki_rank_request_id}> to request a beatmmap.')
            return

        b: Dict[str, Union[float, int, str]] = dict(zip(SQL.column_names, res))

        if b['ranked'] in (2, 5): # Map is already ranked/loved
            await message.author.send('Some (or all) of the difficulties in the beatmap you requested already seem to be '
                                     f'{"ranked" if b["ranked"] == 2 else "loved"} on the Akatsuki server!\n\n'
                                      'If this is false, please contact a BN directly to proceed.')
            return

        # Sort out mode to be used to check difficulty.
        # Also have a formatted one to be used for final post.
        mode, mode_formatted = osuHelper.mode_to_readable(b['mode'])

        # Select map information.
        SQL.execute(f'SELECT difficulty_{mode} FROM beatmaps WHERE beatmap_id = %s ORDER BY difficulty_{mode} DESC LIMIT 1', [b['id']])
        res = SQL.fetchone()
        b.update({ 'difficulty': res[0] if res else 0 })

        # Temp disabled
        #artist = loads(get(f'{mirror_address}/api/s/{map_id}', timeout=1.5).text)['Creator']
        #.add_field (name = "Mapper",            value = artist)                          \

        # Create embeds.
        embed = discord.Embed(
            title = 'A new beatmap request has been recieved.',
            description = '** **',
            color       = embed_colour
            ) \
        .set_image (url  = f'https://assets.ppy.sh/beatmaps/{b["sid"]}/covers/cover.jpg?1522396856') \
        .set_author(url  = f'https://akatsuki.pw/d/{b["sid"]}', name = b['song_name'], icon_url = akatsuki_logo) \
        .set_footer(text = f"Akatsuki's beatmap nomination system v{abns_version:.2f}", icon_url = 'https://nanahira.life/MpgDe2ssQ5zDsWliUqzmQedZcuR4tr4c.jpg') \
        .add_field (name = 'Nominator',         value = message.author.name)       \
        .add_field (name = 'Gamemode',          value = mode_formatted)            \
        .add_field (name = 'Highest SR',        value = f'{b["difficulty"]:.2f}*') \
        .add_field (name = 'Highest AR',        value = b['ar'])                   \
        .add_field (name = 'Highest OD',        value = b['od'])                   \
        .add_field (name = 'Highest Max Combo', value = f'{b["max_combo"]}x')      \
        .add_field (name = 'BPM',               value = b['bpm'])

        # Prepare, and send the report to the reporter.
        embed_dm = discord.Embed(
            title       = "Your beatmap nomination request has been sent to Akatsuki's Beatmap Nomination Team for review.",
            description = 'We will review it shortly.',
            color       = 0x00ff00
            ) \
        .set_thumbnail(url  = akatsuki_logo) \
        .set_image    (url  = f'https://assets.ppy.sh/beatmaps/{b["sid"]}/covers/cover.jpg?1522396856') \
        .set_footer   (text = f"Akatsuki's beatmap nomination system v{abns_version:.2f}", icon_url = crab_emoji)

        # Send the embed to the #rank_requests channel.
        request_post = await bot.get_channel(akatsuki_rank_requests_id).send(embed=embed)

        # Send the embed to the nominator by DM. TODO: check if we can message the user rather than abusing try-except? that might just be slower lul
        try: await message.author.send(embed=embed_dm)
        except: print(f'Could not DM ({message.author.name}).')

        for i in ['👍', '👎']: await request_post.add_reaction(i)
        return


    # Message sent in #player-reporting, move to #reports.
    elif message.channel.id == akatsuki_player_reporting_id:
        await message.delete() # Delete the message from #player-reporting.

        # Prepare, and send the report in #reports.
        embed = discord.Embed(title = 'New report recieved.', description='** **', color=0x00ff00)     \
        .set_thumbnail       (url   = akatsuki_logo)                                                   \
        .add_field           (name  = 'Report content', value = message.content,        inline = True) \
        .add_field           (name  = 'Author',         value = message.author.mention, inline = True)

        # Prepare, and send the report to the reporter.
        embed_pm = discord.Embed(
            title       = 'Thank you for the player report.',
            description = 'We will review the report shortly.',
            color       = 0x00ff00)                                                     \
        .add_field    (name = 'Report content', value = message.content, inline = True) \
        .set_thumbnail(url  = akatsuki_logo)

        if not message.content.startswith(command_prefix): # Do not pm or link to #reports if it is a command.
            await message.author.send(embed=embed_pm)
            await bot.get_channel(akatsuki_reports_id).send(embed=embed)
        return

    # Message sent in #help, log to db.
    elif message.channel.id == akatsuki_help_id:
        # Split the content into sentences by periods.
        # TODO: Other punctuation marks!
        sentence_split: List[str] = message.content.split('.')

        # Default values for properly formatted messages / negative messages.
        properly_formatted, negative = [False] * 2

        # After every period, check they have a space and the next sentence starts with a capital letter (ignore things like "...").
        for idx, sentence in enumerate(sentence_split):
            if len(sentence) > 1 and idx:
                if sentence[0] == ' ' and sentence[1].isupper(): continue
                negative = True

        properly_formatted = \
            message.content[0].isupper() \
            and message.content[len(message.content) - 1] in ('.', '?', '!') \
            and not negative

        quality: int = 1
        if any(i in message.content.lower() for i in low_quality):                          quality -= 1
        elif any(i in message.content.lower() for i in high_quality) or properly_formatted: quality += 1

        cnx.ping(reconnect=True, attempts=2)

        # TODO: Store the whole bitch in a single number.
        # Maybe even do some bitwise black magic shit.
        SQL.execute('INSERT INTO help_logs (id, user, content, datetime, quality) VALUES (NULL, %s, %s, %s, %s)',
            [message.author.id, message.content.encode('ascii', errors='ignore'), time(), quality])

    if message.channel.id != akatsuki_botspam_id:
        col: Optional[int] = None
        if not message.guild:                         col = colour.GREEN
        elif 'cmyui' in message.content.lower():      col = colour.CYAN
        elif message.guild.id == akatsuki_server_id:  col = colour.YELLOW

        m_start: str = f'[{datetime.now():%H:%M%p} #{message.channel}] {message.author}:\n'

        m_end: Union[List[str], str] = []
        for line in message.clean_content.split('\n'): m_end.append(f'{4 * " "}{line}') # I know theres a better way to do this in py, I just can't remember it.
        m_end = '\n'.join(m_end)

        with open(f'{path.dirname(path.realpath(__file__))}/discord.log', 'a+') as log: log.write(f'\n{m_start}{m_end}')

        print(f'{col}{m_start}{colour.RESET}{m_end}\n')

    # Ignore any member with discord's "manage_messages" permissions.
    # Filter messages with our filters & substring_filters.
    if not is_admin(message.author):
        for split in message.content.lower().split(' '):
            if any(i == split for i in filters) or any(i in message.content.lower() for i in substring_filters):
                await message.delete()

                print(f'{colour.LIGHTYELLOW_EX}^ Autoremoved message ^')
                try:
                    await message.author.send(
                        'Hello,\n\n'
                        'Your message in osu!Akatsuki has been removed as it has been deemed unsuitable.\n\n'
                        f'If you have any questions, please ask <@{discord_owner}>.\n'
                        '**Do not try to evade this filter as it is considered fair ground for a ban**.\n\n'
                        f'```{f"{message.author.name}: {message.content}".replace("`", "")}```'
                    )
                except: print(f'{colour.LIGHTRED_EX}Could not warn {message.author.name}.')

                cnx.ping(reconnect=True, attempts=2)

                SQL.execute('INSERT INTO profanity_logs (id, user, content, datetime) VALUES (NULL, %s, %s, %s)',
                    [message.author.id, message.content.encode('ascii', errors='ignore'), time()])

                return

    # Finally, process commands.
    await bot.process_commands(message)
    return

bot.run(discord_token, bot=True, reconnect=True)

# Clean up
print('\nKeyboardInterrupt detected. Powering down Aika..')
SQL.close()
cnx.close()
bot.logout()
print('Cleaning complete.')
