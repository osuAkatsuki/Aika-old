"""
    Aika - osu!Akatsuki's discord bot

    Yo. This is coded by cmyui, a person who is in.. let's call it "coding middle school".

    Expect my coding style to change roughly every week, for things to change at all times, and for code to be inconsistent.
    Did you get that? Very inconsistent. This is because I am in the process of learning not only python, but also a hell
    of a lot of other languages (such as c++, where my style and formatting is very different!).

    These things influence my coding style a lot, and so do friends of mine.

    This code is basically open source for the sake of transparency, with a spice of being able to keep track
    of where I am in my learning.

    I can't really see any time when you'd want to use this code for your own project, but who knows, Atoka did apparently!

    Enjoy the shitshow,
    cm/yui
"""

# Big list of TODO for when I run out of ideas
"""
    1: Move vars such as debug to DB
    2. Find a better way to do quality of helplog reports
    3. Make userstats command use username thing in API like the $recent command does.
    4. Add relax support to both here and Akatsuki's API for the $recent command to work. HaHa it Matchd THe Line ABove it when i Typed $recent command HAHa.!
    5. Unhardcode the responses for a hell of a lot of commands. Or just remove the commands. WHo cares!
    6. use any() where applicable
    7. cool shit for $linkosu and $prune. More functionality More functionality More functionality More functionality More functionality More functionality More functionality More functionality More functionality More functionality More functionality 
    8. time command adjust for server time.
"""

# Library imports.
import discord
import asyncio
import configparser
import logging
import traceback
import requests
import json
import random
from colorama import init
from colorama import Fore, Back, Style
from urllib.parse import urlencode
import mysql.connector
from mysql.connector import errorcode
import re
import time
from datetime import datetime

# Initialize colorama.
init(autoreset=True)

# Discord Client.
client = discord.Client()

# Configuration.
config = configparser.ConfigParser()
config.sections()
config.read("config.ini")

