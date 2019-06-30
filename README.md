[![Akatsuki's Discord](https://discordapp.com/api/guilds/365406575893938177/widget.png?style=shield)](https://discord.gg/5cBtMPW)

## Aika

This is Akatsuki's discord bot's source code.

## Requirements
- Python3
- Requirements from requirements.txt

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
[mysql]
host = mysql access point
user = mysql username
passwd = mysql passwd
db = mysql db
```
Finish up by installing requirements.txt, and then you're on your way.
```
$ pip3 install -r requirements.txt
```
Done!
```
$ python3 Aika.py
```
