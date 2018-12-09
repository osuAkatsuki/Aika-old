[![Discord](https://discordapp.com/api/guilds/365406575893938177/widget.png?style=shield)](https://discord.gg/5cBtMPW)

## Charlotte

This is Akatsuki's discord bot's source code.

## Requirements
- Python
- Colorama 0.4.0

## How to set up this thing
I don't really think you'd ever want to, but heres a thing anyways.
```
$ git clone https://github.com/cmyui/Charlotte.git
```
Then rename your config sample to just config.ini
```
$ mv config.sample.ini config.ini
```
Next, configure the config

The default config should be pretty straight forward. If you're using a token to login to discord, make sure tokenauth is 1, and then just paste your token in. If you're using email/password, disable tokenauth and put the username and password in instead.
```
[default]
debug = 0
tokenauth = 1
important_servers: [2147, 483, 647]
secret = 0
report_pm = 1
commands_enabled = 1

[discord]
owner_id = your personal discord id
token = token here if tokenAuth = 1
username = username here (optional)
email = email here if tokenAuth = 0
password = password here if tokenAuth = 0
```
Finish up by installing requirements.txt, and then you're on your way.
```
$ pip3 install requirements.txt
```
Done!
```
$ python3 Charlotte.py
```