# MySQL
try:
    cnx = mysql.connector.connect(
        user       = config['mysql']['user'],
        password   = config['mysql']['passwd'],
        host       = config['mysql']['host'],
        database   = config['mysql']['db'],
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


""" Constants """

# The version number of Aika!
AIKA_VERSION                 = 3.12               # Aika's version number.

ERROR_BAR_LEN                = 100                # Length of the bars for error handler (https://nanahira.life/1uRp27N5TCipZ3Hs12o5PQLEOTyHHYUE.png).

# Akatsuki settings
AKATSUKI_SERVER_ID           = 365406575893938177 # Guild ID.
AKATSUKI_GENERAL_ID          = 592490140497084436 # ID for #general.
AKATSUKI_HELP_ID             = 365413867167285249 # ID for #help.
AKATSUKI_VERIFY_ID           = 459856640049676299 # ID for #verify.
AKATSUKI_PLAYER_REPORTING_ID = 367068661837725706 # ID for #player_reporting.
AKATSUKI_REPORTS_ID          = 367080772076568596 # ID for #reports.
AKATSUKI_RANK_REQUESTS_ID    = 557095943602831371 # ID for #rank_requests.
AKATSUKI_NSFW_STRAIGHT_ID    = 428460752698081291 # ID for #nsfw
AKATSUKI_NSFW_TRAPS_ID       = 505960162411020288 # ID for #nsfw-traps
AKATSUKI_IP_ADDRESS          = "51.79.17.191"     # Akatsuki's osu! server IP.

COMMAND_PREFIX               = "!"                 # The bot's command prefix.

FAQ_LIST_SPACING             = 12                  # When listing FAQ or INFO, use this many spaces between the divider.


# A list of filters.
# These are to be used to wipe messages that are deemed inappropriate,
# or break rules. For the most part, these are of other private servers,
# as required by rule #2 of the Akatsuki Discord & Chat Rules
# (https://akatsuki.pw/doc/rules).
filters       = [
                # Paypal
                "pp.me", "paypal.me",
                
                # osu! private servers
                "yozo", "y0zo", "yoz0", "y0z0",
                "ainu", "okamura", "kotorikku", "kurikku", "kawata",
                "ryusei", "ryu-sei", "enjuu", "verge", "katori",
                "osu-thailand", "gatari", "hidesu", "hiragi",
                "asuki", "mikoto", "homaru", "awasu",

                # Discord links
                "discord.gg/", "discordapp.com/channels",

                # Bad boy substances
                "lsd", "dmt", "shrooms"
                ]

# A list of message (sub)strings that we will use to deem
# a quantifiable value for the "quality" of a message.
profanity     = [
                "nigg", "n1gg", "retard", "idiot",
                "fuck off", "shut the fuck up", "??"
                ]

high_quality  = [
                "!faq", "!help", "welcome", "have a good",
                "enjoy", "no problem", "of course",
                "can help", "i can", "how can i help you"
                ]

# Akatsuki's logo.
# To be used mostly for embed thumbnails.
akatsuki_logo = "https://akatsuki.pw/static/logos/logo.png"
#aika_pfp     = "https://akatsuki.pw/static/characters/quaver.png"
aika_pfp      = "https://nanahira.life/a70CRNhGGPp2NgnyEku9X5fgYLBrqIGY.png"
crab          = "https://cdn.discordapp.com/attachments/365406576548511745/591470256497754112/1f980.png"

# Debug value
SQL.execute("SELECT value_int FROM aika_settings WHERE name = 'debug'")
debug = SQL.fetchone()[0]


# osu! Mods
NOMOD       = 0
NOFAIL      = 1
EASY        = 2
TOUCHSCREEN = 4
HIDDEN      = 8
HARDROCK    = 16
SUDDENDEATH = 32
DOUBLETIME  = 64
RELAX       = 128
HALFTIME    = 256
NIGHTCORE   = 512
FLASHLIGHT  = 1024
AUTOPLAY    = 2048
SPUNOUT     = 4096
RELAX2      = 8192
PERFECT     = 16384
KEY4        = 32768
KEY5        = 65536
KEY6        = 131072
KEY7        = 262144
KEY8        = 524288
KEYMOD      = 1015808
FADEIN      = 1048576
RANDOM      = 2097152
LASTMOD     = 4194304
KEY9        = 16777216
KEY10       = 33554432
KEY1        = 67108864
KEY3        = 134217728
KEY2        = 268435456
SCOREV2     = 536870912

""" Functions """


def osu_mods(mods): # From: Ripple source

	resp = "+" # At the start to show like +HDDT, +HDRX, etc.
	if not mods:
		return ""
	if mods & NOFAIL > 0:
		resp += "NF"
	if mods & EASY > 0:
		resp += "EZ"
	if mods & HIDDEN > 0:
		resp += "HD"
	if mods & HARDROCK > 0:
		resp += "HR"
	if mods & DOUBLETIME > 0:
		resp += "DT"
	if mods & HALFTIME > 0:
		resp += "HT"
	if mods & FLASHLIGHT > 0:
		resp += "FL"
	if mods & SPUNOUT > 0:
		resp += "SO"
	if mods & TOUCHSCREEN > 0:
		resp += "TD"
	if mods & RELAX > 0:
		resp += "RX"
	return resp


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
        print(Fore.MAGENTA + "\nDEBUG: {}\n".format(string))


async def send_message_formatted(type, message, first_line, string_array=[]):
    """
    Send a response via discord to the channel.

    Example in use:      https://nanahira.life/qxb2f7j0EvrR7DftvHfBxosXTvtL5s9u.png

    :param type:         The "type" of the response.
                         I.E is the message supposed to signify an error?
    :param message:      The message object provided from discord.
    :param first_line:   The first line of the response. The only one required.
    :param string_array: The array of strings to follow. Optional.
    """

    # Choose what kind of status to open the response with.
    # TODO: emojis
    if type == "error":
        status = "🔴"
    elif type == "success":
        status = "🔵"
    else: # neutral
        status = type

    # Build the response string.
    resp =  "{status} **{author_name}**, {first_line}{punctuation}\n".format(
        status      = status,
        author_name = message.author.name,
        first_line  = (first_line[0].lower() if first_line[0] != "I" and first_line[0:8] != "Akatsuki" else first_line[0]) + first_line[1:],
        punctuation = "." if first_line[len(first_line) - 1] not in ("?", "!", ".") else "")

    # Add lines to the response.
    for line in string_array:
        resp += "        {string}\n".format(string=line)

    # Send the response off to discord.
    await message.channel.send(resp)


# Startup, after login action.
@client.event
async def on_ready():
    print(Fore.GREEN + "\nAuthentication Successful.\n{} | {}\n--------------------------\n".format(client.user.name, client.user.id))

    debug_print("\nDebug: {}\n".format(bool(debug)))

    # Announce online status to #general if we're on a server build of Aika.
    SQL.execute("SELECT value_int FROM aika_settings WHERE name = 'server_build'")
    server_build = bool(SQL.fetchone())

    if server_build:
        # Get the server's latest version of Aika run.
        SQL.execute("SELECT value_int FROM aika_settings WHERE name = 'version_latest'")
        version_latest = SQL.fetchone()

        # If the server version mismatches the version of the code, display the update.
        if version_latest != AIKA_VERSION:
            announce_title = "Aika has been updated to v{}. (Previous: v{})".format(AIKA_VERSION, version_latest)
        else:
            announce_title = "Aika v{} Online".format(AIKA_VERSION)

        # Configure, and send the embed to #general.
        announce_online = discord.Embed(
            title       = announce_title,
            description = "Ready for commands <3\n\nAika is osu!Akatsuki's "
                          "[open source](https://github.com/osuAkatsuki/Aika) "
                          "discord bot.\n\n[Akatsuki](https://akatsuki.pw)\n"
                          "[Support Akatsuki](https://akatsuki.pw/support)",
            color       = 0x00ff00)

        announce_online.set_footer(icon_url=crab, text="Thank you for playing!")
        announce_online.set_thumbnail(url=akatsuki_logo)
        await client.get_channel(AKATSUKI_GENERAL_ID).send(embed=announce_online)


# On exceptions, don't make the whole thing die :).
@client.event
async def on_error(event, *args):
    for arg in args:
        print(Fore.RED + "\n\nAn exception has occurred.\n\n" + Fore.LIGHTRED_EX + "Exception: {exception}\n\n{content}\n\n{traceback}\n\n".format(
            exception = Fore.LIGHTBLUE_EX + event + Fore.LIGHTRED_EX,
            content   = Fore.LIGHTBLUE_EX + "{}: {}".format(arg.author, arg.content) + Fore.LIGHTRED_EX,
            traceback = Fore.LIGHTBLUE_EX + ("-" * ERROR_BAR_LEN) + "\n" + Fore.LIGHTRED_EX + traceback.format_exc() + Fore.LIGHTBLUE_EX + ("-" * ERROR_BAR_LEN) + Fore.LIGHTRED_EX))


@client.event
async def on_message(message):
    await client.wait_until_ready()

    # Prevent client crashing.. or atleast try a little bit.
    if not all(ord(char) < 128 for char in message.content) and len(message.content) > 1500:
        await message.delete()
        return

    if message.channel.id in (AKATSUKI_NSFW_STRAIGHT_ID, AKATSUKI_NSFW_TRAPS_ID):
        def check_content(m): # Don't delete links or images.
            if "http" in message.content or message.attachments:
                return False
            else: # honestly not sure if this is safe without else in async idk how this shit work yehaw.
                return True

        if check_content(message):
            await message.delete()
        return

    # Message sent in #player-reporting, move to #reports.
    if message.channel.id == AKATSUKI_PLAYER_REPORTING_ID:
        await message.delete() # Delete the message from #player-reporting.
        return

        # Prepare, and send the report in #reports.
        embed = discord.Embed(title="New report recieved.", description='** **', color=0x00ff00)
        embed.set_thumbnail(url=akatsuki_logo)
        embed.add_field(name="Report content", value=message.content, inline=True)
        embed.add_field(name="Author", value=message.author.mention, inline=True)

        # Prepare, and send the report to the reporter.
        embedPrivate = discord.Embed(title="Thank you for the player report.", description="We will review the report shortly.", color=0x00ff00)

        embedPrivate.add_field(name="Report content", value=message.content, inline=True)
        embedPrivate.set_thumbnail(url=akatsuki_logo)

        if not message.content.startswith(COMMAND_PREFIX): # Do not pm or link to #reports if it is a command.
            await message.author.send(embed=embedPrivate)
            await client.get_channel(AKATSUKI_REPORTS_ID).send(embed=embed)
            return

    # Request sent in rank_requests.
    elif message.channel.id == AKATSUKI_RANK_REQUESTS_ID:
        # Add base thumbs to all requests.
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        return

    elif message.author != client.user:
        messagelen = len(message.content)

        properly_formatted = False

        if messagelen > 0:
            properly_formatted = message.content[0].isupper() and message.content[messagelen - 1] in (".", "?", "!")

        # Message sent in #help, log to db.
        if message.channel.id == AKATSUKI_HELP_ID:
            quality = 1

            # Profanity before high quality and proper formatting.
            if any(x in message.content.lower() for x in profanity):
                quality = 0
            elif any(x in message.content.lower() for x in high_quality) or properly_formatted:
                quality = 2

            debug_print("Quality of message\n\n{} - {}".format("{}: {}".format(message.author, message.content), quality))

            SQL.execute("INSERT INTO help_logs (id, user, content, datetime, quality) VALUES (NULL, %s, %s, %s, %s)", [message.author.id, message.content.encode('ascii', errors='ignore'), int(time.time()), quality])

        elif not message.author.guild_permissions.manage_messages:
            for split in message.content.lower().split(" "):
                if any(x == split for x in filters):
                    SQL.execute("INSERT INTO profanity_filter (user, message, time) VALUES (%s, %s, %s)", [message.author.id, message.content.encode('ascii', errors='ignore'), int(time.time())])

                    await message.delete()
                    await message.author.send(
                        "Hello,\n\nYour message in osu!Akatsuki "
                        "has been removed as it has been deemed "
                        "unsuitable.\n\nIf this makes no sense, "
                        "please report it to <@285190493703503872>. "
                        "\n**Do not try to evade this filter as it is "
                        "considered fair ground for a ban**.\n\n```{}```"
                        .format(message.content.replace("`", "")))

                    debug_print("Filtered message | '{}: {}'".format(message.author, message.content))
                    return

        # Private messages.
        if message.guild is None: # Private message
                print(Fore.YELLOW + Style.BRIGHT + "{} [{}] {}: {}".format(message.created_at, message.channel, message.author, message.content))
        elif "cmyui" in message.content.lower(): # cmyui mentioned
                print(Fore.CYAN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.created_at, message.guild, message.channel, message.author, message.content))
        elif message.guild.id == AKATSUKI_SERVER_ID: # The server is akatsuki.
            print(Fore.BLUE + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.created_at, message.guild, message.channel, message.author, message.content))
        else: # Regular message.
            print("{} [{} ({})] {}: {}".format(message.created_at, message.guild, message.channel, message.author, message.content))

        # Handle user verification before the command section. This should speed things up a bit!
        if message.content.split(' ')[0][1:] == "verify" and message.channel.id == AKATSUKI_VERIFY_ID: # Verify command.
            if message.author.id != config['discord']['owner_id']: # Dont for cmyui, he's probably pinging @everyone to verify.
                await message.author.add_roles(discord.utils.get(message.guild.roles, name="Members"))
                await message.delete()
            return

        if message.content.startswith(COMMAND_PREFIX):

            # First of all, make a simpler way to deal with message content so u don't develop stage 4 cancer.
            messagecontent = message.content.split(" ")
            command = messagecontent[0][1:].lower()

            # Change the bot's displayed game.
            if command == "game":
                if not message.author.guild_permissions.manage_webhooks: # Webhook since it's a bot thing
                    await send_message_formatted("error", message, "you lack sufficient privileges to use this command")
                    return

                # Change your discord users status / game.
                game = ' '.join(messagecontent[1:]).strip() # Get the game.
                if game: # Game also changed.
                    """
                    game Variables:
                    name = name of the game
                    url = link for the game (usually for streaming probably)
                    type = boolean to show whether streaming or not
                    """

                    await client.change_presence(game=discord.Game(name=game, url='https://akatsuki.pw/', type=0))

                    await send_message_formatted("success", message, "game successfully changed to: {}".format(game))
                else:
                    await send_message_formatted("error", message, "please specify a game name")
                    return # dont delete if we fuck up

                await message.delete()
                return

            elif command in ("hs", "helplogs"):
                with message.channel.typing():
                    if not message.author.guild_permissions.manage_roles:
                        await send_message_formatted("error", message, "you lack sufficient privileges to use this command")
                        return

                    if not len(messagecontent) > 1:
                        await send_message_formatted("error", message, "this command requires an argument")
                        return


                    userID = re.findall('\d+', messagecontent[1])[0]

                    SQL.execute("SELECT quality FROM help_logs WHERE user = %s", [userID])

                    logs = SQL.fetchall()

                    debug_print(logs)

                    positive, neutral, negative = 0, 0, 0 # Uh huh

                    if logs is not None:
                        for log in logs:
                            if not log[0]:
                                negative += 1
                            elif log[0] == 1:
                                neutral += 1
                            else:
                                positive += 1

                        embed = discord.Embed(title="Report | {}".format(userID), description='** **', color=0x00ff00)
                        embed.set_thumbnail(url=akatsuki_logo)
                        embed.add_field(name="Total", value=positive + neutral + negative, inline=True)
                        embed.add_field(name="Positive", value=positive, inline=True)
                        embed.add_field(name="Neutral", value=neutral, inline=True)
                        embed.add_field(name="Negative", value=negative, inline=True)
                        await message.channel.send(embed=embed)
                    else:
                        await send_message_formatted("error", message, "no logs could be found on the specified user")
                    return

            # Flip debug 1/0 in db.
            elif command in ("d", "debug"):
                if not message.author.guild_permissions.manage_webhooks:
                    await send_message_formatted("error", message, "you lack sufficient privileges to use this command")
                    return

                SQL.execute("UPDATE aika_settings SET value_int = 1 - value_int WHERE name = 'debug'")
                debug_print("Debug enabled.")
                await message.delete()
                return

            # Command to remind my dumbass which parts of embeds can be links.
            elif command == "cmyuiisretarded":
                if not message.author.guild_permissions.manage_webhooks:
                    await send_message_formatted("error", message, "you lack sufficient privileges to use this command")
                    return

                embed = discord.Embed(title="[cmyui](https://akatsuki.pw/u/1001)", description='** **', color=0x00ff00)
                embed.add_field(name="[cmyui](https://akatsuki.pw/u/1001)", value="[cmyui](https://akatsuki.pw/u/1001)")
                embed.set_footer(icon_url=akatsuki_logo, text="[cmyui](https://akatsuki.pw/u/1001)")
                await message.channel.send(embed=embed)
                return

            # Error on purpose. This is used to test our error handler!
            elif command in ("e", "error"):
                if not message.author.guild_permissions.manage_webhooks:
                    await send_message_formatted("error", message, "you lack sufficient privileges to use this command")
                    return

                await message.delete()
                None.isdigit() # Error, no need to return

            # This will probably only be used when bot goes down and text is sent, since its automated.
            elif command in ("clearnsfw"):
                if not message.author.guild_permissions.manage_messages:
                    await send_message_formatted("error", message, "you lack sufficient privileges to use this command")
                    return
                
                def check_content(m): # Don't delete links or images.
                    if "http" in m.content or m.attachments:
                        return False
                    else: # honestly not sure if this is safe without else in async idk how this shit work yehaw.
                        return True

                _nsfw_straight = await client.fetch_channel(AKATSUKI_NSFW_STRAIGHT_ID)
                _nsfw_traps    = await client.fetch_channel(AKATSUKI_NSFW_TRAPS_ID)

                debug_print("Got #nsfw and #nsfw_traps channel objects.")

                debug_print("Deleting from #nsfw.")
                nsfw_straight  = await _nsfw_straight.purge(limit=1000, check=check_content)
                debug_print("Deleting from #nsfw-traps.")
                nsfw_traps     = await _nsfw_traps.purge(limit=1000, check=check_content)
                debug_print("Complete. {} messages removed.".format(len(nsfw_straight) + len(nsfw_traps)))

                await send_message_formatted("error", message, "cleaned NSFW channels. {} messages deleted.".format(len(nsfw_straight) + len(nsfw_traps)))
                return

            # Regular user commands for the most part below

            # Command which grabs the user's info for relax or regular from the Akatsuki API.
            # Syntax: $user/$stats <username> <-rx>
            # TODO: Change to one request by username (&type=username&name={}).
            elif command in ("user", "stats"):
                if not len(messagecontent) > 1:
                    await send_message_formatted("error", message, "this command requires atleast one argument (username)")
                    return

                with message.channel.typing():
                    username = messagecontent[1]
                    if len(messagecontent) > 2:
                        relax = messagecontent[2]
                    else:
                        relax = None

                    if relax not in (None, "-rx"): # They probably used a username with a space since relax var is something else. Or typo
                        if "rx" not in relax:
                            await send_message_formatted("error", message, "please use underscores in your username rather than spaces")
                            return
                        else:
                            await send_message_formatted("error", message, "incorrect syntax.",
                                ["Please use the syntax `> {}{} <username_with_underscores> <-rx (Optional)>".format(COMMAND_PREFIX, command)])
                            return
                    else:
                        __user = requests.get('https://akatsuki.pw/api/v1/get_user?u={}'.format(username)).text

                        if len(__user) == 2:
                            await send_message_formatted("error", message, "either that user does not exist, or your syntax was incorrect",
                                ["Syntax: `{}stats username_spaced_like_this (-rx)`".format(COMMAND_PREFIX)])
                            return

                        _user = json.loads(__user)

                        userID = int(_user[0]["user_id"])

                        resp = requests.get('https://akatsuki.pw/api/v1/users/{rx}full?id={userID}'.format(rx="rx" if relax == '-rx' else '', userID=userID), timeout=3).text

                        user = json.loads(resp)

                        debug_print("Raw JSON:\n{}\n\nMinified:\n{}".format(resp, user))

                        if not user["favourite_mode"]: # osu!
                            mode = 'std'
                            mode_nice = 'osu!'
                        elif user["favourite_mode"] == 1: # osu!taiko
                            mode = 'taiko'
                            mode_nice = 'osu!taiko'
                        elif user["favourite_mode"] == 2: # osu!catch
                            mode = 'ctb'
                            mode_nice = 'osu!catch'
                        elif user["favourite_mode"] == 3: # osu!mania
                            mode = 'mania'
                            mode_nice = 'osu!mania'

                        embed = discord.Embed(
                            title        = ":flag_{flag}: {username} | {gm} {rx}".format(
                                flag     = user["country"].lower(),
                                username = user["username"],
                                rx       = '(Relax)' if relax == '-rx' else '(Vanilla)',
                                gm       = mode_nice),
                            description  = '** **',
                            color        = 0x00ff00)

                        embed.set_thumbnail(url=akatsuki_logo)

                        if user[mode]["global_leaderboard_rank"] is not None:
                            embed.add_field(
                                name   = "Global Rank",
                                value  = "#{:,}".format(user[mode]["global_leaderboard_rank"]),
                                inline = True)

                        if user[mode]["country_leaderboard_rank"] is not None:
                            embed.add_field(
                                name   = "Country Rank",
                                value  = "#{:,}".format(user[mode]["country_leaderboard_rank"]),
                                inline = True)

                        if user[mode]["pp"] is not None:
                            embed.add_field(
                                name   = "PP",
                                value  = "{:,}pp".format(user[mode]["pp"]),
                                inline = True)

                        if user[mode]["ranked_score"] is not None:
                            embed.add_field(
                                name   = "Ranked Score",
                                value  = "{:,}".format(user[mode]["ranked_score"]),
                                inline = True)

                        if user[mode]["total_score"] is not None:
                            embed.add_field(
                                name   = "Total Score",
                                value  = "{:,}".format(user[mode]["total_score"]),
                                inline = True)

                        if user[mode]["level"] is not None:
                            embed.add_field(
                                name   = "Level",
                                value  = "{}".format(round(user[mode]["level"], 2)),
                                inline = True)

                        if user[mode]["accuracy"] is not None:
                            embed.add_field(
                                name   = "Accuracy",
                                value  = "{}%".format(round(user[mode]["accuracy"], 2)),
                                inline = True)

                        if user[mode]["playcount"] is not None:
                            embed.add_field(
                                name   = "Playcount",
                                value  = "{:,}".format(user[mode]["playcount"]),
                                inline = True)

                        if user[mode]["playtime"] is not None:
                            embed.add_field(
                                name   = "Playtime",
                                value  = "{:,} hours".format(round(int(user[mode]["playtime"]) / 3600, 2)),
                                inline = True)

                        if user[mode]["replays_watched"] is not None:
                            embed.add_field(
                                name   = "Replays Watched",
                                value  = "{:,}".format(user[mode]["replays_watched"]),
                                inline = True)

                        if user["followers"] is not None:
                            embed.add_field(
                                name   = "Followers",
                                value  = "{}".format(user["followers"]),
                                inline = True)

                        await message.channel.send(embed=embed)
                    return

            # Run a command on the Akatsuki server
            # TODO: compare against their ingame perms? this could be a good mini project i guess
