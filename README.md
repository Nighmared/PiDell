# Dell Poweredge Telegram Controller Bot [1]



This is a python program to issue basic power commands to a Dell Poweredge Server via a Telegram bot. I came up with it because I host my Plex server on an ancient Dell PowerEdge and don't need it to be online all the time but would still like to boot it remotely. First i was using the Internet router's built-in VPN functionality, but then the router started to randomly decide to turn the VPN off. So here we are. I now have a Raspi sitting on top of my server and running that Telegram bot to control the aforementioned server. Works perfectly so far.



## Requirements

- Docker
- docker-compose

## Getting started

Create a `settings.env` file that defines the parameters given in `settings.default.env`
- MANAGE_IP is the ip of the idrac interface
- SERVER_USERNAME/SERVER_PASSWORD have to be credentials for the idrac interface
- SERVER_IP is the ip of the OS when the server is up
- TELEGRAM_OWNER_ID is the telegram User ID of the owner account
- DELUGE_USERNAME/ DELUGE_PASSWORD are credentials for a deluge account as described [here](https://dev.deluge-torrent.org/wiki/UserGuide/Authentication)


run the bot with `docker-compose up --build -d`



## Usage

The bot only provides a few commands as of now, the naming of which should explain enough about what they do:

| Everyone   | Admins       | Owner      |
| ---------- | ------------ | ---------- |
| /uptime    | /start       | /addadmin  |
| /whatsmyid | /stop        | /deladmin  |
|            | /ping        | /getadmins |
|            | /gettorrents | /addmovie  |
|            |              | /addseries |























[1] Suggestions for a better name? anyone?

