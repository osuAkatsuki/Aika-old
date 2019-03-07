[![Discord](https://discordapp.com/api/guilds/365406575893938177/widget.png?style=shield)](https://discord.gg/5cBtMPW)

## Aika

This is Akatsuki's discord bot's source code.

## Requirements
- Python
- Colorama 0.4.0

## How to set up this thing
I don't really think you'd ever want to, but heres a thing anyways.
```
$ git clone https://github.com/osuAkatsuki/Aika.git
```
Then rename your config sample to just config.ini
```
$ mv config.sample.ini config.ini
```
Next, configure the config

The default config should be pretty straight forward. If you're using a token to login to discord, make sure tokenauth is 1, and then just paste your token in. If you're using email/password, disable tokenauth and put the username and password in instead.
```
[default]
debug = 0/1, whether to show debug messages or not
announce_online = 0/1, whether to announce when the bot is online in whatever specified channel from config

[discord]
owner_id = your personal discord id
token = token here if tokenAuth = 1
username = username here (optional)

[akatsuki]
general = your server's #general id
server_id = your server's id
player_reporting = your server's #player-reporting id
reports = your server's #reports id
help = your server's #help id
verify = your server's verify channel
apikey = your banchos apikey
ip = your server's ip

[mysql]
host = mysql access point
user = mysql username
passwd = mysql passwd
db = mysql db
```
Finish up by installing requirements.txt, and then you're on your way.
```
$ pip3 install requirements.txt
```
Done!
```
$ python3 Aika.py
```
