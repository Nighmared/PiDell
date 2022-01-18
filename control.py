import configparser
import logging
from datetime import datetime as dt
from datetime import timedelta
from enum import Enum
from os import path, system
from time import sleep
from typing import Callable
from urllib.error import HTTPError

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater

import deluge_module as dm
import log

log.get_ready()
logger = logging.getLogger(log.LOGGERNAME)

dir = path.dirname(__file__)

cfg_path = path.join(dir, "settings.ini")

config = configparser.ConfigParser()
config.read(cfg_path)
access_cfg = config["ACCESS"]


token = config.get("TELEGRAM", "token")
owner_id = int(config.get("TELEGRAM", "owner"))
admin_ids = list(map(int, config.get("TELEGRAM", "admins").split(",")))
if owner_id not in admin_ids:
    admin_ids.append(owner_id)

bot_start_time = dt.now()
is_up = system(f"ping -c 1 {access_cfg['server_address']} > /dev/null") == 0
up_since = dt.now() if is_up else None

updater = Updater(token=token)

torrent = dm.DelugeClient(
    host=config.get("DELUGE", "host"),
    port=config.getint("DELUGE", "port"),
    username=config.get("DELUGE", "username"),
    password=config.get("DELUGE", "password"),
    ratio=config.get("DELUGE", "stop_ratio"),
)


class Permissions(Enum):
    OWNER = 2
    ADMIN = 1
    DEFAULT = 0


def hasPermission(uid: int, lvl: Permissions) -> bool:
    if lvl == Permissions.OWNER:
        return uid == owner_id
    if lvl == Permissions.ADMIN:
        return uid in admin_ids or uid == owner_id
    return True


def reload_admins() -> None:
    global admin_ids
    admin_ids = list(map(int, config.get("TELEGRAM", "admins").split(",")))
    if owner_id not in admin_ids:
        admin_ids.append(owner_id)


def command(role: Permissions = Permissions.DEFAULT):
    def wrap2(func: Callable[[Update, CallbackContext], None]):
        def wrap(update: Update, ctxt: CallbackContext) -> None:
            logger.info(f"received {func.__name__} command")
            if not hasPermission(update.message.from_user.id, role):
                update.message.reply_text("🔒 Not authorized")
                return
            func(update, ctxt)

        updater.dispatcher.add_handler(CommandHandler(func.__name__, wrap))
        return wrap

    return wrap2


@command(Permissions.ADMIN)
def start(update: Update, context: CallbackContext) -> None:
    global is_up
    global up_since

    ret = system(
        f"sshpass -p '{access_cfg['password']}' ssh {access_cfg['username']}@{access_cfg['idrac_address']} racadm serveraction powerup"
    )
    if ret != 0:
        update.message.reply_text("❌ failed to start, got error code " + ret)
    else:
        is_up = True
        up_since = dt.now()
        update.message.reply_text("✅ issued poweron command")


@command(Permissions.ADMIN)
def stop(update: Update, context: CallbackContext) -> None:
    global is_up

    print(f"[{dt.now()}] received stop command")
    ret = system(
        f"sshpass -p '{access_cfg['password']}' ssh {access_cfg['username']}@{access_cfg['idrac_address']} racadm serveraction powerdown"
    )
    if ret != 0:
        update.message.reply_text("❌ failed to shutdown, got error code " + str(ret))
    else:
        is_up = False
        update.message.reply_text("✅ issued powerdown command")


@command(Permissions.OWNER)
def addadmin(update: Update, context: CallbackContext) -> None:
    current_admins = admin_ids[::]
    try:
        to_add_id = int(update.message.text[9:].strip().split(" ")[0])
    except:
        to_add_id = -1
    if to_add_id in current_admins or to_add_id < 0:
        update.message.reply_text("🤷 Either no user id given or user is already admin")
        return

    current_admins.append(to_add_id)
    output_admins = ",".join(map(str, current_admins))
    config.set("TELEGRAM", "admins", output_admins)
    with open(cfg_path, "w") as cfg_file:
        config.write(cfg_file)
    reload_admins()
    update.message.reply_text(
        f"✅ the following uids are currently admins: {str(admin_ids)}"
    )


@command(Permissions.ADMIN)
def getadmins(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        f"ℹ️ The following uids are currently admins: {', '.join(map(str,admin_ids))}"
    )


