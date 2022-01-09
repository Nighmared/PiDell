# Dell Poweredge Telegram Controller Bot [1]



This is a python program to issue basic power commands to a Dell Poweredge Server via a Telegram bot. I came up with it because I host my Plex server on an ancient Dell PowerEdge and don't need it to be online all the time but would still like to boot it remotely. First i was using the Internet router's built-in VPN functionality, but then the router started to randomly decide to turn the VPN off. So here we are. I now have a Raspi sitting on top of my server and running that Telegram bot to control the aforementioned server. Works perfectly so far.



## Requirements

- python-telegram-bot (install via `pip install -r requirements.txt`)
- `sshpass` (install via package manager)
- Python >3.6 (f-strings)



## Getting started

Create a `settings.ini` file that defines the parameters given in `settings.ini.default`

run the bot with `python control.py`



## Usage

The bot only provides a few commands as of now, the naming of which should explain enough about what they do:

| Everyone   | Admins | Owner     |
| ---------- | ------ | --------- |
| /uptime    | /start | /addadmin |
| /whatsmyid | /stop  | /deladmin |























[1] Suggestions for a better name? anyone?

