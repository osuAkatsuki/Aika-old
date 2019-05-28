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

# Initialize colorama owo
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

# Constants
version = 1.75

filters = ['pp.me', 'paypal.me', 'yozo', 'y0zo', 'yoz0', 'y0z0', 'ainu', 'okamura', 'kotorikku', 'kurikku', 'kawata', 'ryusei', 'ryu-sei', 'enjuu', 'verge', 'katori', 'osu-thailand', 'discord.gg/', 'gatari', 'hidesu'] # bad boy words

profanity = ['nigg', 'n1gg', 'retard', 'idiot', 'fuck off', 'shut the fuck up']
high_quality = ['$faq', 'welcome', 'have a good one']
email_checks = ['verify e', 'verification', 'on email', 'verify m', 'verify a', 'email t', 'w verify', 'i verify']

sql_checks = [';', 'drop', 'ripple', 'select', 'delete', 'update', '*']

"""
positivity = ['YES, you can do it! NO, it won\'t be easy, but it\'ll be worth it!', 'Reason to get out of bed: there are puppies to pet!', 'Reason to get out of bed: the sun is shining for you!', 'Reason to get out of bed: there are new ice cream flavours to try!', 'Reasons to get out of bed: there are lots of new steps forward to take', 'Life is tough.. but so are you!', 'You are capable of so much MORe than you think.', 'I think you\'re doing a good job! Keep it up!', 'Instead of focusing on the negative, try to remember all the things you\'re grateful for instead!']
cmyuiPsych = ['jamming out to blue zenith while talking to deallly and others in Akatsuki VC', 'listening to his mom laugh', 'him and the others seeming much further away than they really were', 'driving in the ambulance', 'watching his blood get sucked out into a needle', 'trying to act sober in the face of authority', 'understanding someone that speaks no english', 'the afterimages as i wave my phone back and forth', 'seizure in the kids pool', 'humans split into 5 parts', 'the cat and the praying mantis', 'feeling wrong in my own skin', 'not being able to tell whether hot or cold', 'the relief of drinking the whole bottle of iced tea', 'strange throat feeling, almost as if my tongue had become a plant and sprouted or something', 'feeling music rather than just hearing it', 'intense visible pleasure wave on demand', 'pentap AiAe [a bit jumpy] HD', 'i thought i had bit my tongue but it was my immune system', 'smoke', 'seeing everything even when i closed my eyes', 'pulsating teleportation', 'feeling like we had something to do', 'nose bleeding hallucination', 'shit horse vodka', 'd', 'lost job', 'vomit', 'chicken nuggets', 'beach', 'fat guy', 'glass ceiling', 'facial hair', 'waving green walls', 'sea land', 'rich', 'pleasure', 'reaching up towards the top because the closer you get the exponentially better it gets', 'self dissection', 'high (first lyric in song)', 'follow the light', 'dad offering beer', 'acid interstate', 'driving through the jungles of germany', 'Jägermeister in coke', 'wasp swarm', 'her balcony', 'bending mushroomey houses and buildings', 'the restaurant in the middle of the forest', 'the pathway on the edge of the forest', 'half faking the panorama shake', 'dark green red and blue treetops', 'bugs in the forest', 'water dam', 'dark forest pathways', 'controlling your brain', 'begging for life and forgiveness', 'him crying', 'red and black scarf', 'i am gonnnnnnnnneeeeeeeeeeee', 'hair splitting reality', 'hugging jacob', 'donkey kong fur flowing', 'calendar pulsating', 'flowers moving', 'clouds on the ceiling', 'horses and bodies on the design with lighting', 'pins and needles stabbing my fingers', 'drawing blood and becoming cold', 'going down the water slide', 'asking a girl for a key card', 'running into their room and bed', 'waking up in destroyed room with paramedics', 'becoming older and older and then god himself', 'hearing them say i was dead', 'the jungle under my monitor', 'cat and dog', 'dinner with shinis family', 'fett', 'wanchu back', 'leo\'s sweater', 'lying down on the cool water dam at 4am', 'eating a sandwich', 'sitting on the bus', 'eating one chicken nugget', 'asking a stranger where the water cups were', 'staring at an older couple across in hospital... i think the guy died that night :(', 'logitech g930 usb ripped open but somehow intact', 'wet sand weird ass taste in mouth. literally unexplainable how fucked it feels.', 'my mouth numbing as i put the tab in, with that bitter taste of 25i..', 'standing on my chair overlooking the highway entrance lane. feeling the cars come towards me', 'glass, everywhere', 'stucco ceiling swerving all around', 'realer than real', 'trying to convince jacobs brother of how uncool i am', 'disappearing and reappearing strobe visuals', 'noticing the things on the walls and ceiling i would never otherwise notice', 'its like that-....', 'fighting my brain', 'inferno sounding like a mission', 'F.I becoming the scariest thing I have ever heard, like twisted vines wanted to rip me apart from my core', 'examining my juul for an hour', 'jacobs dad becoming king k rool for 1 frame of existence', 'gracie looking dangerous', 'the flash "plus" as i looked out jacobs back window', 'eyes morphing into other eyes', '"FUCK YOU!" written in my vision everywhere', 'smoking a bowl even though all the odds are stacked against it being a good idea']
justicePsych = ['d', 'FUCKING NEPTUNE', 'civilization incepting on my body', 'what the fuck am I looking at', 'Spencer is God', 'Subaru Outback from NASA', 'the gas station is quite green today', 'Smash on a single joycon is retard central', 'I refuse to fall down the stairs a third time', 'my life is a rainbow', 'my sock is going to kill me', 'omega-cold', 'Mezzanine-Massive Attack', 'HOW DO YOU TURN ON THE FUCKING SHOWER', 'HOW DO YOU TURN OFF THE FUCKING SHOWER', 'I CANT GET OUT OF THE FUCKING SHOWER', 'The shower has brought me great wealth', 'many faces inside of that person', 'look at that Arby\'s sign wow', 'my penis is non-existent what the fuck', 'ice is evil', 'the snow never ends', 'that beer bottle is Satan', 'I am Satan', 'I am definitely not Satan', 'WE HAVE BEEN IN THIS CAR FOREVER I WAS BORN IN THIS CAR', 'why is Chase so far away', 'I cant fucking see anything, but my eyes are pretending they can see']
"""

