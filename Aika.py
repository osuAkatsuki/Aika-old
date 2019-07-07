import discord
from discord.ext import commands
import mysql.connector
from mysql.connector import errorcode
import time

# TODO: stop using these!
from colorama import init
from colorama import Fore, Back, Style

# Initialize colorama.
init(autoreset=True)

# Initalize values as Nonetype for now.
SQL_HOST, SQL_USER, SQL_PASS, SQL_DB = [None] * 4

# Config
config = open('config.ini', 'r')
config_contents = config.read().split("\n")
print(config_contents)
for line in config_contents:
    line = line.split("=")
    if line[0].strip() == "SQL_HOST": # IP Address for SQL.
        SQL_HOST = line[1].strip()
    elif line[0].strip() == "SQL_USER": # Username for SQL.
        SQL_USER = line[1].strip()
    elif line[0].strip() == "SQL_PASS": # Password for SQL.
        SQL_PASS = line[1].strip()
    elif line[0].strip() == "SQL_DB": # DB name for SQL.
        SQL_DB = line[1].strip()
    else: # Config value is unknown. continue iterating anyways.
        continue

# MySQL
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

# Aika's version.
AIKA_VERSION = 4.11

# Akatsuki settings.
AKATSUKI_SERVER_ID           = 365406575893938177 # Guild ID.
AKATSUKI_GENERAL_ID          = 592490140497084436 # ID for #general.
AKATSUKI_HELP_ID             = 365413867167285249 # ID for #help.
AKATSUKI_VERIFY_ID           = 596662084339761172 # ID for #verify.
AKATSUKI_PLAYER_REPORTING_ID = 367068661837725706 # ID for #player_reporting.
AKATSUKI_REPORTS_ID          = 367080772076568596 # ID for #reports.
AKATSUKI_NSFW_STRAIGHT_ID    = 428460752698081291 # ID for #nsfw.
AKATSUKI_NSFW_TRAPS_ID       = 505960162411020288 # ID for #nsfw-traps.
AKATSUKI_RANK_REQUEST_ID     = 597200076561055795 # ID for #rank-request (User).
AKATSUKI_RANK_REQUESTS_ID    = 557095943602831371 # ID for #rank-requests (Staff).
AKATSUKI_BOTSPAM_ID          = 369829943372152833 # ID for #botspam.

# Aika's command prefix.
COMMAND_PREFIX = '!'

# Akatsuki's logo.
# To be used mostly for embed thumbnails.
AKATSUKI_LOGO                = "https://akatsuki.pw/static/logos/logo.png"
CRAB_EMOJI                   = "https://cdn.discordapp.com/attachments/365406576548511745/591470256497754112/1f980.png"

# A list of filters.
# These are to be used to wipe messages that are deemed inappropriate,
# or break rules. For the most part, these are of other private servers,
# as required by rule #2 of the Akatsuki Discord & Chat Rules
# (https://akatsuki.pw/doc/rules).
filters       = [
                # Paypal
                "https://pp.me", "http://pp.me", "https://paypal.me", "http://paypal.me",

                # osu! private servers
                "yozora", "ainu", "okamura", "kotorikku", "kurikku", "kawata",
                "ryusei", "ryu-sei", "enjuu", "verge", "katori", "osu-thailand",
                "gatari", "hidesu", "hiragi", "asuki", "mikoto", "homaru", "awasu",

                # Discord links
                "https://discord.gg/", "http://discord.gg/", "https://discordapp.com/channels", "http://discordapp.com/channels",

                # Bad boy substances
                "lsd", "dmt", "shrooms"
                ]

# A list of message (sub)strings that we will use to deem
# a quantifiable value for the "quality" of a message.
profanity     = ["nigg", "n1gg", "retard", "idiot",
                 "fuck off", "shut the fuck up", "??"]

high_quality  = ["!faq", "!help", "welcome", "have a good", "enjoy", "no problem",
                 "of course", "can help", "i can", "how can i help you"]