@command(Permissions.OWNER)
def deladmin(update: Update, context: CallbackContext) -> None:
    current_admins = admin_ids[::]  # remove duplicates ....
    try:
        to_del_id = int(update.message.text[9:].strip().split(" ")[0])
    except:
        print(update.message.text[9:].strip().split(" "))
        to_del_id = -1
    if to_del_id not in current_admins or to_del_id < 0:
        print(to_del_id, current_admins)
        update.message.reply_text("🤷 Either no user id given or user isn't admin")
        return

    current_admins.remove(to_del_id)
    output_admins = ",".join(map(str, current_admins))
    config.set("TELEGRAM", "admins", output_admins)
    with open(cfg_path, "w") as cfg_file:
        config.write(cfg_file)
    reload_admins()
    update.message.reply_text(
        f"✅ the following uids are currently admins: {str(admin_ids)}"
    )


@command()
def whatsmyid(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("ℹ️ Your id is: " + str(update.message.from_user.id))


def timedelta_to_nice_time(delta: timedelta) -> str:
    seconds = delta.seconds
    d = delta.days
    h = seconds // 3600
    seconds %= 3600
    m = seconds // 60
    seconds %= 60
    s = seconds
    timestring = ""
    if d > 0:
        timestring += f"{d}d "
    if h > 0:
        timestring += f"{h}h "
    if m > 0:
        timestring += f"{m}min "
    if s > 0:
        timestring += f"{s}s"
    return timestring


@command(Permissions.ADMIN)
def gettorrents(update: Update, context: CallbackContext) -> None:
    if not is_up:
        update.message.reply_text("Server not up")
        return

    res, err = torrent.get_torrents()
    if err:
        update.message.reply_text("Failed to get torrents: " + str(err))
        return

    update.message.reply_text(res)


@command(Permissions.OWNER)
def addmovie(update: Update, context: CallbackContext) -> None:
    if not is_up:
        update.message.reply_text("Server not up")
        return

    link = context.args[0]
    res = add_torrent(link, "/Movies")
    update.message.reply_text(res)


def add_torrent(link: str, path: str) -> None:
    completepath = config.get("DELUGE", "base_location") + path
    res, err = torrent.add_torrent(link, completepath)
    if err:
        return "failed to add torrent: " + str(err)
    return res


# @command
def pauseall(update: Update, context: CallbackContext):
    if not hasPermission(update.message.from_user.id, Permissions.OWNER):
        update.message.reply_text("🔒 Not authorized")
        return

    if not is_up:
        update.message.reply_text("Server not up")
        return

    _, err = torrent.pause_all()
    if err:
        print(err)
        update.message.reply_text("Failed to pause: " + str(err))
        return
    update.message.reply_text("Paused all torrents")


@command(Permissions.ADMIN)
def ping(update: Update, context: CallbackContext) -> None:
    PINGRESPONSEEMOTE = "ℹ️"
    global is_up, up_since
    was = is_up
    is_up = system(f"ping -c 1 {access_cfg['server_address']} > /dev/null") == 0
    if is_up != was:
        if is_up:
            up_since = dt.now()
            update.message.reply_text(
                PINGRESPONSEEMOTE + "\nExpected: Offline\nActual:  Online\n🤭"
            )
        else:
            update.message.reply_text(
                PINGRESPONSEEMOTE + "\nExpected: Online\nActual:  Offline\n🤭"
            )
    else:
        if is_up:
            update.message.reply_text(
                PINGRESPONSEEMOTE + "\nExpected: Online\nActual:  Online\n💁"
            )
        else:
            update.message.reply_text(
                PINGRESPONSEEMOTE + "\nExpected: Offline\nActual:  Offline\n💁"
            )


@command()
def uptime(update: Update, context: CallbackContext) -> None:
    if is_up:
        update.message.reply_text(
            "⌚ Server up for (at least): "
            + timedelta_to_nice_time((dt.now() - up_since))
            + "\n🤖 Bot has been running for: "
            + timedelta_to_nice_time(dt.now() - bot_start_time)
        )

    else:
        update.message.reply_text(
            "😴 Server not online (if you think it actually is online, use /ping to have me check the status again)"
            + "\n🤖 Bot has been running for: "
            + timedelta_to_nice_time(dt.now() - bot_start_time)
        )


def errorh(update: Update, context: CallbackContext) -> None:
    logger.fatal(context.error)
    if isinstance(context.error, HTTPError):
        sleep(60)  # give it some time


updater.dispatcher.add_error_handler(errorh)
print("Bot up!")
updater.start_polling()
updater.idle()
