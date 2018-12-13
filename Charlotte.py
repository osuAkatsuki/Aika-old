import discord
import asyncio
import configparser
import re
import logging
import traceback
from colorama import init
from colorama import Fore, Back, Style
from secret import scoreFlags

# Initialize colorama owo
init(autoreset=True)

# Discord Client
client = discord.Client()

# Configuration
config = configparser.ConfigParser()
config.sections()
config.read('config.ini')

#Constants
version = 1.17
servers = ['yozora', 'ainu', 'kotorikku', 'kawata', 'toh.ru', 'ryusei', 'ryu-sei', 'waving', 'enjuu', 'verge', 'toh ru']
emailChecks = ['verify e', 'verification', 'on email', 'verify m', 'verify a', 'email t']

# Startup, after login action
@client.event
async def on_ready():
    print(Fore.GREEN + '\nAuthentication Successful.\n{} | {}\n--------------------------\n'.format(client.user.name,client.user.id))
    if int(config['default']['debug']) == 1:
        print(Fore.MAGENTA + "\n\nConfiguration:\ndebug: {}\n\n".format(config['default']['debug']))

    # Send an announcement that the bots been started in Akatsuki's #general (if debug)
    if config['default']['debug'] == 1:
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
            # I really don't know how to do this :(
            # Private Messaging
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
        elif any(x in message.content.lower() for x in servers):
            await client.delete_message(message)  # Remove other private server-related messages

        if message.server is None: # Private messages
                print(Fore.YELLOW + Style.BRIGHT + "{} [{}] {}: {}".format(message.timestamp, message.channel, message.author, message.content))
        elif config['discord']['owner_id'] in message.content: # When you are pinged
                print(Fore.CYAN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))
        elif (config['discord']['username'] in message.content.lower() and len(config['discord']['username']) > 1): # When your username is mentioned (either actual one, or custom set in configuration)
                print(Fore.GREEN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))

                # add if thing for new config here
        elif message.server.id in config['default']['important_servers']: # important_servers from configuration file
            if message.channel.id == config['akatsuki']['general']: # Akatsuki's discord server id
                # Play my fucking audio file here when thats a thing
                print(Back.CYAN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))
            else:
                print(Fore.BLUE + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))
        else: # Regular message
            print("{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))

        if int(config['default']['commands_enabled']) == 1 and message.content.startswith('$'): # The message is a command. handle it that way owo..
            #TODO: Process commands based on discord perms
            if message.author.id == config['discord']['owner_id']: # Process owner commands
                """
                Process owner commands. Only the config['discord']['owner_id'] has access to these.
                """

                if message.content.startswith('$flags'):
                    # Check osu! score flags.. in discord!
                    await client.delete_message(message)  # Remove $f
                    if config['default']['secret']:
                        print("\n")
                        flags = ''.join(message.content[3:]).strip() # Get the flags from discord message
                        if flags.isdigit():
                            scoreFlags.calculateFlags(int(flags))
                        else:
                            print(Fore.RED + "That is not a valid entry.")
                    else:
                        print(Fore.RED + "You do not have secret enabled in config.")

                elif message.content.startswith('$game'):
                    # Change your discord users status / game
                    game = ''.join(message.content[3:]).strip() # Get the game
                    if game: # Game also changed

                        """
                        game Variables:
                        name = name of the game
                        url = link for the game (usually for streaming probably)
                        type = boolean to show whether streaming or not
                        """
                        await client.change_presence(game=discord.Game(name=game, url='https://akatsuki.pw/', type=0))

                        print(Fore.GREEN + Style.BRIGHT + "Game changed to: {}".format(game))
                        await client.delete_message(message) # Remove $s
                    else:
                        print(Fore.RED + Style.BRIGHT + "Please specify a game name.")
                        await client.delete_message(message) # Remove $s

                elif message.content.startswith('$p'): # prune messages
                    amtMessages = ''.join(message.content[3:]).strip() if len(''.join(message.content[3:]).strip()) > 0 else 100 # Get the amt of messages
                    deleted = await client.purge_from(message.channel, limit=int(amtMessages))
                    await client.send_message(message.channel, 'Deleted {} message(s).'.format(len(deleted)))

            """ otherwise
            Process regular user command. Anyone can use these!
            """
            if message.content.startswith('$faq'): # FAQ command
                topic = ''.join(message.content[5:]).strip().lower()
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

            elif message.content.startswith('$verify') and message.channel.id == config['akatsuki']['verify']: # Verify command
                verified = discord.utils.get(message.server.roles, name="Members")
                await client.add_roles(message.author, verified)
                await client.send_message(message.channel, "User verified successfully.")


if int(config['default']['debug']) == 1:
    print(Fore.MAGENTA + "Logging in with credentials: {}".format('*' * len(config['discord']['token'])))
client.run(str(config['discord']['token']))