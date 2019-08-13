import discord
from discord.ext import commands
import asyncio

import mysql.connector
from mysql.connector import errorcode

from time import time
from json import loads
from requests import get

# TODO: stop using these!
from colorama import init
from colorama import Fore, Back, Style
init(autoreset=True)


SQL_HOST, SQL_USER, SQL_PASS, SQL_DB = [None] * 4
with open('config.ini', 'r') as f:
    for _line in f.read().splitlines():
        if not _line: continue
        line = _line.split("=")
        key = line[0].rstrip()
        val = line[1].lstrip()

        if key == "SQL_HOST": SQL_HOST = val # IP Address for SQL.
        elif key == "SQL_USER": SQL_USER = val # Username for SQL.
        elif key == "SQL_PASS": SQL_PASS = val # Password for SQL.
        elif key == "SQL_DB": SQL_DB = val # DB name for SQL.

if any(not i for i in [SQL_HOST, SQL_USER, SQL_PASS, SQL_DB]):
    raise Exception("Not all required configuration values could be found.")

try:
    cnx = mysql.connector.connect(
        user       = SQL_USER,
        password   = SQL_PASS,
        host       = SQL_HOST,
        database   = SQL_DB,
        autocommit = True)
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your username or password.")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist.")
    else:
        print(err)
else:
    SQL = cnx.cursor()


# Subsystem versions.
AIKA_VERSION = 4.21 # Aika (This bot).
ABNS_VERSION = 2.14 # Akatsuki's Beatmap Nomination System (#rank-request(s)).


# Akatsuki's server/channel IDs.
# [S] = Server.
# [T] = Text channel.
# [V] = Voice channel.
AKATSUKI_SERVER_ID           = 365406575893938177 # [S] | ID for osu!Akatsuki.
AKATSUKI_GENERAL_ID          = 592490140497084436 # [T] | ID for #general.
AKATSUKI_HELP_ID             = 365413867167285249 # [T] | ID for #help.
AKATSUKI_VERIFY_ID           = 596662084339761172 # [T] | ID for #verify.
AKATSUKI_PLAYER_REPORTING_ID = 367068661837725706 # [T] | ID for #player_reporting.
AKATSUKI_REPORTS_ID          = 367080772076568596 # [T] | ID for #reports.
AKATSUKI_NSFW_STRAIGHT_ID    = 428460752698081291 # [T] | ID for #nsfw.
AKATSUKI_NSFW_TRAPS_ID       = 505960162411020288 # [T] | ID for #nsfw-traps.
AKATSUKI_RANK_REQUEST_ID     = 597200076561055795 # [T] | ID for #rank-request (User).
AKATSUKI_RANK_REQUESTS_ID    = 557095943602831371 # [T] | ID for #rank-requests (Staff).
AKATSUKI_BOTSPAM_ID          = 369829943372152833 # [T] | ID for #botspam.

AKATSUKI_FRIENDS_ONLY        = 597948877621952533 # [T] | ID for #friends-only.
AKATSUKI_DRAG_ME_IN_VOICE    = 597949535938936833 # [V] | ID for Drag me in (VC).
AKATSUKI_FRIENDS_ONLY_VOICE  = 597948898421768192 # [V] | ID for ✨cmyui (VC).


# Aika's command prefix.
COMMAND_PREFIX = '!'


# Akatsuki's logo.
# To be used mostly for embed thumbnails.
AKATSUKI_LOGO = "https://akatsuki.pw/static/logos/logo.png"
CRAB_EMOJI    = "https://cdn.discordapp.com/attachments/365406576548511745/591470256497754112/1f980.png"


# A list of filters.
# These are to be used to wipe messages that are deemed inappropriate,
# or break rules. For the most part, these are of other private servers,
# as required by rule #2 of the Akatsuki Discord & Chat Rules
# (https://akatsuki.pw/doc/rules).
filters       = [
                # osu! private servers
                "yozora", "ainu", "okamura", "kotorikku", "kurikku", "kawata",
                "ryusei", "ryu-sei", "enjuu", "verge", "katori", "osu-thailand",
                "gatari", "hidesu", "hiragi", "asuki", "mikoto", "homaru", "awasu",
                "vipsu", "xii", "xii.nz", "yarota", "silverosu", "sugoisu", "kono",
                "zeltu", "karizuku", "koreasu", "asta", "tiller", # I really didn't want to block "tiller", but it seems like it keeps getting mentioned..

                # osu! cheating programs
                "aqn", "hq", "hqosu", "aquila",

                # Bad boy substances
                "lsd", "dmt", "shrooms"
                ]