# Assign discord owner value.
SQL.execute("SELECT value_string FROM aika_settings WHERE name = 'discord_owner'")
discord_owner = int(SQL.fetchone()[0])


def debug_print(string):
    """
    Print a debug message to the console.

    Example in use:      https://nanahira.life/dOgXljmmKW336gro3Ts5gJmU7P4hNDZz.png

    :param string:       The message to be printed to the console.
    """

    # Debug value
    SQL.execute("SELECT value_int FROM aika_settings WHERE name = 'debug'")
    debug = SQL.fetchone()[0]

    if debug:
        print(f"{Fore.MAGENTA}\n{string}\n")


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


cogs = ['cogs.staff', 'cogs.user']


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - {bot.user.id}")
    await bot.change_presence(activity=discord.Game(name="osu!Akatsuki", url="https://akatsuki.pw/", type=1))
    for cog in cogs:
        bot.load_extension(cog)

    # Announce online status to #general if we're on a server build of Aika.
    SQL.execute("SELECT value_int FROM aika_settings WHERE name = 'server_build'")
    server_build = bool(SQL.fetchone()[0])

    if server_build:
        # Get the server's latest version of Aika run.
        SQL.execute("SELECT value_int FROM aika_settings WHERE name = 'version_latest'")
        version_latest = SQL.fetchone()[0]

        SQL.execute("UPDATE aika_settings SET value_int = %s WHERE name = 'version_latest'", [AIKA_VERSION])

        # If the server version mismatches the version of the code, display the update.
        if version_latest != AIKA_VERSION:
            announce_title = f"Aika has been updated to v{AIKA_VERSION}. (Previous: v{version_latest})"
        else:
            announce_title = f"Aika v{AIKA_VERSION} Online"

        # Configure, and send the embed to #general.
        announce_online = discord.Embed(
            title       = announce_title,
            description = "Ready for commands <3\n\nAika is osu!Akatsuki's [open source](https://github.com/osuAkatsuki/Aika) "
                          "discord bot.\n\n[Akatsuki](https://akatsuki.pw)\n[Support Akatsuki](https://akatsuki.pw/support)",
            color       = 0x00ff00)

        announce_online.set_footer(icon_url=CRAB_EMOJI, text="Thank you for playing!")
        announce_online.set_thumbnail(url=AKATSUKI_LOGO)
        await bot.get_channel(AKATSUKI_GENERAL_ID).send(embed=announce_online)

    return