#            elif command == "r" and message.author.guild_permissions.manage_roles: # guild_permissions does not take channel perms into account
#
#                if not message.author.is_on_mobile(): # Only allow !r to be used from mobile.
#                    return
#
#                with message.channel.typing():
#                    execute = ' '.join(messagecontent[1:]).strip()
#
#                    if not len(execute.strip()) > 4 or messagecontent[1][0] != COMMAND_PREFIX:
#                        await send_message_formatted("error", message, "what exactly are you trying to send..?")
#                        return
#
#                    params = urlencode({"k": config["akatsuki"]["apikey"], "to": "#admin", "msg": execute})
#                    requests.get("http://{}:5001/api/v1/fokabotMessage?{}".format(config["akatsuki"]["ip"], params))
#
#                    await send_message_formatted("success", message, "your command has been successfully executed on Akatsuki", ["`{}`".format(execute)])
#                    return

            # Return current UNIX timestamp
            elif command in ("time", "unix", "unixtime"):
                await send_message_formatted("success", message, "current UNIX timestamp: `{}`".format(int(time.time())))
                return

            # Round arg0 to arg1 decimals
            elif command == "round": # TODO: server time adjustment
                if not len(messagecontent) > 2:
                    await send_message_formatted("error", message, "missing required parameters (number, decimal places).")
                    return
                if re.match("^\d+?\.\d+?$", messagecontent[1]) is None:
                    await send_message_formatted("error", message, "why are your trying to round that?")
                    return

                if len(messagecontent[1].split(".")[1]) < int(messagecontent[2]):
                    messagecontent[2] = len(messagecontent[1].split(".")[1])
                await send_message_formatted("success", message, "rounded value (decimal places: {}): `{}`".format(messagecontent[2], round(float(messagecontent[1]), int(messagecontent[2]))))
                return

            # Command which grabs most recent (regular) plays from the Akatsuki API.
            # Syntax: $recent <username>
            # TODO: Add relax support.
            elif command == "recent":
                with message.channel.typing():
                    if not len(messagecontent) > 2:
                        await send_message_formatted("error", message, "missing required parameters (username, gamemode).")
                        return

                    username = messagecontent[1]
                    gamemode = messagecontent[2].lower()

                    # Change gamemode from user input string
                    # to gamemodeint and beautified gamemode.
                    # TODO: any()
                    if 's' in gamemode or ('o' in gamemode and not 'm' in gamemode and not 'c' in gamemode and not 't' in gamemode):
                        gamemode = 0
                        gamemode_string = "osu!"
                    elif 't' in gamemode:
                        gamemode = 1
                        gamemode_string = "osu!taiko"
                    elif 'c' in gamemode:
                        gamemode = 2
                        gamemode_string = "osu!catch"
                    elif 'm' in gamemode:
                        gamemode = 3
                        gamemode_string = "osu!mania"
                    else:
                        await send_message_formatted("error", message, "please enter a valid gamemode", ["Options: std, ctb, taiko, mania."])
                        return

                    _user = requests.get('https://akatsuki.pw/api/v1/get_user?u={}'.format(username)).text
                    user = json.loads(_user)[0]

                    userID = user["user_id"]

                    _resp = requests.get("http://akatsuki.pw/api/get_user_recent?u={user}&limit=5&type=string&m={mode}".format(user=username, mode=gamemode)).text
                    resp = json.loads(_resp)

                    debug_print("Raw JSON:\n{}\n\nMinified:\n{}".format(_resp, resp))

                    embed = discord.Embed(
                        title            = "Recent Plays for :flag_{flag}: {username} | {gm}"
                            .format(
                                flag     = user["country"].lower(),
                                username = user["username"],
                                gm       = gamemode_string
                                ),
                        description      = '** **',
                        color            = 0x00ff00)

                    # The thumbnail for the embed should be Akatsuki's logo.
                    embed.set_thumbnail(url=akatsuki_logo)

                    for idx, score in enumerate(resp):

                        debug_print(score)

                        beatmap = json.loads(requests.get("https://akatsuki.pw/api/get_beatmaps?b={beatmap_id}".format(beatmap_id=score["beatmap_id"])).text)[0]

                        embed.add_field(
                            name="** **", # :crab:
                            value="**{index}. `{rank_achieved}` [{artist} - {song_name} \[{diff_name}\]](https://akatsuki.pw/b/{beatmap_id}) ({star_rating}★) {mods}**\n**Score**: {score}\n**PP**: {pp}\n**Combo**: {combo_achieved}/{max_combo}x - [{count300}/{count100}/{count50}/{countmiss}]\n**Date achieved**: {date}" \
                            .format(
                                index          = idx + 1,
                                rank_achieved  = score["rank"], # TODO: This is actually disgusting!
                                artist         = beatmap["artist"],
                                song_name      = beatmap["title"],
                                diff_name      = beatmap["version"],
                                beatmap_id     = score["beatmap_id"],
                                star_rating    = round(float(beatmap["difficultyrating"]), 2),
                                mods           = osu_mods(int(score["enabled_mods"])),
                                score          = score["score"],
                                pp             = score["pp"],
                                combo_achieved = score["maxcombo"],
                                max_combo      = beatmap["max_combo"],
                                count300       = score["count300"],
                                count100       = score["count100"],
                                count50        = score["count50"],
                                countmiss      = score["countmiss"],
                                date           = score["date"]))

                    await message.channel.send(embed=embed)
                    return

            # Multipurpose akatsuki info command.
            # Syntax: $akatsuki <callback>
            # TODO: Unhardcode the responses; database.
            elif command == "akatsuki":
                if len(messagecontent) > 1:
                    topic = messagecontent[1].lower()
                else:
                    topic = None

                if topic in (None, "help"):
                    await send_message_formatted("✨", message, "please enter a topic", ["There are quite a few, so they will not be listed."])
                    return
                elif topic == 'discord':
                    resp = 'https://discord.gg/5cBtMPW/'
                elif topic == 'twitch':
                    resp = 'https://www.twitch.tv/akatsuki_pw/'
                elif topic == 'youtube' or topic == 'yt':
                    resp = 'https://www.youtube.com/channel/UCjf8Fx_BlUr-htEy6hficcQ/'
                elif topic == 'rlb' or topic == 'relaxleaderboard':
                    resp = 'https://akatsuki.pw/leaderboard?mode=0&p=1&rx=1/'
                elif topic == 'lb' or topic == 'leaderboard':
                    resp = 'https://akatsuki.pw/leaderboard?mode=0&p=1&rx=0/'
                elif topic == 'admin':
                    resp = 'https://old.akatsuki.pw/index.php?p=100/'
                elif topic == 'log' or topic == 'adminlog' or topic == 'raplog':
                    resp = 'https://old.akatsuki.pw/index.php?p=116'
                elif topic == 'datadog' or topic == 'status':
                    resp = 'https://p.datadoghq.com/sb/71577ef74-a079587e79/'
                elif topic == 'vote':
                    resp = 'https://topg.org/osu-private-servers/in-509809'
                else:
                    await send_message_formatted("error", message, "I couldn't find a topic by that name")
                    return
                
                await send_message_formatted("success", message, resp)
                return

            # Multipurpose staff application commands.
            # Syntax: $apply <callback>
            # TODO: Unhardcode the responses; database.
            elif command == "apply":
                if len(messagecontent) > 1:
                    position = messagecontent[1].lower()
                else:
                    position = None

                resp_array = []
                emoticon = "success"

                if position in (None, "help"):
                    resp = \
                        "Please use a role name as an arguement"

                    resp_array = \
                        ["Eg: $apply bn, or $apply beatmap_nominator"]

                    emoticon = "✨"

                elif 'admin' in position or position == 'commuinity_manager' or position == 'communitymanager':
                    resp = \
                        "You cannot apply for this role"

                    resp_array = \
                        ["Admins are always handpicked from " \
                        "lower roles or from the community when " \
                        "we find a member we believe would " \
                        "be a good fit for the role."]

                    emoticon = "error"

                elif 'mod' in position:
                    resp = \
                        "You cannot apply for this role"

                    resp_array = \
                        ["Mods are usually handpicked from " \
                        "lower roles (such as BN, Support Team).",
                        "This usually happens when we believe " \
                        "they would be better suited with some " \
                        "fancy new powers."]

                    emoticon = "error"

                elif 'beat' in position or position == 'bn':
                    resp = \
                        "BNs are currently in high demand!"

                    resp_array = \
                        ["If you're interested in this position " \
                         "(and are quite active on the server, " \
                         "this will be checked), feel free to " \
                         "apply!",
                         "https://goo.gl/forms/XyLMtFlaA6mHAiIB3"]

                elif 'support' in position:
                    resp = \
                        "To be considered for the support team, " \
                        "you will need to be quite active in the " \
                        "<#365413867167285249> channel already"

                    resp_array = \
                        ["We use this to ensure that you\'re the right " \
                        "kind of person for the job.",
                        "Most likely, if we see you being active, we will offer " \
                        "you the position if you seem to be a good pick."]

                elif 'akatsuki' in position or 'people' in position or 'uploader' in position:
                    resp = \
                        "You cannot apply for this role"

                    resp_array = \
                        ["Due to our past experiences with picking " \
                        "members from the community for this role, " \
                        "we have decided to no longer make it a public role.",
                        "Members of the Akatsuki people role are handpicked " \
                        "by cmyui himself."]

                    emoticon = "error"

                elif position == 'premium' or position.startswith('don') or position == 'supporter':
                    resp = \
                        "This isn\'t a role you can apply for, silly"

                    resp_array = \
                        ["Supporter: https://akatsuki.pw/donate",
                        "Premium: https://akatsuki.pw/premium",
                        "Thanks for considering to support the " \
                        "server, though!",
                        "**It means a lot!**"]

                elif 'verif' in position:
                    resp = \
                        "The verified role in-game is for players " \
                        "who we essentially trust (for lack of " \
                        "better wording)."

                    resp_array = \
                        ["These players have either " \
                        "been verified through liveplays, or maybe " \
                        "have even met a staff member IRL to prove " \
                        "their legitimacy (rare, but there are 10+).",
                        "",
                        "You cannot apply for verified, as it is " \
                        "something we will look to give you, rather " \
                        "than vice versa :^)"]
                else:
                    await send_message_formatted("error", message, "I couldn't find a position by that name")
                    return

                await send_message_formatted(emoticon, message, resp, resp_array)
                return

            # cmyui command; multipurpose information command on the guy.
            # Syntax: $cmyui <callback>
            # TODO: Unhardcode yet again!
            elif command == "cmyui":
                if len(messagecontent) > 1:
                    topic = messagecontent[1].lower()
                else:
                    topic = None

                resp_array = []

                if topic in (None, "help"):
                    resp = \
                    "The $cmyui command is just a dictionary of stuff cmyui has saved in it"

                elif topic == 'settings':
                    resp = \
                    "Here are cmyui's normal osu! settings"

                    resp_array = \
                    ["",
                     "**osu! Settings**",
                     "✅ 1.0x Sensitivity",
                     "❌ Video & Storyboard",
                     "💯 Background Dim",
                     "",
                     "**Peripherals**",
                     "🖊 Wacom CTH-480 (CTL470 Pen) Area: https://nanahira.life/Z1BVsPqqvsi8el7SjiCPQVV64zgraHw1.png",
                     "⌨ CM Masterkeys Pro L (Cherry MX Browns)",
                     "💻 1: Acer 240hz | 2: Asus 144hz | 3: Asus 60hz",
                     "🖥 CPU: i7-8700 | GPU: GTX 1070Ti | 16GB DDR4 2444MHz"
                     ]

                elif topic.startswith('skin'):
                    resp = \
                    "Here are some of the skins cmyui uses frequently"

                    resp_array = \
                    ["",
                     "**Current Main Skin(s)**",
                     "(Abyssal 2018-15-06): https://i.namir.in/Asi.osk",
                     "",
                     "**Other skins**",
                     "cmyui v5.3: https://i.namir.in/6CF.osk",
                     "cmyui v6.0 (Blue Crystal v2.1): https://i.namir.in/JS9.osk",
                     "cmyui v7.0: https://i.namir.in/YP7.osk",
                     "cmyui v9.4: https://i.namir.in/jHW.osk",
                     "Alacrity 1.2: https://i.namir.in/4Oo.osk",
                     "g3p: https://i.namir.in/Q1L.osk",
                     "Justice: https://i.namir.in/b1u.osk",
                     "Cookiezi 32: https://i.namir.in/y8v.osk",
                     "Cookiezi 35: https://i.namir.in/y8v.osk",
                     "",
                     "**If any of the links are not working, "
                     "please tell cmyui#0425 :)**"]

                elif topic == 'psyqui' or topic == 'yvs':
                    resp = \
                    "https://www.youtube.com/watch?v=wKgbDk2hXI8"

                else:
                    await send_message_formatted("error", message, "I couldn't find a subcategory by that name")
                    return

                # TODO: send this to author rather than channel..
                await send_message_formatted("✨", message, resp, resp_array)
                return

            # Info and FAQ command. General information such as rules, etc.
            # Syntax: $info <callback> | $faq <callback>
            elif command in ("info", "information", "faq", "help"):
                if len(messagecontent) > 1:
                    callback = messagecontent[1].lower()
                else:
                    callback = "" # not nonetype so we can support digit stuff without a copy paste exception fucking python no goto fuck
                
                command_type = 0 if command.startswith("info") else 1

                SQL.execute("SELECT * FROM discord_faq WHERE {type} = %s AND type = %s".format(type='id' if callback.isdigit() else 'topic'), [callback, command_type])
  
                result = SQL.fetchone()

                if result is not None:
                    embed = discord.Embed(title=result[2], description='** **', color=0x00ff00)
                    embed.set_thumbnail(url=akatsuki_logo)
                    embed.add_field(
                        name="** **",
                        value=result[3]
                            .replace("{AKATSUKI_IP}", AKATSUKI_IP_ADDRESS)
                            .replace("{COMMAND_PREFIX}", COMMAND_PREFIX),
                        inline=result[5])

                    if result[4] is not None:
                        embed.set_footer(icon_url='', text=result[4])
                    await message.channel.send(embed=embed)
                else:
                    SQL.execute("SELECT id, topic, title FROM discord_faq WHERE type = %s", [command_type])

                    faq_db = SQL.fetchall()

                    faq_list = ""
                    for idx, val in enumerate(faq_db):
                        faq_list += "{}. {}{}|| {}\n".format(idx + 1, val[1], " " * (FAQ_LIST_SPACING - len(val[1])), val[2])

                    await send_message_formatted("error", message,"I couldn't find a topic by that {}".format("id" if callback.isdigit() else "name"), ["```{faq_list}```".format(
                        topic    = " " + callback if len(callback) > 0 else "",
                        faq_list = faq_list.replace("`", ""))])
                return

            elif command in ("aika", "botinfo"): # Bot info command.
                embed = discord.Embed(title="Why hello! I'm Aika.", description='** **', color=0x00ff00)
                embed.set_thumbnail(url=aika_pfp)
                embed.add_field(
                    name   = "** **",
                    value  = "I\'m Akatsuki\'s (and cmyui\'s) bot. "
                             "I provide the server with things such as "
                             "commands to track ingame stats, help out "
                             "members in need, and provide overall fun "
                             "(and lots of useless) commands!\n\nSource "
                             "code: https://github.com/osuAkatsuki/Aika."
                             "\nIngame: https://akatsuki.pw/u/999\nCreator: "
                             "https://akatsuki.pw/u/1001",
                    inline = False)

                embed.set_footer(icon_url="", text="Good vibes <3")
                await message.channel.send(embed=embed)
                return

            # Prune command. Prune x messages from the current channel.
            # Syntax: $prune <count>
            # TODO: More functionality, maybe prune by a specific user, etc.
            elif command in ("p", "prune") and message.author.guild_permissions.manage_messages:
                if len(messagecontent) > 1:
                    count = messagecontent[1]
                else:
                    count = ""

                if not count.isdigit():
                    await send_message_formatted("error", message, "it seems you didn't specify a correct integer",
                        ["Correct syntax: `{}prune <messagecount>`.".format(COMMAND_PREFIX), "The limit for deleted messagecount is 1000."])
                    return
                else:
                    count = int(count)

                if count <= 1000:
                    deleted = await message.channel.purge(limit=count + 1 if count != 1000 else count)
                    await send_message_formatted("success", message, 'Successfully pruned {messages} message{plural}'.format(
                        messages = len(deleted) - 1,
                        plural   = "s" if len(deleted) - 1 > 1 else ""))
                else:
                    await send_message_formatted("error", message, "It seems you used the command syntax improperly",
                        ["Correct syntax: `{}prune <messagecount>`.".format(COMMAND_PREFIX), "The limit for deleted messagecount is 1000."])
                return

            # Command for linking osu! account to discord
            # Syntax: $linkosu
            # TODO: More functionality, maybe not for only donors?
            elif command == "linkosu":
                SQL.execute("SELECT * FROM discord_roles WHERE discordid = %s", [message.author.id])
                result = SQL.fetchone()

                if result is not None:
                    if not result[4]:
                        await client.add_roles(message.author, discord.utils.get(message.guild.roles, id=result[3]))
                        SQL.execute("UPDATE discord_roles SET verified = 1 WHERE discordid = %s", [message.author.id])

                        await send_message_formatted("success", message, "your Discord has been sucessfully linked to your Akatsuki account.", ["Your roles should now be synced."])
                    else:
                        await send_message_formatted("error", message, "you already have an account linked")
                else:
                    await send_message_formatted("✨", message, "Linking process initiated",
                        ["Next, please use the following command in #osu, or in a DM with 'Aika' ingame.",
                         "(in-game in the osu! client).", ">> `!linkdiscord {}`".format(message.author.id)])
                return

print(Fore.CYAN + "\nLogging into Discord with token..")
client.run(str(config['discord']['token']))

# Clean up
print(Fore.MAGENTA + "\nCleaning up MySQL variables..")
SQL.close()
cnx.close()
print(Fore.GREEN + "Cleaning complete.")