# Secondary filters.
# These are the same idea as filters,
# although they are *searched for within a string*, rather than compared against.
substring_filters = [
                    # PayPal
                    "pp.me", "paypal.me",

                    # Discord invite links
                    "discord.gg/", "discordapp.com/channels"
                    ]


# A list of message (sub)strings that we will use to deem
# a quantifiable value for the "quality" of a message.
profanity     = ["nigg", "n1gg", "retard", "idiot",
                 "fuck off", "shut the fuck up", "??"]

high_quality  = ["!faq", "!help", "welcome", "have a good", "enjoy", "no problem",
                 "of course", "can help", "i can", "how can i help you"]


# Assign discord owner value.
SQL.execute("SELECT value_string FROM aika_settings WHERE name = %s", ["discord_owner"])
discord_owner = int(SQL.fetchone()[0])


def debug_print(string):
    """
    Print a debug message to the console.

    Example in use:      https://nanahira.life/dOgXljmmKW336gro3Ts5gJmU7P4hNDZz.png

    :param string:       The message to be printed to the console.
    """

    # Debug value
    SQL.execute("SELECT value_int FROM aika_settings WHERE name = %s", ["debug"])
    debug = SQL.fetchone()[0]

    if debug:
        print(Fore.MAGENTA, string, "", sep="\n")


def safe_discord(s): return str(s).replace("`", "") 


def get_prefix(client, message):

    prefixes = [COMMAND_PREFIX] # More prefixes can be added to this

    # Users can also mention the bot.
    return commands.when_mentioned_or(*prefixes)(client, message)


client = discord.Client()
bot = commands.Bot(
    command_prefix   = get_prefix,
    description      = "Aika - osu!Akatsuki's official Discord bot.",
    owner_id         = discord_owner,
    case_insensitive = True # No case sensitivity on commands
)


cogs = ["cogs.staff", "cogs.user"]


@bot.event
async def on_voice_state_update(member, before, after): # TODO: check if they left dragmein, and delete embed.. if that's even possible..
    # Await for the bot to be ready before processing voice state updates whatsoever.
    await bot.wait_until_ready()

    # Only use this event for the "drag me in" voice channel.
    if not after.channel or after.channel.id != AKATSUKI_DRAG_ME_IN_VOICE: return

    debug_print(f"on_voice_state_update event fired.\n\nData:\n\n{member}\n\n{before}\n\n{after}")

    # Create our vote embed.
    embed = discord.Embed(
        title       = f"{member} wants to be dragged in.",
        description = "Please add a reaction to determine their fate owo..",
        color       = 0x00ff00)

    embed.set_footer(icon_url=CRAB_EMOJI, text="Only one vote is required.")
    embed.set_thumbnail(url=AKATSUKI_LOGO)

    # Assign friends-only chat and voice channel as constants.
    FRIENDS_ONLY_TEXT  = bot.get_channel(AKATSUKI_FRIENDS_ONLY)
    FRIENDS_ONLY_VOICE = bot.get_channel(AKATSUKI_FRIENDS_ONLY_VOICE)

    # Send our embed, and add our base 👍.
    msg = await FRIENDS_ONLY_TEXT.send(embed=embed)
    await msg.add_reaction("👍")

    def check(reaction, user):
        if user == bot.user: return False
        return reaction.emoji == "👍" and user.voice.channel == FRIENDS_ONLY_VOICE

    # Wait for a 👍 from a "friend". Timeout: 5 minutes.
    try: reaction, user = await bot.wait_for("reaction_add", timeout=5*60, check=check)
    except asyncio.TimeoutError: # Timed out. Remove the embed.
        await FRIENDS_ONLY_TEXT.send(f"Timed out {member}'s join query.")
        await msg.delete()
        return

    try: await member.move_to(channel=FRIENDS_ONLY_VOICE, reason="Voted in.")
    except discord.errors.HTTPException: await msg.delete(); return

    # Send our vote success, and delete the original embed.
    await FRIENDS_ONLY_TEXT.send(f"{user} voted {member} in.")
    await msg.delete()
    return

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - {bot.user.id}")
    await bot.change_presence(activity=discord.Game(name="osu!Akatsuki", url="https://akatsuki.pw/", type=1))
    for cog in cogs: bot.load_extension(cog)

    # Announce online status to #general if we're on a server build of Aika.
    SQL.execute("SELECT value_int FROM aika_settings WHERE name = %s", ["server_build"])
    server_build = bool(SQL.fetchone()[0])

    if server_build:
        # Get the server's latest version of Aika run.
        SQL.execute("SELECT value_int FROM aika_settings WHERE name = %s", ["version_latest"])
        version_latest = SQL.fetchone()[0]

        # If the server version mismatches the version of the code, display the update in a #general webhook.
        if version_latest == AIKA_VERSION: return

        SQL.execute("UPDATE aika_settings SET value_int = %s WHERE name = %s", [AIKA_VERSION, "version_latest"])

        # Configure, and send the embed to #general.
        announce_online = discord.Embed(
            title       = f"Aika has been updated to v{'%.2f' % AIKA_VERSION}. (Previous: v{'%.2f' % version_latest})",
            description = "Ready for commands <3\n\nAika is osu!Akatsuki's [open source](https://github.com/osuAkatsuki/Aika) "
                          "discord bot.\n\n[Akatsuki](https://akatsuki.pw)\n[Support Akatsuki](https://akatsuki.pw/support)",
            color       = 0x00ff00)

        announce_online.set_footer(icon_url=CRAB_EMOJI, text="Thank you for playing!")
        announce_online.set_thumbnail(url=AKATSUKI_LOGO)
        await bot.get_channel(AKATSUKI_GENERAL_ID).send(embed=announce_online)
    return


