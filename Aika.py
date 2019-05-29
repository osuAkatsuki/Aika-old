import discord
import asyncio
import configparser
import re
import logging
import traceback
import requests
import json
import random
from colorama import init
from colorama import Fore, Back, Style
from urllib.parse import urlencode
import MySQLdb
import redis
import time
from datetime import datetime

# Initialize colorama
init(autoreset=True)

# Discord Client
client = discord.Client()

# Configuration
config = configparser.ConfigParser()
config.sections()
config.read('config.ini')

# Connect to redis
r = redis.Redis(host='localhost', port=6379, db=0)

# MySQL
db = MySQLdb.connect(
    host=str(config['mysql']['host']),
    user=str(config['mysql']['user']),
    passwd=str(config['mysql']['passwd']),
    db=str(config['mysql']['db'])
    )
db.autocommit(True)
db.ping(True)


""" Constants """

# The version number of Aika!
version = 2.00

# A list of filters.
# These are to be used to wipe messages that are deemed inappropriate,
# or break rules. For the most part, these are of other private servers,
# as required by rule #2 of the Akatsuki Discord & Chat Rules
# (https://akatsuki.pw/doc/rules).
filters       = ['pp.me', 'paypal.me', 'yozo', 'y0zo', 'yoz0', 'y0z0',
                 'ainu', 'okamura', 'kotorikku', 'kurikku', 'kawata',
                 'ryusei', 'ryu-sei', 'enjuu', 'verge', 'katori',
                 'osu-thailand', 'discord.gg/', 'gatari', 'hidesu',
                 'hiragi', 'asuki', 'mikoto', 'homaru', 'awasu']

# A list of message (sub)strings that we will use to deem
# a quantifiable value for the "quality" of a message.
profanity     = ['nigg', 'n1gg', 'retard', 'idiot',
                 'fuck off', 'shut the fuck up', '??']

high_quality  = ['$faq', 'welcome', 'have a good',
                 'enjoy', 'no problem', 'of course',
                 'can help', 'i can', 'how can i help you']

# A list of message (sub)strings used to determine when a user
# is asking about email verification (which does not exist on Akatsuki).
email_checks  = ['verify e', 'verification', 'on email', 'verify m', 'verify a', 'email t', 'w verify', 'i verify']

# Akatsuki's logo.
# To be used mostly for embed thumbnails.
akatsuki_logo = "https://akatsuki.pw/static/logos/logo.png"
aika_pfp      = "https://akatsuki.pw/static/characters/quaver.png"


""" Functions """


def debug_print(string):
    """
    Print a debug message to the console.
    
    Example in use:      https://nanahira.life/dOgXljmmKW336gro3Ts5gJmU7P4hNDZz.png

    :param string:       The message to be printed to the console.
    """

    if config['default']['debug'] != '0':
        print(Fore.MAGENTA + "\nDEBUG: {}\n".format(string))


async def send_message_formatted(type, message, first_line, string_array=[]):
    """
    Send a response via discord to the channel.

    Example in use:      https://nanahira.life/qxb2f7j0EvrR7DftvHfBxosXTvtL5s9u.png

    :param message:      The message object provided from discord.
    :param first_line:   The first line of the response. The only one required.
    :param string_array: The array of strings to follow. Optional.
    """

    # Choose what kind of emoticon to open the response with.
    if type == "error":
        emoticon = "🔴"
    elif type == "success":
        emoticon = "🔵"
    else: # neutral
        emoticon = type

    # Build the response string.
    resp =  "{emoticon} **{author_name}**, {first_line}.".format(emoticon=emoticon, author_name=message.author.name, first_line=first_line)
    for line in string_array:
        resp += "        {string}\n".format(string=line)

    # Send the response off to discord.
    await client.send_message(message.channel, resp)