@bot.event
async def on_message(message):
    await bot.wait_until_ready()

    if message.author.id != discord_owner: # Regular user
        if message.content.split(' ')[0][1:7] == "verify" and message.channel.id == AKATSUKI_VERIFY_ID: # Verify command.
            await message.author.add_roles(discord.utils.get(message.guild.roles, name="Members"))
            await message.delete()
            return
        
        # Prevent client crashing.. or atleast try a little bit.
        if not all(ord(char) < 128 for char in message.content) and len(message.content) > 1500:
            await message.delete()
            return

    else: # Owner

        if message.content.split(' ')[0][1:] == "reload":
            cog_name = message.content.split(' ')[1].lower()
            if cog_name in ("staff", "user"):
                bot.reload_extension(f"cogs.{cog_name}")
                await message.channel.send(f"Reloaded extension {cog_name}.")
            else:
                await message.channel.send(f"Invalid extension {cog_name}.")
            return


    if message.channel.id in (AKATSUKI_NSFW_STRAIGHT_ID, AKATSUKI_NSFW_TRAPS_ID):
        def check_content(m): # Don't delete links or images.
            if "http" in message.content or message.attachments:
                return False
            return True

        if check_content(message):
            await message.delete()
        return


    # Message sent in #rank-request, move to #rank-requests.
    if message.channel.id == AKATSUKI_RANK_REQUEST_ID:
        await message.delete()

        if not any(required in message.content for required in ("akatsuki.pw", "osu.ppy.sh")) or len(message.content) > 30: # Should not EVER be over 30 characters.
            await message.author.send("Your beatmap request was incorrectly formatted, and thus has not been submitted. Please use the old osu links for the time being. (e.g. https://osu.ppy.sh/b/123)")
            return

        # TODO: New osu link support.
        if "://" in message.content: # Support both links like "https://osu.ppy.sh/b/123" AND "osu.ppy.sh/b/123". Also allow both /s/ and /b/ links.
            partitions = message.content.split("/")[3:]
        else:
            partitions = message.content.split("/")[1:]

        beatmapset = partitions[0] == "s" # Link is a beatmapset_id link, not a beatmap_id link.
        map_id = partitions[1] # Can be SetID or MapID.

        if not beatmapset: # If the user used a /b/ link, let's turn it into a set id.
            SQL.execute("SELECT beatmapset_id FROM beatmaps WHERE beatmap_id = %s LIMIT 1", [map_id])
            map_id = SQL.fetchone()[0]

        # Do this so we can check if any maps in the set are ranked or loved.
        # If they are, the QAT have most likely already determined statuses of the map.
        SQL.execute("SELECT mode, ranked FROM beatmaps WHERE beatmapset_id = %s ORDER BY ranked DESC LIMIT 1", [map_id])
        sel = SQL.fetchone()

        mode   = sel[0]
        status = sel[1]

        if not sel: # We could not find any matching rows with the map_id.
            await message.author.send("That map seems to be invalid. Quoi?")
            return

        if status in (2, 5): # Map is already ranked/loved
            await message.author.send(f"Some (or all) of the difficulties in the beatmap you requested already seem to be {'ranked' if status == 2 else 'loved'} on the Akatsuki server!\n\nIf this is false, please contact a QAT directly to proceed.")
            return

        # Sort out mode to be used to check difficulty.
        # Also have a formatted one to be used for final post.
        if mode == 0:
            mode = "std"
            mode_formatted = "osu!"
        elif mode == 1:
            mode = "taiko"
            mode_formatted = "osu!taiko"
        elif mode == 2:
            mode = "ctb"
            mode_formatted = "osu!catch"
        else:
            mode = "mania"
            mode_formatted = "osu!mania"

        # Select map information.
        SQL.execute(f"SELECT song_name, ar, od, max_combo, bpm, difficulty_{mode} FROM beatmaps WHERE beatmapset_id = %s ORDER BY difficulty_{mode} DESC LIMIT 1", [map_id])
        bdata = SQL.fetchone()

        # Return from DB.
        song_name   = bdata[0]
        ar          = bdata[1]
        od          = bdata[2]
        max_combo   = bdata[3]
        bpm         = bdata[4]
        star_rating = bdata[5]

        # Create embeds.
        embed = discord.Embed(
            title       = "A new beatmap request has been recieved.",
            description = "** **",
            color       = 5516472
        )

        embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{map_id}/covers/cover.jpg?1522396856")
        embed.set_author(name=song_name, url=f"https://akatsuki.pw/d/{map_id}", icon_url=AKATSUKI_LOGO)
        embed.set_footer(text="Akatsuki's beatmap nomination system v2.0", icon_url="https://nanahira.life/MpgDe2ssQ5zDsWliUqzmQedZcuR4tr4c.jpg")
        embed.add_field(name="Nominator", value=message.author.name)
        embed.add_field(name="Gamemode", value=mode_formatted)
        embed.add_field(name="Highest SR", value=round(star_rating, 2))
        embed.add_field(name="Highest AR", value=ar)
        embed.add_field(name="Highest OD", value=od)
        embed.add_field(name="Highest Max Combo", value=max_combo)
        embed.add_field(name="BPM", value=bpm)

        # Prepare, and send the report to the reporter.
        embed_dm = discord.Embed(
            title       = "Your beatmap nomination request has been sent to Akatsuki's Quality Assurance Team for review.",
            description = "We will review it shortly.",
            color       = 0x00ff00
        )

        embed_dm.set_thumbnail(url=AKATSUKI_LOGO)
        embed_dm.set_image(url=f"https://assets.ppy.sh/beatmaps/{map_id}/covers/cover.jpg?1522396856")
        embed_dm.set_footer(text="Akatsuki's beatmap nomination system v2.0", icon_url="https://nanahira.life/MpgDe2ssQ5zDsWliUqzmQedZcuR4tr4c.jpg")

        # Send the embed to the nominator by DM.
        await message.author.send(embed=embed_dm)

        # Send the embed to the #rank_requests channel.
        request_post = await bot.get_channel(AKATSUKI_RANK_REQUESTS_ID).send(embed=embed)

        # Add reaction thumbs to post for votes.
        await request_post.add_reaction("👍")
        await request_post.add_reaction("👎")
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

    elif message.author != bot.user:
        messagelen = len(message.content)

        properly_formatted = False

        if messagelen > 0:
            sentence_split = message.content.split(".")
            negative = False

            debug_print(f"Sentence split: {sentence_split}")

            # After every period, check they have a space and the next sentence starts with a capital letter (ignore things like "...").
            for idx, sentence in enumerate(sentence_split):
                if len(sentence) > 1 and idx != 0:
                    if sentence[0] == " " and sentence[1].isupper():
                        continue
                    negative = True

            properly_formatted = message.content[0].isupper() and message.content[messagelen - 1] in (".", "?", "!") and not negative

        # Message sent in #help, log to db.
        if message.channel.id == AKATSUKI_HELP_ID:
            quality = 1

            # Profanity before high quality and proper formatting.
            if any(x in message.content.lower() for x in profanity):
                quality = 0
            elif any(x in message.content.lower() for x in high_quality) or properly_formatted:
                quality = 2

            debug_print(f"Quality of message\n\n{message.author}: {message.content} - {quality}")

            SQL.execute("INSERT INTO help_logs (id, user, content, datetime, quality) VALUES (NULL, %s, %s, %s, %s)",
                [message.author.id, message.content.encode('ascii', errors='ignore'), time.time(), quality])

        if not message.author.guild_permissions.manage_messages:
            for split in message.content.lower().split(" "):
                if any(split.startswith(individual_filter) for individual_filter in filters):
                    SQL.execute("INSERT INTO profanity_filter (user, message, time) VALUES (%s, %s, %s)",
                        [message.author.id, message.content.encode('ascii', errors='ignore'), time.time()])

                    await message.delete()
                    await message.author.send(
                        "Hello,\n\nYour message in osu!Akatsuki has been removed as it has been deemed "
                        "unsuitable.\n\nIf you have any questions, please ask <@285190493703503872>. "
                        "\n**Do not try to evade this filter as it is considered fair ground for a ban**."
                        f"\n\n```{message.content.replace('`', '')}: {message.content.replace('`', '')}```")

                    debug_print(f"Filtered message | '{message.author}: {message.content}'")
                    return

        if message.channel.id != AKATSUKI_BOTSPAM_ID: # Don't print anything from botspam. This helps reduce a LOT of clutter.

            # Formatted message to be printed to console on message event.
            message_string = f"{message.created_at} [{message.guild if message.guild is not None else ''} {message.channel}] {message.author}: {message.content}"

            if message.guild is None: # Private message.
                print(Fore.YELLOW + Style.BRIGHT + message_string)
            elif "cmyui" in message.content.lower(): # cmyui was mentioned in the message.
                print(Fore.CYAN + Style.BRIGHT + message_string)
            elif message.guild.id == AKATSUKI_SERVER_ID: # The server is Akatsuki.
                print(Fore.BLUE + Style.BRIGHT + message_string)
            else: # Regular message.
                print(message_string)

        # Finally, process commands.
        await bot.process_commands(message)
    return

SQL.execute("SELECT value_string FROM aika_settings WHERE name = 'rewrite_token'")
bot.run(SQL.fetchone()[0], bot=True, reconnect=True)

# Clean up
print("\nForce-quit detected. Cleaning up Aika before shutdown..\nCleaning up MySQL variables..")
SQL.close()
cnx.close()
print("Cleaning complete.")