@bot.event
async def on_message(message):
    # Await for the bot to be ready before processing messages whatsoever.
    await bot.wait_until_ready()

    # The message has no content.
    # Don't bother doing anything with it.
    if not message.content or len(message.content) < 2: return

    if message.author.id != discord_owner: # Regular user
        if message.content.lower()[1] == "v" and message.channel.id == AKATSUKI_VERIFY_ID: # Verify command.
            await message.author.add_roles(discord.utils.get(message.guild.roles, name="Members"))
            await message.delete()
            return

        # if we have unicode in > 1k char message, it's probably with crashing intent?
        if not all(ord(char) < 128 for char in message.content) and len(message.content) > 1000: await message.delete(); return
    else: # Owner
        if len(message.content) > 5 and message.content[1:7] == "reload":
            cog_name = message.content[9:].lower()
            if cog_name in ("staff", "user"):
                bot.reload_extension(f"cogs.{cog_name}")
                await message.channel.send(f"Reloaded extension {cog_name}.")
            else:
                await message.channel.send(f"Invalid extension {cog_name}.")
            return


    if message.channel.id in (AKATSUKI_NSFW_STRAIGHT_ID, AKATSUKI_NSFW_TRAPS_ID):
        def check_content(m): # Don't delete links or images.
            if "http" in message.content or message.attachments: return False
            return True

        if check_content(message): await message.delete()
        return


    # Message sent in #rank-request, move to #rank-requests.
    if message.channel.id == AKATSUKI_RANK_REQUEST_ID:
        await message.delete()

        if not any(required in message.content for required in ("akatsuki.pw", "osu.ppy.sh")) or len(message.content) > 58: # Should not EVER be over 58 characters. (57 but safe)
            await message.author.send("Your beatmap request was incorrectly formatted, and thus has not been submitted. "
                                      "Please use the old osu links for the time being. (e.g. https://osu.ppy.sh/b/123)")
            return

        # Support both links like "https://osu.ppy.sh/b/123" AND "osu.ppy.sh/b/123".
        # Also allow for /s/, /b/, and /beatmapset/setid/discussion/mapid links.
        if "://" in message.content: partitions = message.content.split("/")[3:]
        else:                        partitions = message.content.split("/")[1:]

        # Yea thank you for sending something useless in #rank-request very cool.
        if partitions[0] not in ("s", "b", "beatmapsets"): return

        beatmapset = partitions[0] in ("s", "beatmapsets") # Link is a beatmapset_id link, not a beatmap_id link.
        map_id = partitions[1] # Can be SetID or MapID.

        if not beatmapset: # If the user used a /b/ link, let's turn it into a set id.
            SQL.execute("SELECT beatmapset_id FROM beatmaps WHERE beatmap_id = %s LIMIT 1", [map_id])
            map_id = SQL.fetchone()[0]

        # Do this so we can check if any maps in the set are ranked or loved.
        # If they are, the QAT have most likely already determined statuses of the map.
        SQL.execute("SELECT mode, ranked FROM beatmaps WHERE beatmapset_id = %s ORDER BY ranked DESC LIMIT 1", [map_id])
        sel = SQL.fetchone()

        if not sel: # We could not find any matching rows with the map_id.
            await message.author.send("That map seems to be invalid. Quoi?")
            return

        mode, status = sel

        if status in (2, 5): # Map is already ranked/loved
            await message.author.send(f"Some (or all) of the difficulties in the beatmap you requested already seem to be {'ranked' if status == 2 else 'loved'} "
                                       "on the Akatsuki server!\n\nIf this is false, please contact a QAT directly to proceed.")
            return

        # Sort out mode to be used to check difficulty.
        # Also have a formatted one to be used for final post.
        if mode == 0: mode, mode_formatted = "std", "osu!"
        elif mode == 1: mode, mode_formatted = "taiko", "osu!taiko"
        elif mode == 2: mode, mode_formatted = "ctb", "osu!catch"
        else: mode, mode_formatted = "mania", "osu!mania"

        # Select map information.
        SQL.execute(f"SELECT song_name, ar, od, max_combo, bpm, difficulty_{mode} FROM beatmaps WHERE beatmapset_id = %s ORDER BY difficulty_{mode} DESC LIMIT 1", [map_id])
        song_name, ar, od, max_combo, bpm, star_rating = SQL.fetchone()

        # Return values from web request/DB query.
        # TODO: either use the API for everything, or dont use it at all.
        artist = loads(get(f"https://cheesegull.mxr.lol/api/s/{map_id}").text)["Creator"]

        # Create embeds.
        embed = discord.Embed(
            title       = "A new beatmap request has been recieved.",
            description = "** **",
            color       = 5516472 # Akatsuki purple.
        )

        embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{map_id}/covers/cover.jpg?1522396856")
        embed.set_author(name=song_name, url=f"https://akatsuki.pw/d/{map_id}", icon_url=AKATSUKI_LOGO)
        embed.set_footer(text=f"Akatsuki's beatmap nomination system v{'%.2f' % ABNS_VERSION}", icon_url="https://nanahira.life/MpgDe2ssQ5zDsWliUqzmQedZcuR4tr4c.jpg")
        embed.add_field(name="Nominator", value=message.author.name)
        embed.add_field(name="Mapper", value=artist)
        embed.add_field(name="Gamemode", value=mode_formatted)
        embed.add_field(name="Highest SR", value="%.2f*" % round(star_rating, 2))
        embed.add_field(name="Highest AR", value=ar)
        embed.add_field(name="Highest OD", value=od)
        embed.add_field(name="Highest Max Combo", value=f"{max_combo}x")
        embed.add_field(name="BPM", value=bpm)

        # Prepare, and send the report to the reporter.
        embed_dm = discord.Embed(
            title       = "Your beatmap nomination request has been sent to Akatsuki's Quality Assurance Team for review.",
            description = "We will review it shortly.",
            color       = 0x00ff00 # Lime green.
        )

        embed_dm.set_thumbnail(url=AKATSUKI_LOGO)
        embed_dm.set_image(url=f"https://assets.ppy.sh/beatmaps/{map_id}/covers/cover.jpg?1522396856")
        embed_dm.set_footer(text=f"Akatsuki's beatmap nomination system v{ABNS_VERSION}", icon_url="https://nanahira.life/MpgDe2ssQ5zDsWliUqzmQedZcuR4tr4c.jpg")

        # Send the embed to the #rank_requests channel.
        request_post = await bot.get_channel(AKATSUKI_RANK_REQUESTS_ID).send(embed=embed)

        # Send the embed to the nominator by DM. TODO: check if we can message the user rather than abusing try-except? that might just be slower lul
        try: await message.author.send(embed=embed_dm)
        except: print(f"Could not DM ({message.author.name}).")

        [request_post.add_reaction(i) for i in ["👎", "👍"]]
        return


    # Message sent in #player-reporting, move to #reports.
    if message.channel.id == AKATSUKI_PLAYER_REPORTING_ID:
        await message.delete() # Delete the message from #player-reporting.

        # Prepare, and send the report in #reports.
        embed = discord.Embed(title="New report recieved.", description="** **", color=0x00ff00)
        embed.set_thumbnail(url=AKATSUKI_LOGO)
        embed.add_field(name="Report content", value=message.content, inline=True)
        embed.add_field(name="Author", value=message.author.mention, inline=True)

        # Prepare, and send the report to the reporter.
        embed_pm = discord.Embed(title="Thank you for the player report.", description="We will review the report shortly.", color=0x00ff00)

        embed_pm.add_field(name="Report content", value=message.content, inline=True)
        embed_pm.set_thumbnail(url=AKATSUKI_LOGO)

        if not message.content.startswith(COMMAND_PREFIX): # Do not pm or link to #reports if it is a command.
            await message.author.send(embed=embed_pm)
            await bot.get_channel(AKATSUKI_REPORTS_ID).send(embed=embed)
        return

    elif message.author != bot.user and message.guild:
        # Message sent in #help, log to db.
        if message.channel.id == AKATSUKI_HELP_ID:
            # Split the content into sentences by periods.
            # TODO: Other punctuation marks!
            sentence_split = message.content.split(".")

            # Default values for properly formatted messages / negative messages.
            properly_formatted, negative = [False] * 2

            debug_print(f"Sentence split: {sentence_split}")

            # After every period, check they have a space and the next sentence starts with a capital letter (ignore things like "...").
            for idx, sentence in enumerate(sentence_split):
                if len(sentence) > 1 and idx:
                    if sentence[0] == " " and sentence[1].isupper(): continue
                    negative = True

            properly_formatted = message.content[0].isupper() and message.content[len(message.content) - 1] in (".", "?", "!") and not negative

            quality = 1
            if any(x in message.content.lower() for x in profanity): quality = 0
            elif any(x in message.content.lower() for x in high_quality) or properly_formatted: quality = 2

            debug_print(f"Quality of message\n\n{message.author}: {message.content} - {quality}")

            # TODO: Store the whole bitch in a single number. 
            # Maybe even do some bitwise black magic shit.
            SQL.execute("INSERT INTO help_logs (id, user, content, datetime, quality) VALUES (NULL, %s, %s, %s, %s)",
                [message.author.id, message.content.encode("ascii", errors="ignore"), time(), quality])

        # Ignore moderators for the following flagging.
        if message.author.guild_permissions.manage_messages:
            PROFANITY_WARNING = "Hello,\n\nYour message in osu!Akatsuki has been removed as it has been deemed "   \
                               "unsuitable.\n\nIf you have any questions, please ask <@285190493703503872>. "      \
                                "\n**Do not try to evade this filter as it is considered fair ground for a ban**." \
                                f"\n\n```" + safe_discord(message.author.name) + ':' +  safe_discord(message.content) + "```"

            # Primary filters.
            # These are looking for direct comparison results.
            for split in message.content.lower().split(" "):
                if any(split.startswith(i) for i in filters) or any(i in message.content.lower() for i in substring_filters):
                    await message.delete()

                    try: await message.author.send(PROFANITY_WARNING)
                    except: print(f"{Fore.LIGHTRED_EX}Could not warn {message.author.name}.")

                    debug_print(f"Filtered message | '{message.author.name}: {message.content}'")

                    SQL.execute("INSERT INTO profanity_logs (id, user, content, datetime) VALUES (NULL, %s, %s, %s)",
                        [message.author.id, message.content.encode("ascii", errors="ignore"), time()])

                    return

        if message.channel.id != AKATSUKI_BOTSPAM_ID:
            message_string = f"%s{message.created_at} [{message.guild if message.guild else ''} {message.channel}] {message.author}: {message.content}"

            _c = None
            if not message.guild: _c = Fore.YELLOW
            elif "cmyui" in message.content.lower(): _c = Fore.CYAN
            elif message.guild.id == AKATSUKI_SERVER_ID:  _c = Fore.BLUE

            print(message_string % _c)
            del _c

        # Finally, process commands.
        await bot.process_commands(message)
    return

SQL.execute("SELECT value_string FROM aika_settings WHERE name = %s", ["rewrite_token"])
bot.run(SQL.fetchone()[0], bot=True, reconnect=True)

# Clean up
print("", "Force-quit detected. Cleaning up Aika before shutdown..", "Cleaning up MySQL variables..", sep="\n")
SQL.close()
cnx.close()
print("Cleaning complete.")