# Startup, after login action
@client.event
async def on_ready():
    print(Fore.GREEN + 'Authentication Successful.\n{} | {}\n--------------------------\n'
        .format(client.user.name, client.user.id))

    debug_print("Debug enabled.")

    # Send an announcement that the bots been started in Akatsuki's #general (if debug)
    if int(config['default']['announce_online']) == 1:
        announceOnline = discord.Embed(title="Aika v{versionNum} Online"
                                        .format(versionNum=version),
                                            description="Ready for commands <3\n\n "
                                                "Source code can be found at "
                                                "https://github.com/osuAkatsuki/Aika.",
                                            color=0x00ff00)

        announceOnline.set_thumbnail(url='http://akatsuki.pw/static/characters/quaver.png')
        await client.send_message(client.get_channel(config['akatsuki']['general']), embed=announceOnline)

# On exceptions, don't make the whole thing die :)
@client.event
async def on_error(event, *args):
    print(Fore.RED + "\n\nAn exception has occurred.\n\nError: {}\nargs: {}\n\nTraceback: {}\n"
        .format(event, *args, logging.warning(traceback.format_exc())))

# On message event
@client.event
async def on_message(message):
    client.wait_until_ready()

    # Message sent in #player-reporting, move to #reports
    if message.channel.id == config['akatsuki']['player_reporting']: 
        await client.delete_message(message) # Delete the message from #player-reporting

        # Prepare, and send the report in #reports
        embed = discord.Embed(title="New report recieved.", description='** **', color=0x00ff00)
        embed.set_thumbnail(url=akatsuki_logo)
        embed.add_field(name="Report content", value=message.content, inline=True)
        embed.add_field(name="Author", value=message.author.mention, inline=True)

        # Prepare, and send the report to the reporter
        embedPrivate = discord.Embed(title="Thank you for the player report.",
                                    description="We will review the report shortly."
                                    .format(message.content), color=0x00ff00)

        embedPrivate.add_field(name="Report content", value=message.content, inline=True)
        embedPrivate.set_thumbnail(url=akatsuki_logo)

        if not message.content.startswith('$'): # Do not pm or link to #reports if it is a command
            await client.send_message(message.author, embed=embedPrivate)
            await client.send_message(client.get_channel(config['akatsuki']['reports']), embed=embed)

            # Print result to console
            print(Fore.CYAN + "Report recieved. It has been moved to #reports.")

    # Request sent in rank_requests, add base thumbs
    elif message.channel.id == config['akatsuki']['rank_requests']:
        await client.add_reaction(message, "👍")
        await client.add_reaction(message, "👎")

    elif message.author != client.user:

        messagelen = len(message.content)

        properly_formatted = False

        if messagelen > 0:
            #debug_print("First character: {}\n"
            #            "Last character:  {}\n"
            #            "First isupper?:  {u}\n"
            #            "Last isperiod?:  {p}".format(message.content[0], message.content[messagelen - 1], u=message.content[0].isupper(), p=message.content[messagelen - 1] == "."))

            properly_formatted = message.content[0].isupper() and message.content[messagelen - 1] in (".", "?", "!")


        # Message sent in #help, log to db
        if message.channel.id == config['akatsuki']['help']:
            if any(x in message.content.lower() for x in profanity):
                quality = 0
            elif any(x in message.content.lower() for x in high_quality) or properly_formatted:
                quality = 2
            else:
                quality = 1

            debug_print("Quality of message {}: {}".format(message.id, quality))

            cursor = db.cursor()
            cursor.execute("""
                            INSERT INTO help_logs
                                        (id,
                                         user,
                                         content,
                                         datetime,
                                         quality)
                            VALUES
                                        (NULL,
                                         %s,
                                         %s,
                                         %s,
                                         %s);
                            """,
                            [message.author.id,
                            message.content,
                            int(time.time()),
                            quality])

        # Checks for things in message
        if any(x in message.content.lower() for x in email_checks) and message.server.id == config['akatsuki']['server_id']:
            if "badge" not in message.content.lower():
                await client.send_message(message.author,
                                        "Right, this is an automated message as it "
                                        "was assumed you needed assitance in Akatsuki "
                                        "with: Email Verification\n\nAs the verification "
                                        "page says, Akatsuki does not use verification "
                                        "emails. To verify your account, simply install "
                                        "the switcher, install the certificate, click the "
                                        "server you\'d like to play on, and click On/Off, "
                                        "then login to osu! to complete the verification process.")

                await client.delete_message(message)

                debug_print("Triggered: Verification Email Support\nUser: {}"
                    .format(message.author))
            else:
                debug_print("Aborted Trigger: Email Verification Support, due "
                            "to \"badge\" contents of the message.\nUser: {}"
                            .format(message.author))

        elif any(x in message.content.lower() for x in filters):
            cursor = db.cursor()
            cursor.execute("""
                            INSERT INTO profanity_filter
                                        (user,
                                         message,
                                         time)
                            VALUES
                                        (%s,
                                         %s,
                                         %s);
                            """,
                            [message.author.id,
                            message.content,
                            int(time.time())])

            await client.delete_message(message)
            await client.send_message(message.author,
                                    "Hello,\n\nYour message in osu!Akatsuki "
                                    "has been removed as it has been deemed "
                                    "unsuitable.\n\nIf this makes no sense, "
                                    "please report it to <@285190493703503872>. "
                                    "\n**Do not try to evade this filter as it is "
                                    "considered fair ground for a ban**.\n\n```{}```"
                                    .format(message.content))

            print(Fore.MAGENTA + "Filtered message | '{}: {}'"
                .format(message.author, message.content))

        # Private messages
        if message.server is None:
                print(Fore.YELLOW + Style.BRIGHT + "{} [{}] {}: {}"
                    .format(message.timestamp, message.channel,
                            message.author, message.content))

        # When you are pinged
        elif config['discord']['owner_id'] in message.content:
                print(Fore.CYAN + Style.BRIGHT + "{} [{} ({})] {}: {}"
                    .format(message.timestamp, message.server, message.channel,
                            message.author, message.content))

        # When your username is mentioned (either actual one, or custom set in configuration)
        elif (config['discord']['username'] in message.content.lower() \
        and len(config['discord']['username']) > 1):
                print(Fore.GREEN + Style.BRIGHT + "{} [{} ({})] {}: {}"
                    .format(message.timestamp, message.server, message.channel,
                            message.author, message.content))

        # The server is akatsuki
        elif message.server.id == config['akatsuki']['server_id']:
            print(Fore.BLUE + Style.BRIGHT + "{} [{} ({})] {}: {}"
                .format(message.timestamp, message.server, message.channel,
                        message.author, message.content))

        # Regular message
        else:
            print("{} [{} ({})] {}: {}"
                .format(message.timestamp, message.server, message.channel,
                        message.author, message.content))

        if message.content.startswith('$') or message.content.startswith('!verify'): # The message is a command

            # First of all, make a simpler way to deal with message content so u don't develop stage 4 cancer
            messagecontent = message.content.split(' ')

            # TODO: Process commands based on discord perms
            if message.author.id == config['discord']['owner_id']: # Process owner commands
                """
                Process owner commands.

                Only the config['discord']['owner_id'] has access to these.
                """
                if messagecontent[0].lower() == '$game':
                    # Change your discord users status / game
                    game = ' '.join(messagecontent[1:]).strip() # Get the game
                    if game: # Game also changed

                        """
                        game Variables:
                        name = name of the game
                        url = link for the game (usually for streaming probably)
                        type = boolean to show whether streaming or not
                        """
                        await client.change_presence(
                            game=discord.Game(name=game, url='https://akatsuki.pw/', type=0))

                        await send_message_formatted("success", message,
                            "Game successfully changed to: {}".format(game))
                    else:
                        await send_message_formatted("error", message,
                            "Please specify a game name")
                    await client.delete_message(message)

                elif messagecontent[0].lower() == '$hs':
                    userID = re.findall('\d+', messagecontent[1])[0]

                    cursor = db.cursor()
                    cursor.execute("""
                                    SELECT quality
                                    FROM help_logs
                                    WHERE
                                    user = %s;
                                    """,
                                    [userID])

                    logs = cursor.fetchall()

                    debug_print(logs)

                    positive, neutral, negative, i = 0, 0, 0, 0

                    if logs is not None:
                        for x in logs:
                            if logs[i][0] == 0:
                                negative += 1
                            elif logs[i][0] == 1:
                                neutral += 1
                            else:
                                positive += 1
                            i = i + 1

                        embed = discord.Embed(title="Helplogs report | {}".format(userID), description='** **', color=0x00ff00)
                        embed.set_thumbnail(url=akatsuki_logo)
                        embed.add_field(name="Total", value=positive + neutral + negative, inline=True)
                        embed.add_field(name="Positive", value=positive, inline=True)
                        embed.add_field(name="Neutral", value=neutral, inline=True)
                        embed.add_field(name="Negative", value=negative, inline=True)
                        await client.send_message(message.channel, embed=embed)
                    else:
                        await send_message_formatted("error", message,
                            "No logs found on the specified user")

                elif messagecontent[0].lower() == '$r':
                    try:
                        annmsg = ' '.join(messagecontent[1:]).strip()

                        processingMessage = await send_message_formatted("success", message,
                                             "Processing request.")

                        params = urlencode({"k": config["akatsuki"]["apikey"], "to": "#admin", "msg": annmsg})
                        requests.get("http://{}:5001/api/v1/fokabotMessage?{}".format(config["akatsuki"]["ip"], params))

                        await send_message_formatted("success", message,
                            "Successfully executed: `{}` on Akatsuki"
                            .format(annmsg))

                        await client.delete_message(processingMessage)
                    except:
                        await send_message_formatted("error", message,
                            "Something went wrong during the request")

                elif messagecontent[0].lower() == '$d':
                    config.set('default', 'debug', '{}'.format('1' if config['default']['debug'] == '0' else 0))
                    print('1' if config['default']['debug'] == '0' else 0)

                    await send_message_formatted("✨", message,
                        "Debug: {}"
                        .format('Disabled' if config['default']['debug'] == '0' else 'Enabled'))

            """
            Process regular user command.

            All users can access these commands.
            """
            if messagecontent[0].lower() == '$user' \
            or messagecontent[0].lower() == '$stats': # Akatsuki userinfo command
                username = messagecontent[1]
                try:
                    relax = messagecontent[2]
                except:
                    relax = ''

                if relax != '' and relax != '-rx':
                    await send_message_formatted("error", message,
                        "Please use underscores in your username rather than spaces")
                else:
                    try:
                        processingMessage = await send_message_formatted("success", message,
                                             "Processing request.")

                        gamer = requests.get('https://akatsuki.pw/api/v1/get_user?u={}'.format(username)).text

                        gamerInfo = json.loads(gamer)

                        userID = int(gamerInfo[0]["user_id"])

                        resp = requests.get('https://akatsuki.pw/api/v1/users/{rx}full?id={userID}'
                            .format(rx="rx" if relax == '-rx' else '', userID=userID), timeout=3).text
                        
                        userInfo = json.loads(resp)

                        debug_print("{}\n\n{}".format(resp, userInfo))
                        if userInfo["favourite_mode"] == 0: # osu!
                            mode = 'std'
                            modeNice = 'osu!'
                        elif userInfo["favourite_mode"] == 1: # osu!taiko
                            mode = 'taiko'
                            modeNice = 'osu!taiko'
                        elif userInfo["favourite_mode"] == 2: # osu!catch
                            mode = 'ctb'
                            modeNice = 'osu!catch'
                        elif userInfo["favourite_mode"] == 3: # osu!mania
                            mode = 'mania'
                            modeNice = 'osu!mania'

                        embed = discord.Embed(title="{flag} {username} | {gm} {rx}".format(flag=":flag_{}:"
                            .format(userInfo["country"].lower()), username=userInfo["username"],
                                    rx='(Relax)' if relax == '-rx' else '(Vanilla)',
                                    gm=modeNice), description='** **', color=0x00ff00)

                        embed.set_thumbnail(url=akatsuki_logo)

                        if userInfo["{}".format(mode)]["global_leaderboard_rank"] is not None:
                            embed.add_field(name="Global Rank", value="#{:,}"
                                .format(userInfo["{}".format(mode)]["global_leaderboard_rank"]),
                                inline=True)

                        if userInfo["{}".format(mode)]["country_leaderboard_rank"] is not None:
                            embed.add_field(name="Country Rank", value="#{:,}"
                                .format(userInfo["{}".format(mode)]["country_leaderboard_rank"]),
                                inline=True)

                        if userInfo["{}".format(mode)]["pp"] is not None:
                            embed.add_field(name="PP", value="{:,}pp"
                                .format(userInfo["{}".format(mode)]["pp"]),
                                inline=True)

                        if userInfo["{}".format(mode)]["ranked_score"] is not None:
                            embed.add_field(name="Ranked Score", value="{:,}"
                                .format(userInfo["{}".format(mode)]["ranked_score"]),
                                inline=True)

                        if userInfo["{}".format(mode)]["total_score"] is not None:
                            embed.add_field(name="Total Score", value="{:,}"
                                .format(userInfo["{}".format(mode)]["total_score"]),
                                inline=True)

                        if userInfo["{}".format(mode)]["accuracy"] is not None:
                            embed.add_field(name="Accuracy", value="{}%"
                                .format(round(userInfo["{}".format(mode)]["accuracy"], 2)),
                                inline=True)

                        if userInfo["{}".format(mode)]["playcount"] is not None:
                            embed.add_field(name="Playcount", value="{:,}"
                                .format(userInfo["{}".format(mode)]["playcount"]),
                                inline=True)

                        if userInfo["{}".format(mode)]["playtime"] is not None:
                            embed.add_field(name="Playtime", value="{:,} hours"
                                .format(round(int(userInfo["{}".format(mode)]["playtime"]) / 3600, 2)),
                                inline=True)

                        if userInfo["{}".format(mode)]["replays_watched"] is not None:
                            embed.add_field(name="Replays Watched", value="{:,}"
                                .format(userInfo["{}".format(mode)]["replays_watched"]),
                                inline=True)

                        await client.send_message(message.channel, embed=embed)
                    except:
                        await send_message_formatted("error", message,
                                        "either that user does not exist, or your syntax was incorrect",
                                        ["Syntax: `$stats username_spaced_like_this (-rx)`"])

                    await client.delete_message(processingMessage)

            elif messagecontent[0].lower() == '$akatsuki': # multipurpose akatsuki info TODO: unhardcode
                try:
                    topic = messagecontent[1].lower()
                except:
                    topic = ''

                if topic == '' or topic == 'help':
                    await send_message_formatted("✨", message,
                        "Please enter a topic."
                        "There are quite a few, so they will not be listed")

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
                    await send_message_formatted("error", message,
                        "I couldn't find a topic by that name")
                    return
                
                
                await send_message_formatted("success", message, resp)

            elif messagecontent[0].lower() == '$apply': # multipurpose staff application commands
                try:
                    position = messagecontent[1].lower()
                except:
                    position = ''

                if position == '' or position == 'help':
                    await client.send_message(message.channel,
                                            "Please use a role name as an arguement. "
                                            "Eg: $apply bn, or $apply beatmap_nominator")
                elif 'admin' in position or position == 'commuinity_manager' or position == 'communitymanager':
                    await client.send_message(message.channel,
                                            "You cannot apply for this role. "
                                            "Admins are handpicked from the community "
                                            "by cmyui himself :o")
                elif 'mod' in position:
                    await client.send_message(message.channel,
                                            "You cannot apply for this role. "
                                            "Mods are usually handpicked from "
                                            "lower roles (such as BN, Akatsuki "
                                            "People, Support Team) if we believe "
                                            "they would be better suited with some "
                                            "fancy new powers.")

                elif 'beat' in position or position == 'bn':
                    await client.send_message(message.channel,
                                            "BNs are currently in high demand! If "
                                            "you\'re interested in this position "
                                            "(and are quite active on the server, "
                                            "this will be checked), feel free to "
                                            "apply here! https://goo.gl/forms/XyLMtFlaA6mHAiIB3")

                elif 'support' in position:
                    await client.send_message(message.channel,
                                            "To be considered for the support team, "
                                            "you will need to be quite active in the "
                                            "<#365413867167285249> channel already. We "
                                            "use this to ensure that you\'re the right "
                                            "kind of person for the job. Most likely, "
                                            "if we see you being active, we will offer "
                                            "you the position if you seem to be a good pick.")
                
                #elif 'akatsuki' in position or 'people' in position or 'uploader' in position:
                #    await client.send_message(message.channel,
                #                            "Looking to be an uploader?\n\nThere are "
                #                            "actually some PC requirements for this, "
                #                            "but they\'re really nothing special.\n- "
                #                            "PC Capable of recording 1080p60fps videos "
                #                            "without dropping below 4.2ms frametime (240fps)."
                #                            "\n\nYea, that\'s it! haha. Even better if you can "
                #                            "do 4K, or have editing capabilities.\n\nJust shoot "
                #                            "<@285190493703503872> a DM to apply for this role.")
                

                elif position == 'premium' or position == 'donor' or position == 'donator' or position == 'supporter':
                    await client.send_message(message.channel,
                                            "This isn\'t a role you can apply for, "
                                            "silly!\n\nSupporter: https://akatsuki.pw"
                                            "/donate\nPremium: https://akatsuki.pw/premium"
                                            "\n\nThanks for considering to support the "
                                            "server, though!\nIt means a lot!'")

                elif 'verif' in position:
                    await client.send_message(message.channel,
                                            "The verified role in-game is for players "
                                            "who we essentially trust (for lack of "
                                            "better wording). These players have either "
                                            "been verified through liveplays, or maybe "
                                            "have even met a staff member IRL to prove "
                                            "their legitimacy (rare, but there are 10+)."
                                            "\n\nYou cannot apply for verified, as it is "
                                            "something we will look to give you, rather "
                                            "than vice versa :^)")
                else:
                    await send_message_formatted("error", message,
                        "I couldn't find a position by that name")

            elif messagecontent[0].lower() == '$cmyui': # cmyui command. Multipurpose information command on the guy
                try:
                    topic = messagecontent[1].lower()
                except:
                    topic = ''

                if topic == '' or topic == 'help':
                    await client.send_message(message.channel,
                                            "The $cmyui command is just a dictionary "
                                            "of stuff cmyui has saved in it. Some public "
                                            "ones:\n\n$cmyui area - cmyui\'s area\n$cmyui "
                                            "skin - cmyui\'s skins\n$cmyui settings - "
                                            "cmyui\'s settings")

                elif topic == 'area':
                    await client.send_message(message.author,
                                            "Wacom CTH-480 (CTL470 Pen)\n\n100mm width "
                                            "(forced proportions) [16:9 screen, making it "
                                            "1.778:1]\nX : 0mm\nY : 57.79mm")

                    await client.send_message(message.channel,
                                            "The response has been sent to you via DM.")

                elif topic == 'settings':
                    await client.send_message(message.author,
                                            "1.0x sens, video and storyboard off, dim "
                                            "100%, fullscreen 1920x1080@240hz, snaking "
                                            "sliders, cursor size 0.60-0.84, hit lighting "
                                            "off, raw input off.")

                    await client.send_message(message.channel,
                                            'The response has been sent to you via DM.')
                elif topic == 'skin':
                    await client.send_message(message.author,
                                            "**Here are some of the skins cmyui uses "
                                            "frequently**\n\nCurrent main skin "
                                            "(Abyssal \2018-15-06): https://i.namir.in/Asi.osk"
                                            "\n\nOther skins:"
                                            "\ncmyui v5.3: https://i.namir.in/6CF.osk"
                                            "\ncmyui v6.0 (Blue Crystal v2.1): https://i.namir.in/JS9.osk"
                                            "\ncmyui v7.0: https://i.namir.in/YP7.osk"
                                            "\ncmyui v9.4: https://i.namir.in/jHW.osk"
                                            "\nAlacrity 1.2: https://i.namir.in/4Oo.osk"
                                            "\ng3p: https://i.namir.in/Q1L.osk"
                                            "\nJustice: https://i.namir.in/b1u.osk"
                                            "\nCookiezi 32: https://i.namir.in/y8v.osk"
                                            "\nCookiezi 35: https://i.namir.in/y8v.osk"
                                            "\n\nIf any of the links are not working, "
                                            "please tell cmyui#0425 :)")

                    await client.send_message(message.channel,
                                            "The response has been sent to you via DM.")

                elif topic == 'psyqui' or topic == 'yvs':
                    await client.send_message(message.channel, "https://www.youtube.com/watch?v=wKgbDk2hXI8")
                else:
                    await send_message_formatted("error", message,
                        "I couldn't find a subcategory by that name")

            elif messagecontent[0].lower() == '$faq': # FAQ command
                try:
                    callback = messagecontent[1].lower()
                except:
                    callback = ''

                cursor = db.cursor()
                cursor.execute("""
                                SELECT *
                                FROM discord_faq
                                WHERE
                                {type} = %s
                                AND
                                type = 1;
                                """
                    .format(type='id' if callback.isdigit() else 'topic'), [callback])

                result = cursor.fetchone()

                if result is not None:
                    embed = discord.Embed(title=result[2], description='** **', color=0x00ff00)
                    embed.set_thumbnail(url=akatsuki_logo)
                    embed.add_field(name="** **", value=result[3], inline=result[5])
                    if result[4] is not None:
                        embed.set_footer(icon_url='', text=result[4])
                    await client.send_message(message.channel, embed=embed)
                else:
                    cursor.execute("""
                                    SELECT id, topic, title
                                    FROM discord_faq
                                    WHERE
                                    type = 1;
                                    """)
                    faq_db = cursor.fetchall()
                    faq_list = ''
                    i = 0
                    for x in faq_db:
                        add_len = 12 - len(faq_db[i][1])
                        spaces = ''
                        spaces += ' ' * add_len

                        faq_list += '{}. {}{}|| {}\n'.format(i + 1, faq_db[i][1], spaces, faq_db[i][2])
                        i += 1

                    await send_message_formatted("error", message,
                        "I couldn't find a FAQ topic by that name", ["```{faqlist}```"
                            .format(
                                topic=' ' + callback if len(callback) > 0 else '',
                                faqlist=faq_list)])

            elif messagecontent[0].lower() == '$info': # info command
                try:
                    callback = messagecontent[1].lower()
                except:
                    callback = ''

                cursor = db.cursor()
                cursor.execute("""
                                SELECT *
                                FROM discord_faq
                                WHERE
                                {type} = %s
                                AND
                                type = 0;
                                """
                                .format(type='id' if callback.isdigit() else 'topic'),
                                [callback])
  
                result = cursor.fetchone()

                if result is not None:
                    embed = discord.Embed(title=result[2], description='** **', color=0x00ff00)
                    embed.set_thumbnail(url=akatsuki_logo)
                    embed.add_field(name="** **", value=result[3], inline=result[5])
                    if result[4] is not None:
                        embed.set_footer(icon_url='', text=result[4])
                    await client.send_message(message.channel, embed=embed)
                else:
                    cursor.execute("""
                                    SELECT id, topic, title
                                    FROM discord_faq
                                    WHERE
                                    type = 0;
                                    """)

                    info_db = cursor.fetchall()

                    info_list = ''
                    i = 0
                    for x in info_db:
                        add_len = 12 - len(info_db[i][1])
                        spaces = ''
                        spaces += ' ' * add_len

                        info_list += '{}. {}{}|| {}\n'.format(i + 1, info_db[i][1], spaces, info_db[i][2])
                        i += 1

                    await send_message_formatted("error", message,
                        "I couldn't find a FAQ topic by that name", ["```{infolist}```"
                            .format(
                                topic=' ' + callback if len(callback) > 0 else '',
                                infolist=info_list)])

            elif messagecontent[0].lower() in ('$verify', '!verify') and message.channel.id == config['akatsuki']['verify']: # Verify command
                if message.author.id != config['discord']['owner_id']: # Dont for cmyui, he's probably pinging @everyone to verify.
                    verified = discord.utils.get(message.server.roles, name="Members")
                    await client.add_roles(message.author, verified)
                    await client.delete_message(message)

            elif messagecontent[0].lower() == '$botinfo': # Bot info command
                embed = discord.Embed(title="Why hello! I'm Aika.", description='** **', color=0x00ff00)
                embed.set_thumbnail(url=aika_pfp)
                embed.add_field(
                    name="** **", value="I\'m Akatsuki\'s (and cmyui\'s) bot. "
                                        "I provide the server with things such as "
                                        "commands to track ingame stats, help out "
                                        "members in need, and provide overall fun "
                                        "(and lots of useless) commands!\n\nSource "
                                        "code: https://github.com/osuAkatsuki/Aika."
                                        "\nIngame: https://akatsuki.pw/u/999\nCreator: "
                                        "https://akatsuki.pw/u/1001", inline=False)

                embed.set_footer(icon_url='', text='Good vibes <3')
                await client.send_message(message.channel, embed=embed)

            elif messagecontent[0].lower() == '$prune' and message.author.server_permissions.manage_messages: # Prune messages
                await send_message_formatted("error", message,
                    "This command has been depreciated", ["Please use Tatsumaki's ;;prune command instead, as it is **much** more versatile."])

                """
                try:
                    amtMessages = messagecontent[1]
                except:
                    amtMessages = 100

                if str(amtMessages).isdigit() and int(amtMessages) <= 1000:
                    deleted = await client.purge_from(message.channel, limit=int(amtMessages) + 1)
                    message_count = len(deleted) - 1
                    await client.send_message(message.channel, 'Deleted {messages} message{plural}.'.format(messages=message_count, plural='s' if message_count > 1 else ''))
                else:
                    await client.send_message(message.channel, 'Incorrect syntax. Please use: $prune <1 - 1000>.')
                """

            elif messagecontent[0].lower() == '$linkosu':
                cursor = db.cursor()
                cursor.execute("""
                                SELECT *
                                FROM discord_roles
                                WHERE
                                discordid = %s
                                """,
                                [message.author.id])

                result = cursor.fetchone()
                if result is not None:
                    if result[4] == 0:
                        role = discord.utils.get(message.server.roles, id=result[3])
                        await client.add_roles(message.author, role)
                        cursor.execute("""
                                    UPDATE discord_roles
                                    SET
                                    verified = 1
                                    WHERE
                                    discordid = %s
                                    """,
                                    [message.author.id])

                        await client.send_message(message.channel,
                            "Your Discord has been sucessfully linked to your Akatsuki account.")
                    else:
                        await send_message_formatted("error", message,
                            "You already have an account linked")
                else:
                    await client.send_message(message.channel,
                                            "Linking process initiated\n\nNext, "
                                            "please use the following command in "
                                            "#osu, or in a DM with 'Aika' ingame "
                                            "(in-game in the osu! client).\n`>> "
                                            "!linkdiscord {}`".format(message.author.id))

print(Fore.CYAN + "\nLogging in with credentials: {}".format('*' * len(config['discord']['token'])))
client.run(str(config['discord']['token']))