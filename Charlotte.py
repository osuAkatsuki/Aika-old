import discord
import asyncio
import configparser
import re
import logging
import traceback
import requests
import json
from colorama import init
from colorama import Fore, Back, Style
from secret import scoreFlags
from urllib.parse import urlencode

# Initialize colorama owo
init(autoreset=True)

# Discord Client
client = discord.Client()

# Configuration
config = configparser.ConfigParser()
config.sections()
config.read('config.ini')

#Constants
version = 1.25
servers = ['yozora', 'ainu', 'kotorikku', 'kawata', 'toh.ru', 'ryusei', 'ryu-sei', 'waving', 'enjuu', 'verge', 'toh ru', 'toh-ru']
emailChecks = ['verify e', 'verification', 'on email', 'verify m', 'verify a', 'email t']
SQLChecks = [';', 'drop', 'ripple', 'select', '*'] # because im paranoid as fuck

# Startup, after login action
@client.event
async def on_ready():
    print(Fore.GREEN + '\nAuthentication Successful.\n{} | {}\n------------------------------\n'.format(client.user.name,client.user.id))
    print(Fore.MAGENTA + "\n\nConfiguration:\nDebug: {debug}\n\n".format(debug="True" if int(config['default']['debug']) == 1 else "False"))

    # Send an announcement that the bots been started in Akatsuki's #general (if debug)
    if int(config['default']['debug']) == 1:
        announceOnline = discord.Embed(title="Charlotte v{versionNum} Online.".format(versionNum=version), description='Ready for commands owo\n\nSource code can be found at https://github.com/osuAkatsuki/Charlotte.', color=0x00ff00)
        announceOnline.set_thumbnail(url='https://i.namir.in/5kE.png')
        await client.send_message(client.get_channel(config['akatsuki']['general']), embed=announceOnline)

# On exceptions, don't make the whole thing die :)
@client.event
async def on_error(event, *args):
    print(Fore.RED + "\n\nAn exception has occurred.\n\nError: {}\nargs: {}\n\nTraceback: {}\n".format(event, *args, logging.warning(traceback.format_exc())))

