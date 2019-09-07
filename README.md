[![Akatsuki's Discord](https://discordapp.com/api/guilds/365406575893938177/widget.png?style=shield)](https://discord.gg/5cBtMPW)

## Aika (rewrite) -- osu!Akatsuki's Discord bot.

Hello! However you happened to stumble upon this repository, welcome!

Aika is essentially the place I decided to take my small knowledge of python, and see what I could do. It's not much, but it's provided me with a lot of learning over the last little bit.

Apparently it's good enough that other osu! servers have decided to fork and use it aswell! If that's what you're interested in doing, feel free to give it a shot (although I'm sure you'd be better off finding an alternative, or making one yourself!).

## Requirements
- Python>=3.6 (fstrings are used, so 3.6 is a minimum)
- Requirements (pip3 install -r requirements.txt)

## How to set up Aika.
If you're actually planning on setting it up, it might be a bit difficult as I don't completely plan on spoonfeeding. This means no SQL will be provided, and I will most likely not be of very much help if you run into an issue.
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
{
    "SQL_HOST": "",
    "SQL_USER": "",
    "SQL_PASS": "",
    "SQL_DB": ""
}
```
Finish up by installing requirements.txt, and then you're on your way.
```
$ pip3 install -r requirements.txt
```
Done!
```
$ python3.6 Aika.py
```