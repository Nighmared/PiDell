
# Dell Poweredge Telegram Controller Bot [1]

[![main](https://github.com/Nighmared/PiDell/actions/workflows/main.yml/badge.svg)](https://github.com/Nighmared/PiDell/actions/workflows/main.yml)
[![staging](https://github.com/Nighmared/PiDell/actions/workflows/staging.yml/badge.svg)](https://github.com/Nighmared/PiDell/actions/workflows/staging.yml)

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

[Optional] If you want to override the defaults for the values defined in `default.env` you can do so by creating a file called `.env` and define the values you want in there. These env variables are used in the `docker-compose.yml` file. Currently the following variables are defined in that way:
- MAIN_DNS & FALLBACK_DNS are the ip adresses of 2 DNS servers

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


### Notice
Basically all torrent related functionality becomes obsolete once one starts using Radarr/Sonarr and a reverse proxy... D;



















[1] Suggestions for a better name? anyone?

