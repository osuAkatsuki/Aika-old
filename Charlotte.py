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
version = 1.1

# Startup, after login action
@client.event
async def on_ready():
    print(Fore.GREEN + '\nAuthentication Successful.\n{} | {}\n--------------------------\n'.format(client.user.name,client.user.id))
    if int(config['default']['debug']) == 1:
        print(Fore.MAGENTA + "\n\nConfiguration:\ndebug: {}\ntokenauth: {}\n\n".format(config['default']['debug'], config['default']['tokenauth']))

    # Send an announcement that the bots been started in Akatsuki's #general
    announceOnline = discord.Embed(title="Charlotte v{versionNum} Online.".format(versionNum=version), description='Ready for commands owo\n\nSource code can be found at https://github.com/cmyui/Charlotte.', color=0x00ff00)
    announceOnline.set_thumbnail(url='https://i.namir.in/5kE.png')
    await client.send_message(client.get_channel('365406576548511745'), embed=announceOnline)

# On exceptions, don't make the whole thing die :)
@client.event
async def on_error(event, *args):
    print(Fore.RED + "\n\nFuck.\n\nError: {}\nargs: {}\n\nTraceback: {}\n".format(event, *args, logging.warning(traceback.format_exc())))

# On message event
@client.event
async def on_message(message):
    client.wait_until_ready()

    if message.channel.id == '367068661837725706': # message sent in #player-reporting, move to #reports
        await client.delete_message(message) # delete the message from #player-reporting

        # Prepare, and send the report in #reports
        embed = discord.Embed(title="New report recieved.", description='** **', color=0x00ff00)
        embed.set_thumbnail(url='https://i.namir.in/Mbp.png')
        embed.add_field(name="Report content", value=message.content, inline=True)
        embed.add_field(name="Author", value=message.author.mention, inline=True)
        await client.send_message(client.get_channel('367080772076568596'), embed=embed)

        # Prepare, and send the report to the reporter
        embedPrivate = discord.Embed(title="Thank you for the player report.", description="We will review the report shortly.".format(message.content), color=0x00ff00)
        embedPrivate.add_field(name="Report content", value=message.content, inline=True)
        embedPrivate.set_thumbnail(url='https://i.namir.in/Mbp.png')
        await client.send_message(message.author, embed=embedPrivate)

        # Send the report to the bot owner, if enabled in config
        if config['default']['report_pm'] == 1:
            await client.send_message(channel=discord.User(id=config['discord']['owner_id']), embed=embed)

        # Print result to console
        print(Fore.CYAN + "Report recieved. It has been moved to #reports{end}".format(end=" and sent to {}.".format(config['discord']['username']) if config['default']['report_pm'] == 1 else "."))
    elif message.author != client.user:
        if ("verify e" in message.content.lower() or
        "verification" in message.content.lower() or
        "on email" in message.content.lower() or
        "verify m" in message.content.lower() or
        "verify a" in message.content.lower() or
        "email t" in message.content.lower()) and message.author != client.user:

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
            elif message.server.id == '365406575893938177':
                if "badge" not in message.content.lower():
                    await client.send_message(message.author, 'Right, this is an automated message as it was assumed you needed assitance in Akatsuki with: Email Verification\n\nAs the verification page says, Akatsuki does not use verification emails. To verify your account, simply install the switcher, install the certificate, click the server you\'d like to play on, and click On/Off, then login to osu! to complete the verification process.')
                    if int(config['default']['debug']) == 1:
                        print(Fore.MAGENTA + "Triggered: Verification Email Support\nUser: {}".format(message.author))
                else:
                    print(Fore.MAGENTA + "Aborted Trigger: Email Verification Support, due to \"badge\" contents of the message.\nUser: {}".format(message.author))
        
        if message.server is None: # Private messages
                print(Fore.YELLOW + Style.BRIGHT + "{} [{}] {}: {}".format(message.timestamp, message.channel, message.author, message.content))
        elif config['discord']['owner_id'] in message.content: # When you are pinged
                print(Fore.CYAN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))
        elif (config['discord']['username'] in message.content.lower() and len(config['discord']['username']) > 1): # When your username is mentioned (either actual one, or custom set in configuration)
                print(Fore.GREEN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))

                # add if thing for new config here
        elif message.server.id in config['default']['important_servers']: # important_servers from configuration file
            if message.channel.id == '508022888113111040': # Akatsuki's discord server id
                # Play my fucking audio file here when thats a thing
                print(Back.CYAN + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))
            else:
                print(Fore.BLUE + Style.BRIGHT + "{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))
        else: # Regular message
            print("{} [{} ({})] {}: {}".format(message.timestamp, message.server, message.channel, message.author, message.content))

        if config['default']['commands_enabled'] == 1:
            if message.content.startswith('$f') and message.author.id == config['discord']['owner_id']:
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

            elif message.content.startswith('$s') and message.author == config['discord']['owner_id']:
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
            else:
                print(Fore.RED + 'This feature could not be found, or in unavailable.')

if int(config['default']['tokenauth']) == 1:
    if int(config['default']['debug']) == 1:
        print(Fore.MAGENTA + "Logging in with credentials: {}".format('*' * len(config['discord']['token'])))
    client.run(str(config['discord']['token']))
elif int(config['default']['tokenauth']) == 0:
    if int(config['default']['debug']) == 1:
        print(Fore.MAGENTA + "Logging in with credentials: {}, {}".format(config['discord']['email'], '*' * len(config['discord']['password'])))
    client.run('{}'.format(config['discord']['email']), '{}'.format(config['discord']['password']))