# Startup, after login action
@client.event
async def on_ready():
    print(Fore.GREEN + '\nAuthentication Successful.\n{} | {}\n--------------------------\n'.format(client.user.name, client.user.id))
    if int(config['default']['debug']) == 1:
        print(Fore.MAGENTA + "\n\nConfiguration:\nDebug: {debug}\n\n".format(debug="True" if int(config['default']['debug']) == 1 else "False"))

    # Send an announcement that the bots been started in Akatsuki's #general (if debug)
    if int(config['default']['announce_online']) == 1:
        announceOnline = discord.Embed(title="Aika v{versionNum} Online".format(versionNum=version), description='Ready for commands <3\n\nSource code can be found at https://github.com/osuAkatsuki/Aika.', color=0x00ff00)
        announceOnline.set_thumbnail(url='https://cdn.discordapp.com/attachments/285250367732842516/572989444723048498/s.png')
        await client.send_message(client.get_channel(config['akatsuki']['general']), embed=announceOnline)

# On exceptions, don't make the whole thing die :)
@client.event
async def on_error(event, *args):
    print(Fore.RED + "\n\nAn exception has occurred.\n\nError: {}\nargs: {}\n\nTraceback: {}\n".format(event, *args, logging.warning(traceback.format_exc())))

# On message event
@client.event
async def on_message(message):
    client.wait_until_ready()

    """ Constants """

    # Akatsuki's logo.
    # To be used mostly for embed thumbnails.
    akatsuki_logo = 'https://akatsuki.pw/static/logos/logo.png'
    aika_pfp = 'https://a.akatsuki.pw/999.png'

    if message.channel.id == config['akatsuki']['player_reporting']: # Message sent in #player-reporting, move to #reports
        await client.delete_message(message) # Delete the message from #player-reporting

        # Prepare, and send the report in #reports
        embed = discord.Embed(title="New report recieved.", description='** **', color=0x00ff00)
        embed.set_thumbnail(url=akatsuki_logo)
        embed.add_field(name="Report content", value=message.content, inline=True)
        embed.add_field(name="Author", value=message.author.mention, inline=True)

        # Prepare, and send the report to the reporter
        embedPrivate = discord.Embed(title="Thank you for the player report.", description="We will review the report shortly.".format(message.content), color=0x00ff00)
        embedPrivate.add_field(name="Report content", value=message.content, inline=True)
        embedPrivate.set_thumbnail(url=akatsuki_logo)

        if not message.content.startswith('$'): # Do not pm or link to #reports if it is a command
            await client.send_message(message.author, embed=embedPrivate)
            await client.send_message(client.get_channel(config['akatsuki']['reports']), embed=embed)

            # Print result to console
            print(Fore.CYAN + "Report recieved. It has been moved to #reports.")

    elif message.channel.id == config['akatsuki']['rank_requests']: # Request sent in rank_requests, add base thumbs
        await client.add_reaction(message, '👍')
        await client.add_reaction(message, '👎')

    elif message.author != client.user:
        # Message sent in #help, log to db
        if message.channel.id == config['akatsuki']['help']:
            if any(x in message.content.lower() for x in profanity):
                quality = 0
            elif any(x in message.content.lower() for x in high_quality):
                quality = 2
            else:
                quality = 1

            cursor = db.cursor()
            cursor.execute("INSERT INTO help_logs (user, content, datetime, quality) VALUES (`{user}`, `{content}`, `{time}`, `{quality}`);".format(user=message.author.id, content=message.content, time=int(time.time()), quality=quality))

        # Checks for things in message
        if any(x in message.content.lower() for x in email_checks) and message.server.id == config['akatsuki']['server_id']:
            if "badge" not in message.content.lower():
                await client.send_message(message.author, 'Right, this is an automated message as it was assumed you needed assitance in Akatsuki with: Email Verification\n\nAs the verification page says, Akatsuki does not use verification emails. To verify your account, simply install the switcher, install the certificate, click the server you\'d like to play on, and click On/Off, then login to osu! to complete the verification process.')
                await client.delete_message(message)
                if int(config['default']['debug']) == 1:
                    print(Fore.MAGENTA + "Triggered: Verification Email Support\nUser: {}".format(message.author))
            else:
                print(Fore.MAGENTA + "Aborted Trigger: Email Verification Support, due to \"badge\" contents of the message.\nUser: {}".format(message.author))

        elif any(x in message.content.lower() for x in filters) and message.author.id != config['discord']['owner_id']:
            cursor = db.cursor()
            cursor.execute("INSERT INTO profanity_filter (user, message, time) VALUES ('{user}', '{message}', '{time}');".format(user=message.author.id, message=message.content, time=int(time.time())))
            await client.delete_message(message)
            await client.send_message(message.author, 'Hello,\n\nYour message in osu!Akatsuki has been removed as it has been deemed unsuitable.\n\nIf this makes no sense, please report it to <@285190493703503872>.\n**Do not try to evade this filter as it is considered fair ground for a ban**.\n\n```{}```'.format(message.content))
            print(Fore.MAGENTA + "Filtered message | '{}: {}'".format(message.author, message.content))

        if message.server is None: # Private messages
                print(Fore.YELLOW + Style.BRIGHT + "{} [{}] {}: {}".format(message.timestamp, message.channel, message.author, message.content))

        elif config['discord']['owner_id'] in message.content: # When you are pinged
                print(Fore.CYAN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))

        elif (config['discord']['username'] in message.content.lower() and len(config['discord']['username']) > 1): # When your username is mentioned (either actual one, or custom set in configuration)
                print(Fore.GREEN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))

        elif message.server.id == config['akatsuki']['server_id']: # The server is akatsuki
            print(Fore.BLUE + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))
        else: # Regular message
            print("{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))

        if message.content.startswith('$'): # The message is a command

            # First of all, make a simpler way to deal with message content so u don't develop stage 4 cancer
            messagecontent = message.content.split(' ')

            #TODO: Process commands based on discord perms
            if message.author.id == config['discord']['owner_id']: # Process owner commands
                """
                Process owner commands. Only the config['discord']['owner_id'] has access to these.
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
                        await client.change_presence(game=discord.Game(name=game, url='https://akatsuki.pw/', type=0))

                        await client.send_message(message.channel, 'Game successfully changed to: \'{}\'.'.format(game))
                    else:
                        await client.send_message(message.channel, 'Please specify a game name.')
                    await client.delete_message(message)

                elif messagecontent[0].lower() == '$hs':
                    userID = re.findall('\d+', messagecontent[1])[0]

                    cursor = db.cursor()
                    cursor.execute("SELECT quality FROM help_logs WHERE user = {}".format(userID))
                    logs = cursor.fetchall()

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
                        await client.send_message(message.channel, 'No logs found on the specified user..')

                elif messagecontent[0].lower() == '$r':
                    try:
                        annmsg = ' '.join(messagecontent[1:]).strip()
                        if any(x in message.content.lower() for x in sql_checks):
                            await client.send_message(message.channel, '<@285190493703503872>')
                        else:
                            processingMessage = await client.send_message(message.channel, 'Processing request...')
                            params = urlencode({"k": config["akatsuki"]["apikey"], "to": "#admin", "msg": annmsg})
                            requests.get("http://{}:5001/api/v1/fokabotMessage?{}".format(config["akatsuki"]["ip"], params))
                            await client.send_message(message.channel, 'Successfully executed: `{}` on Akatsuki.'.format(annmsg))
                            await client.delete_message(processingMessage)
                    except:
                        await client.send_message(message.channel, 'Something went wrong.')
                """
                elif messagecontent[0].lower() == '$partner':
                    userID = messagecontent[1]
                    streamName = messagecontent[2]
                    platform = messagecontent[3]

                    if not platform.isdigit():
                        if platform == 'twitch':
                            platform = 1
                        elif platform == 'youtube':
                            platform = 2
                        elif platform == 'mixer':
                            platform = 3

                    cursor = db.cursor()
                    cursor.execute("SELECT * FROM partners WHERE userid = {}".format(userID))
                    result = cursor.fetchone()
                    if result is None:
                        cursor.execute("INSERT INTO partners (userid, stream_username, platform) VALUES ('{}', '{}', '{}')".format(userID, streamName, platform))
                        await client.send_message(message.channel, "{} has been sucessfully registered as an Akatsuki partner.".format(streamName))
                    else:
                        await client.send_message(message.channel, "That userID is already partnered!")

                elif messagecontent[0].lower() == '$removepartner':
                    streamName = messagecontent[1]

                    cursor = db.cursor()
                    cursor.execute("SELECT * FROM partners WHERE stream_username = {}".format(streamName))

                    if result is not None:
                        cursor.execute("DELETE FROM partners WHERE stream_username = {}".format(streamName))
                        await client.send_message(message.channel, "{}'s partnership sucessfully revoked.".format(streamName))
                    else:
                        await client.send_message(message.channel, "{} is not a registered partner.".format(streamName))

            
            Process regular user command.
            """
            if messagecontent[0].lower() == '$user' \
            or messagecontent[0].lower() == '$stats': # Akatsuki userinfo command
                username = messagecontent[1]
                try:
                    relax = messagecontent[2]
                except:
                    relax = ''

                if relax != '' and relax != '-rx':
                    await client.send_message(message.channel, "Please use underscores in your username rather than spaces.")
                else:
                    try:
                        processingMessage = await client.send_message(message.channel, 'Processing request...')

                        gamer = requests.get('https://akatsuki.pw/api/v1/get_user?u={}'.format(username)).text

                        gamerInfo = json.loads(gamer)

                        userID = int(gamerInfo[0]["user_id"])

                        resp = requests.get('https://akatsuki.pw/api/v1/users/{rx}full?id={userID}'.format(rx="rx" if relax == '-rx' else '', userID=userID), timeout=3).text
                        
                        userInfo = json.loads(resp)

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

                        embed = discord.Embed(title="{flag} {username} | {gm} {rx}".format(flag=":flag_{}:".format(userInfo["country"].lower()), username=userInfo["username"], rx='(Relax)' if relax == '-rx' else '(Vanilla)', gm=modeNice), description='** **', color=0x00ff00)
                        embed.set_thumbnail(url=akatsuki_logo)

                        embed.add_field(name="Global Rank", value="#{:,}".format(userInfo["{}".format(mode)]["global_leaderboard_rank"]), inline=True)
                        embed.add_field(name="Country Rank", value="#{:,}".format(userInfo["{}".format(mode)]["country_leaderboard_rank"]), inline=True)
                        embed.add_field(name="PP", value="{:,}pp".format(userInfo["{}".format(mode)]["pp"]), inline=True)
                        embed.add_field(name="Ranked Score", value="{:,}".format(userInfo["{}".format(mode)]["ranked_score"]), inline=True)
                        embed.add_field(name="Total Score", value="{:,}".format(userInfo["{}".format(mode)]["total_score"]), inline=True)
                        embed.add_field(name="Accuracy", value="{}%".format(round(userInfo["{}".format(mode)]["accuracy"], 2)), inline=True)
                        embed.add_field(name="Playcount", value="{:,}".format(userInfo["{}".format(mode)]["playcount"]), inline=True)
                        embed.add_field(name="Playtime", value="{:,} hours".format(round(int(userInfo["{}".format(mode)]["playtime"]) / 3600, 2)), inline=True)
                        embed.add_field(name="Replays Watched", value="{:,}".format(userInfo["{}".format(mode)]["replays_watched"]), inline=True)

                        await client.send_message(message.channel, embed=embed)
                        await client.delete_message(processingMessage)
                    except:
                        await client.send_message(message.channel, "Either that user does not exist, or the format of your message was incorrect. Format: | $stats username_spaced_like_this -rx\n\n(-rx is optional and will return -rx stats)")

            elif messagecontent[0].lower() == '$akatsuki': # multipurpose akatsuki info
                try:
                    topic = messagecontent[1].lower()
                except:
                    topic = ''

                if topic == '' or topic == 'help':
                    await client.send_message(message.channel, 'Please enter a topic. There are quite a few, so they will not be listed.')
                elif topic == 'discord':
                    await client.send_message(message.channel, 'https://discord.gg/5cBtMPW/')
                elif topic == 'twitch':
                    await client.send_message(message.channel, 'https://www.twitch.tv/akatsuki_pw/')
                elif topic == 'youtube' or topic == 'yt':
                    await client.send_message(message.channel, 'https://www.youtube.com/channel/UCjf8Fx_BlUr-htEy6hficcQ/')
                elif topic == 'rlb' or topic == 'relaxleaderboard':
                    await client.send_message(message.channel, 'https://akatsuki.pw/leaderboard?mode=0&p=1&rx=1/')
                elif topic == 'lb' or topic == 'leaderboard':
                    await client.send_message(message.channel, 'https://akatsuki.pw/leaderboard?mode=0&p=1&rx=0/')
                elif topic == 'admin':
                    await client.send_message(message.channel, 'https://old.akatsuki.pw/index.php?p=100/')
                elif topic == 'log' or topic == 'adminlog' or topic == 'raplog':
                    await client.send_message(message.channel, 'https://old.akatsuki.pw/index.php?p=116')
                elif topic == 'datadog' or topic == 'status':
                    await client.send_message(message.channel, 'https://p.datadoghq.com/sb/71577ef74-a079587e79/')
                elif topic == 'vote':
                    await client.send_message(message.channel, 'https://topg.org/osu-private-servers/in-509809')
                else:
                    await client.send_message(message.channel, 'That topic could not be found.')

            elif messagecontent[0].lower() == '$apply': # multipurpose staff application commands
                try:
                    position = messagecontent[1].lower()
                except:
                    position = ''

                if position == '' or position == 'help':
                    await client.send_message(message.channel, 'Please use a role name as an arguement. Eg: $apply bn, or $apply beatmap_nominator')
                elif 'admin' in position or position == 'commuinity_manager' or position == 'communitymanager':
                    await client.send_message(message.channel, 'You cannot apply for this role. Admins are handpicked from the community by cmyui himself :o')
                elif 'mod' in position:
                    await client.send_message(message.channel, 'You cannot apply for this role. Mods are usually handpicked from lower roles (such as BN, Akatsuki People, Support Team) if we believe they would be better suited with some fancy new powers.')
                elif 'beat' in position or position == 'bn':
                    await client.send_message(message.channel, 'BNs are currently in high demand! If you\'re interested in this position (and are quite active on the server, this will be checked), feel free to apply here! https://goo.gl/forms/XyLMtFlaA6mHAiIB3')
                elif 'support' in position:
                    await client.send_message(message.channel, 'To be considered for the support team, you will need to be quite active in the <#365413867167285249> channel already. We use this to ensure that you\'re the right kind of person for the job. Most likely, if we see you being active, we will offer you the position if you seem to be a good pick.')
                elif 'akatsuki' in position or 'people' in position or 'uploader' in position:
                    await client.send_message(message.channel, 'Looking to be an uploader?\n\nThere are actually some PC requirements for this, but they\'re really nothing special.\n- PC Capable of recording 1080p60fps videos without dropping below 4.2ms frametime (240fps).\n\nYea, that\'s it! haha. Even better if you can do 4K, or have editing capabilities.\n\nJust shoot <@285190493703503872> a DM to apply for this role.')
                elif position == 'premium' or position == 'donor' or position == 'donator' or position == 'supporter':
                    await client.send_message(message.channel, 'This isn\'t a role you can apply for, silly!\n\nSupporter: https://akatsuki.pw/donate\nPremium: https://akatsuki.pw/premium\n\nThanks for considering to support the server, though!\nIt means a lot!')
                elif 'verif' in position:
                    await client.send_message(message.channel, 'The verified role in-game is for players who we essentially trust (for lack of better wording). These players have either been verified through liveplays, or maybe have even met a staff member IRL to prove their legitimacy (rare, but there are 10+).\n\nYou cannot apply for verified, as it is something we will look to give you, rather than vice versa :^)')
                else:
                    await client.send_message(message.channel, 'That position could not be found.')

            elif messagecontent[0].lower() == '$cmyui': # cmyui command. Multipurpose information command on the guy
                try:
                    topic = messagecontent[1].lower()
                except:
                    topic = ''

                if topic == '' or topic == 'help':
                    await client.send_message(message.channel, 'The $cmyui command is just a dictionary of stuff cmyui has saved in it. Some public ones:\n\n$cmyui area - cmyui\'s area\n$cmyui skin - cmyui\'s skins\n$cmyui settings - cmyui\'s settings')
                elif topic == 'area':
                    await client.send_message(message.author, 'Wacom CTH-480 (CTL470 Pen)\n\n100mm width (forced proportions) [16:9 screen, making it 1.778:1]\nX : 0mm\nY : 57.79mm')
                    await client.send_message(message.channel, 'The response has been sent to you via DM.')
                elif topic == 'settings':
                    await client.send_message(message.author, '1.0x sens, video and storyboard off, dim 100%, fullscreen 1920x1080@240hz, snaking sliders, cursor size 0.60-0.84, hit lighting off, raw input off.')
                    await client.send_message(message.channel, 'The response has been sent to you via DM.')
                elif topic == 'skin':
                    await client.send_message(message.author, '**Here are some of the skins cmyui uses frequently**\n\nCurrent main skin (Abyssal 2018-15-06): https://i.namir.in/Asi.osk\n\nOther skins:\ncmyui v5.3: https://i.namir.in/6CF.osk\ncmyui v6.0 (Blue Crystal v2.1): https://i.namir.in/JS9.osk\ncmyui v7.0: https://i.namir.in/YP7.osk\ncmyui v9.4: https://i.namir.in/jHW.osk\nAlacrity 1.2: https://i.namir.in/4Oo.osk\ng3p: https://i.namir.in/Q1L.osk\nJustice: https://i.namir.in/b1u.osk\nCookiezi 32: https://i.namir.in/y8v.osk\nCookiezi 35: https://i.namir.in/y8v.osk\n\nIf any of the links are not working, please tell cmyui#0425 :)')
                    await client.send_message(message.channel, 'The response has been sent to you via DM.')
                elif topic == 'psyqui' or topic == 'yvs':
                    await client.send_message(message.channel, 'https://www.youtube.com/watch?v=wKgbDk2hXI8')
                else:
                    await client.send_message(message.channel, '$cmyui subcategory{topic} does not exist..'.format(topic=' ' + topic if len(topic) > 0 else ''))

            elif messagecontent[0].lower() == '$faq': # FAQ command
                try:
                    callback = messagecontent[1].lower()
                except:
                    callback = ''

                cursor = db.cursor()
                cursor.execute("SELECT * FROM discord_faq WHERE {type} = '{callback}' AND type = 1".format(type='id' if callback.isdigit() else 'topic', callback=callback))
                result = cursor.fetchone()

                if result is not None:
                    embed = discord.Embed(title=result[2], description='** **', color=0x00ff00)
                    embed.set_thumbnail(url=akatsuki_logo)
                    embed.add_field(name="** **", value=result[3].replace('\\n', '\n'), inline=result[5])
                    if result[4] is not None:
                        embed.set_footer(icon_url='', text=result[4].replace('\\n', '\n'))
                    await client.send_message(message.channel, embed=embed)
                else:
                    cursor.execute("SELECT id, topic, title from discord_faq WHERE type = 1")
                    faq_db = cursor.fetchall()
                    faq_list = ''
                    i = 0
                    for x in faq_db:
                        add_len = 16 - len(faq_db[i][1])
                        spaces = ''
                        spaces += ' ' * add_len

                        faq_list += '{}. {}{}|| {}\n'.format(i + 1, faq_db[i][1], spaces, faq_db[i][2])
                        i += 1

                    await client.send_message(message.channel, 'Invalid FAQ callback{topic}.\n\nHere is a list of available FAQ:\n```{faqlist}```'.format(topic=' ' + callback if len(callback) > 0 else '', faqlist=faq_list))

            elif messagecontent[0].lower() == '$info': # info command
                try:
                    callback = messagecontent[1].lower()
                except:
                    callback = ''

                cursor = db.cursor()
                cursor.execute("SELECT * FROM discord_faq WHERE {type} = '{callback}' AND type = 0".format(type='id' if callback.isdigit() else 'topic', callback=callback))
                result = cursor.fetchone()

                if result is not None:
                    embed = discord.Embed(title=result[2], description='** **', color=0x00ff00)
                    embed.set_thumbnail(url=akatsuki_logo)
                    embed.add_field(name="** **", value=result[3].replace('\\n', '\n'), inline=result[5])
                    if result[4] is not None:
                        embed.set_footer(icon_url='', text=result[4].replace('\\n', '\n'))
                    await client.send_message(message.channel, embed=embed)
                else:
                    cursor.execute("SELECT id, topic, title from discord_faq WHERE type = 0")

                    info_db = cursor.fetchall()

                    info_list = ''
                    i = 0
                    for x in info_db:
                        add_len = 16 - len(info_db[i][1])
                        spaces = ''
                        spaces += ' ' * add_len

                        info_list += '{}. {}{}|| {}\n'.format(i + 1, info_db[i][1], spaces, info_db[i][2])
                        i += 1

                    await client.send_message(message.channel, 'Invalid INFO callback{topic}.\n\nHere is a list of available INFO:\n```{infolist}```'.format(topic=' ' + callback if len(callback) > 0 else '', infolist=info_list))

            elif messagecontent[0].lower() == '$verify' and message.channel.id == config['akatsuki']['verify']: # Verify command
                verified = discord.utils.get(message.server.roles, name="Members")
                await client.add_roles(message.author, verified)
                await client.delete_message(message)

            elif messagecontent[0].lower() == '$botinfo': # Bot info command
                embed = discord.Embed(title="Why hello! I'm Aika.", description='** **', color=0x00ff00)
                embed.set_thumbnail(url=aika_pfp)
                embed.add_field(name="** **", value='I\'m Akatsuki\'s (and cmyui\'s) bot. I provide the server with things such as commands to track ingame stats, help out members in need, and provide overall fun (and lots of useless) commands!\n\nSource code: https://github.com/osuAkatsuki/Aika.\nIngame: https://akatsuki.pw/u/999\nCreator: https://akatsuki.pw/u/1001', inline=False)
                embed.set_footer(icon_url='', text='Good vibes <3')
                await client.send_message(message.channel, embed=embed)

            elif messagecontent[0].lower() == '$prune' and message.author.server_permissions.manage_messages: # Prune messages
                await client.send_message(message.channel, "This command has been depreciated. Please use Tatsumaki's ;;prune instead.")
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
                cursor.execute("SELECT * FROM discord_roles WHERE discordid = {}".format(message.author.id))
                result = cursor.fetchone()
                if result is not None:
                    if result[4] == 0:
                        role = discord.utils.get(message.server.roles, id=result[3])
                        await client.add_roles(message.author, role)
                        cursor.execute("UPDATE discord_roles SET verified = 1 WHERE discordid = {}".format(message.author.id))
                        await client.send_message(message.channel, "Your Discord has been sucessfully linked to your Akatsuki account.")
                    else:
                        await client.send_message(message.channel, "You already have an account linked!")
                else:
                    await client.send_message(message.channel, "Linking process initiated\n\nNext, please use the following command in #osu, or in a DM with 'Aika' ingame (in-game in the osu! client).\n`>> !linkdiscord {}`".format(message.author.id))

print(Fore.CYAN + "\nLogging in with credentials: {}".format('*' * len(config['discord']['token'])))
client.run(str(config['discord']['token']))