# On message event
@client.event
async def on_message(message):
    client.wait_until_ready()

    if message.channel.id == config['akatsuki']['player_reporting'] and not message.startswith('$'): # message sent in #player-reporting, move to #reports, unless it is a command
        await client.delete_message(message) # delete the message from #player-reporting

        # Prepare, and send the report in #reports
        embed = discord.Embed(title="New report recieved.", description='** **', color=0x00ff00)
        embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
        embed.add_field(name="Report content", value=message.content, inline=True)
        embed.add_field(name="Author", value=message.author.mention, inline=True)
        await client.send_message(client.get_channel(config['akatsuki']['reports']), embed=embed)

        # Prepare, and send the report to the reporter
        embedPrivate = discord.Embed(title="Thank you for the player report.", description="We will review the report shortly.".format(message.content), color=0x00ff00)
        embedPrivate.add_field(name="Report content", value=message.content, inline=True)
        embedPrivate.set_thumbnail(url='https://i.namir.in/Mbp.png')
        await client.send_message(message.author, embed=embedPrivate)

        # Send the report to the bot owner, if enabled in config
        if config['default']['report_pm'] == 1:
            await client.send_message(channel=discord.User(id=int(config['discord']['owner_id'])), embed=embed)

        # Print result to console
        print(Fore.CYAN + "Report recieved. It has been moved to #reports{end}".format(end=" and sent to {}.".format(config['discord']['username']) if config['default']['report_pm'] == 1 else "."))
    elif message.author != client.user:
        # Checks for things in message
        if any(x in message.content.lower() for x in emailChecks):
            if message.server is None:
                if "badge" not in message.content.lower():
                    await client.send_message(message.author, 'Right, this is an automated message as it was presumed your message was about: Email Verification\n\nAs the verification page says, Akatsuki does not use verification emails. To verify your account, simply install the switcher, install the certificate, click the server you\'d like to play on, and click On/Off, then login to osu! to complete the verification process.')
                    if int(config['default']['debug']) == 1:
                        print(Fore.MAGENTA + "Triggered: Verification Email Support\nUser: {}".format(message.author))
                    else:
                        print(Fore.MAGENTA + "Aborted Trigger: Email Verification Support, due to \"badge\" contents of the message.\nUser: {}".format(message.author))
            # Akatsuki's ServerID
            elif message.server.id == config['akatsuki']['server_id']:
                if "badge" not in message.content.lower():
                    await client.send_message(message.author, 'Right, this is an automated message as it was assumed you needed assitance in Akatsuki with: Email Verification\n\nAs the verification page says, Akatsuki does not use verification emails. To verify your account, simply install the switcher, install the certificate, click the server you\'d like to play on, and click On/Off, then login to osu! to complete the verification process.')
                    await client.delete_message(message)
                    if int(config['default']['debug']) == 1:
                        print(Fore.MAGENTA + "Triggered: Verification Email Support\nUser: {}".format(message.author))
                else:
                    print(Fore.MAGENTA + "Aborted Trigger: Email Verification Support, due to \"badge\" contents of the message.\nUser: {}".format(message.author))
        elif any(x in message.content.lower() for x in servers) or 'discord.gg/' in message.content.lower() and message.author.id != config['discord']['owner_id']:
            await client.delete_message(message)  # Remove other private server-related messages

        if message.server is None: # Private messages
                print(Fore.YELLOW + Style.BRIGHT + "{} [{}] {}: {}".format(message.timestamp, message.channel, message.author, message.content))
        elif config['discord']['owner_id'] in message.content: # When you are pinged
                print(Fore.CYAN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))
        elif (config['discord']['username'] in message.content.lower() and len(config['discord']['username']) > 1): # When your username is mentioned (either actual one, or custom set in configuration)
                print(Fore.GREEN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))

                # add if thing for new config here
        elif message.server.id in config['default']['important_servers']: # important_servers from configuration file
            print(Fore.BLUE + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))
        else: # Regular message
            print("{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))

        if int(config['default']['commands_enabled']) == 1 and message.content.startswith('$'): # The message is a command. handle it that way owo..
            messagecontent = message.content.split(' ')
            #TODO: Process commands based on discord perms
            if message.author.id == config['discord']['owner_id']: # Process owner commands
                """
                Process owner commands. Only the config['discord']['owner_id'] has access to these.
                """

                if messagecontent[0].lower() == '$flags':
                    # Check osu! score flags.. in discord!
                    await client.delete_message(message)  # Remove $f
                    if config['default']['secret']:
                        print("\n")
                        flags = messagecontent[1] # Get the flags from discord message
                        if flags.isdigit():
                            scoreFlags.calculateFlags(int(flags))
                        else:
                            print(Fore.RED + "That is not a valid entry.")
                    else:
                        print(Fore.RED + "You do not have secret enabled in config.")

                elif messagecontent[0].lower() == '$game':
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
                    await client.delete_message(message) # Remove $s

                elif messagecontent[0].lower() == '$info':
                    try:
                        topic = messagecontent[1].lower()
                    except:
                        topic = ''

                    if topic == 'welcome':
                        embed = discord.Embed(title="Welcome to the Akatsuki Discord!", description='** **', color=0x00ff00)
                        embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
                        embed.add_field(name="** **", value='Hi! Welcome to our little corner of the internet.\n\nYou\'re probably rushing around trying to figure out to verify, but I\'m here to tell you to calm down. We have the 10-minute waiting period for a reason, and that is so that you take a moment to read <#426852938107977738>. Please do this, as I bet that it\'ll fix your issues. After you\'ve read through it and 10 minutes have passed, feel free to type $verify in the <#459856640049676299> channel to get full access to all the cool features of the discord.\n\nAkatsuki is an osu! private server and community run predominantly by <@285190493703503872> and <@107356210486898688>. We currently run an osu! server with some pretty unique and awesome features, such as relax score submission, with a custom PP algorithm . None of this would be possible without our contributors, donators (both premium, and supporters), and especially the Ripple developers for the base of which we started this project on.\n\n[osu!Akatsuki](https://akatsuki.pw/)', inline=False)
                        await client.send_message(message.channel, embed=embed)
                    elif topic == 'chatrules':
                        embed = discord.Embed(title="Akatsuki Discord & Chat Rules", description='** **', color=0x00ff00)
                        embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
                        embed.add_field(name="** **", value='These are the rules that apply to the Akatsuki Discord, and also the in-game chat on the Akatsuki Server.\n\n1. NSFW material is only permitted within the <#428460752698081291> and <#505960162411020288> channels.\n2. No talk about other osu! private servers will be permitted.\n3. Racism, sexism, toxicity, and hate speech will not be tolerated.\n4. Spamming is obviously not permitted.\n5. Do not make any kind of cheating accusation, use <#367068661837725706>.\n6. Keep memes and such to the <#463420430552662017> channel.\n7. Treat all members of Akatsuki with respect.\n8. Advertising other discord servers in any way is not allowed.\n9. Do not excessively highlight other members of the community.\n10. Do not discuss cheating activities.\n11. If you leave the discord, you permanently forfeit your roles. Don’t expect to rejoin and bug staff for them back.', inline=False)
                        embed.set_footer(icon_url='', text='Please remember we reserve the right to kick you without a reason/notice.')
                        await client.send_message(message.channel, embed=embed)
                    elif topic == 'gamerules':
                        embed = discord.Embed(title="Akatsuki Discord & Chat Rules", description='** **', color=0x00ff00)
                        embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
                        embed.add_field(name="** **", value='These are the rules that apply in-game on the Akatsuki Server.\n\n1. Cheating and any other form of hacking are strictly prohibited.\n2. You are allowed to have 1 account on the Akatsuki server.\n3. Impersonation of any other player is not permitted.\n4. Edited clients are not permitted on Akatsuki (with the exception of osu!Sync).\n5. Shared or boosted accounts are not allowed.\n6. Do not try to exploit bugs found on the server, report them to a developer immediately.', inline=False)
                        embed.set_footer(icon_url='', text='Overall, do not abuse our patience. We provide this server free of charge for the community, and you will be banned from the community if we deem it necessary.')
                        await client.send_message(message.channel, embed=embed)
                    else:
                        await client.send_message(message.channel, 'Invalid INFO callback{topic}.. Try harder?'.format(topic=' ' + topic if len(topic) > 0 else ''))

                elif messagecontent[0].lower() == '$r':
                    try:
                        annmsg = ' '.join(messagecontent[1:]).strip()
                        if any(x in message.content.lower() for x in SQLChecks):
                            await client.send_message(message.channel, 'nice try fucker. <@285190493703503872>')
                        else:
                            processingMessage = await client.send_message(message.channel, 'Processing request...')
                            params = urlencode({"k": config["akatsuki"]["apikey"], "to": "#admin", "msg": annmsg})
                            requests.get("http://{}:5001/api/v1/fokabotMessage?{}".format(config["akatsuki"]["ip"], params))
                            await client.send_message(message.channel, 'Successfully executed: `{}` on Akatsuki.'.format(annmsg))
                            await client.delete_message(processingMessage)
                    except:
                        await client.send_message(message.channel, 'something exploded. L')

            """ otherwise
            Process regular user command.
            """
            if messagecontent[0].lower() == '$user': # akatsuki userinfo command
                userID = messagecontent[1]
                try:
                    relax = messagecontent[2]
                except:
                    relax = ''

                processingMessage = await client.send_message(message.channel, 'Processing request...')

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
                embed.set_thumbnail(url='https://i.namir.in/Mbp.png')

                embed.add_field(name="Global Rank", value="#{:,}".format(userInfo["{}".format(mode)]["global_leaderboard_rank"]), inline=True)
                embed.add_field(name="Country Rank", value="#{:,}".format(userInfo["{}".format(mode)]["country_leaderboard_rank"]), inline=True)
                embed.add_field(name="PP", value="{:,}pp".format(userInfo["{}".format(mode)]["pp"]), inline=True)
                embed.add_field(name="Ranked Score", value="{:,}".format(userInfo["{}".format(mode)]["ranked_score"]), inline=True)
                embed.add_field(name="Total Score", value="{:,}".format(userInfo["{}".format(mode)]["total_score"]), inline=True)
                embed.add_field(name="Accuracy", value=userInfo["{}".format(mode)]["accuracy"], inline=True)
                embed.add_field(name="Playcount", value="{:,}".format(userInfo["{}".format(mode)]["playcount"]), inline=True)
                embed.add_field(name="Replays Watched", value="{:,}".format(userInfo["{}".format(mode)]["replays_watched"]), inline=True)

                await client.send_message(message.channel, embed=embed)
                await client.delete_message(processingMessage)

            elif messagecontent[0].lower() == '$faq': # FAQ command
                try:
                    topic = messagecontent[1].lower()
                except:
                    topic = ''

                if topic == 'namechange':
                    embed = discord.Embed(title="Akatsuki name changes.", description='** **', color=0x00ff00)
                    embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
                    embed.add_field(name="** **", value='Name changes (both in-game, and on the discord), are an Akatsuki Supporter donation perk. Additional details can be found here: https://akatsuki.pw/donate', inline=False)
                    await client.send_message(message.channel, embed=embed)

                elif topic == 'appeal':
                    embed = discord.Embed(title="Appealing your Akatsuki restriction.", description='** **', color=0x00ff00)
                    embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
                    embed.add_field(name="** **", value='Akatsuki does not accept unrestriction appeals under usual circumstances. If you believe your restriction was false, you may contact an Administrator. Remember that we are not idiots, and that we are usually 100% confident in our restrictions. If you try to abuse this, you will be permanently blacklisted from the community alltogether.', inline=False)
                    await client.send_message(message.channel, embed=embed)

                elif topic == 'email':
                    embed = discord.Embed(title="Why has my verification email not arrived?", description='** **', color=0x00ff00)
                    embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
                    embed.add_field(name="** **", value='As the verification page says, Akatsuki does not use verification emails. To verify your account, simply install the switcher, install the certificate, click the server you\'d like to play on, and click On/Off, then login to osu! to complete the verification process.', inline=False)
                    await client.send_message(message.channel, embed=embed)

                elif topic == 'readonly':
                    embed = discord.Embed(title="\"Error writing to hosts file, readonly mode\" error while using switcher", description='** **', color=0x00ff00)
                    embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
                    embed.add_field(name="** **", value="Ensure you are running the switcher as Administrator, and disable your anti-virus (or add the switcher as an exclusion) and try again. As mentioned before, this is triggered since the switcher edits a system file (hosts).\n\nIf it still does not work, feel free to edit your hosts file yourself by adding these to the bottom of your hosts file (found at \"C:\\Windows\\System32\\Drivers\\etc\"). You will need to run notepad as admin, then use ctrl + o to open the file, as it is a system file.\n\n```\n163.172.67.35    osu.ppy.sh\n163.172.67.35    c.ppy.sh\n163.172.67.35    c1.ppy.sh\n163.172.67.35    c2.ppy.sh\n163.172.67.35    c3.ppy.sh\n163.172.67.35    c4.ppy.sh\n163.172.67.35    c5.ppy.sh\n163.172.67.35    c6.ppy.sh\n163.172.67.35    ce.ppy.sh\n163.172.67.35    a.ppy.sh\n163.172.67.35    s.ppy.sh\n163.172.67.35    i.ppy.sh```", inline=False)
                    await client.send_message(message.channel, embed=embed)

                elif topic == 'cert':
                    embed = discord.Embed(title="\"Connection failed. Retrying in 30s...\" while connecting to Akatsuki", description='** **', color=0x00ff00)
                    embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
                    embed.add_field(name="** **", value="This means that your hosts file has most likely successfully been redirected via the hosts file, but your certificate is somehow not working. Please check https://c.ppy.sh/ and refer to the possibilities below:\n\nA. Page unsafe warning\nFix: This means the certificate is infact invalid/not working. If this happens, please install the certificate 'ca.crt', which can be found at the bottom of the <#365413867167285249> channel, as this gif does: https://cdn.discordapp.com/attachments/365413867167285249/405175068965076992/2017-11-27_03-41-35.gif.\n\nB. osu!Bancho page\nFix: This means your hosts file actually was not written, or redirection is not working in some way, but somehow your osu! is still being redirected? Move to <#365413867167285249>.", inline=False)
                    await client.send_message(message.channel, embed=embed)

                elif topic == 'hosts':
                    embed = discord.Embed(title="\"Bancho authentication failed. Please check your username/password by clicking the user panel on the main menu.\" while connecting to Akatsuki.", description='** **', color=0x00ff00)
                    embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
                    embed.add_field(name="** **", value="This means that your osu! is connected to either Akatsuki or Bancho (or whatever other server you were playing on), but is failing on login. This usually either means:\nA. You registered on the wrong server; Akatsuki has two servers, regular and relax.\nFix: Please ensure you registered on the correct website for the respective servers, as they have separate logins (https://osu.akatsuki.pw/, https://relax.akatsuki.pw/).\n\nB. Your switcher did not properly write to the hosts file, and you are still connected to a different server (most likely Bancho).\nFix: Refer to the first FAQ to locate your hosts file, and ensure the ppy.sh related lines are there. If not, add them and try again. If you cannot solve your problem, move to <#365413867167285249>.\n\nC. You did not restart your osu! after switching servers\nFix: Simply restart your game and try again.", inline=False)
                    await client.send_message(message.channel, embed=embed)

                elif topic == 'linux':
                    embed = discord.Embed(title="\"Error writing to hosts file, readonly mode\" error while using switcher", description='** **', color=0x00ff00)
                    embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
                    embed.add_field(name="** **", value="Connecting via Linux or OS X is a bit more tricky than windows, as you will have to do it manually, rather than using a server switcher.\nFirst, you will need to locate your hosts file. Since different non-windows operating systems have different directories for this file, please just google your operating system's hosts file to save some time.\nOnce you have located this file, paste the following lines in:\n\nRelax```\n163.172.67.35    osu.ppy.sh\n163.172.67.35    c.ppy.sh\n163.172.67.35    c1.ppy.sh\n163.172.67.35    c2.ppy.sh\n163.172.67.35    c3.ppy.sh\n163.172.67.35    c4.ppy.sh\n163.172.67.35    c5.ppy.sh\n163.172.67.35    c6.ppy.sh\n163.172.67.35    ce.ppy.sh\n163.172.67.35    a.ppy.sh\n163.172.67.35    s.ppy.sh\n163.172.67.35    i.ppy.sh```\n\nNext, you will need to install the certificate. Again, this is different from OS to OS, so you'll need to google this one aswell. The cerificate you'll need to install is 'ca.crt', which can be found at the bottom of this channel.", inline=False)
                    await client.send_message(message.channel, embed=embed)
                else:
                    await client.send_message(message.channel, 'Invalid FAQ callback{topic}.. Try harder?'.format(topic=' ' + topic if len(topic) > 0 else ''))

            elif messagecontent[0].lower() == '$verify' and message.channel.id == config['akatsuki']['verify']: # Verify command
                verified = discord.utils.get(message.server.roles, name="Members")
                await client.add_roles(message.author, verified)
                await client.send_message(message.channel, "User verified successfully.")

            elif messagecontent[0].lower() == '$prune' and message.author.server_permissions.manage_messages: # prune messages
                try:
                    amtMessages = messagecontent[1]
                except:
                    amtMessages = 100

                if str(amtMessages).isdigit() and int(amtMessages) <= 1000:
                    deleted = await client.purge_from(message.channel, limit=int(amtMessages) + 1)
                    await client.send_message(message.channel, 'Deleted {} message(s).'.format(len(deleted) - 1))
                else:
                    await client.send_message(message.channel, 'Incorrect syntax. Please use: $prune <1 - 1000>.')


if int(config['default']['debug']) == 1:
    print(Fore.MAGENTA + "Logging in with credentials: {}".format('*' * len(config['discord']['token'])))
client.run(str(config['discord']['token']))