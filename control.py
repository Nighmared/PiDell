"""Main script for the PiDell Telegram Bot"""
import logging
from datetime import datetime as dt
from datetime import timedelta
from enum import Enum
from os import environ as env
from os import path, system
from time import sleep
from typing import Callable

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater
from urllib3.exceptions import HTTPError

import dbhandler
import dbsetup
import deluge_module as dm
import idrac_web_puppet
import log

__author__ = "nighmared"
__version__ = "1.1"

log.get_ready()
logger = logging.getLogger(log.LOGGERNAME)

dirname = path.dirname(__file__)

access_cfg = {
    "username": env.get("SERVER_USERNAME"),
    "password": env.get("SERVER_PASSWORD"),
    "idrac_address": env.get("MANAGE_IP"),
    "server_address": env.get("SERVER_IP"),
}

telegram_cfg = {
    "owner": int(env.get("TELEGRAM_OWNER_ID")),
    "token": env.get("TELEGRAM_BOT_TOKEN"),
    "dbpath": env.get("DBPATH"),
}

deluge_cfg = {
    "host": env.get("DELUGE_HOST"),
    "port": int(env.get("DELUGE_PORT")),
    "username": env.get("DELUGE_USERNAME"),
    "password": env.get("DELUGE_PASSWORD"),
    "base_dir": env.get("DELUGE_BASE_DIR"),
    "stop_ratio": env.get("DELUGE_STOP_RATIO"),
}

PINGRESPONSEEMOTE = "ℹ️"

OWNER_ID = telegram_cfg["owner"]
ADMIN_IDS = [
    OWNER_ID,
]

DB_NEWLY_CREATED = dbsetup.setup(telegram_cfg["dbpath"])  # ensures table exists
db = dbhandler.Dbhandler(telegram_cfg["dbpath"])
if DB_NEWLY_CREATED:
    db.add_admin(OWNER_ID)

for admin in db.get_admins():
    if admin not in ADMIN_IDS:
        ADMIN_IDS.append(admin)


bot_start_time = dt.now()
IS_UP = system(f"ping -c 1 -w 3 {access_cfg['server_address']} > /dev/null") == 0
UP_SINCE = dt.now() if IS_UP else None

updater = Updater(token=telegram_cfg["token"])

torrent = dm.DelugeClient(
    host=deluge_cfg["host"],
    port=deluge_cfg["port"],
    username=deluge_cfg["username"],
    password=deluge_cfg["password"],
    ratio=deluge_cfg["stop_ratio"],
)


class Permissions(Enum):
    "Enum for permissin classes"
    OWNER = 2
    ADMIN = 1
    DEFAULT = 0


class Powercommands(Enum):
    """
    Enum for possible power commands
    that can be issued on the server
    """

    POWERUP = "powerup"
    POWERDOWN = "powerdown"
    GRACEDOWN = "graceful shutdown"


def get_action_name(cmd: Powercommands):
    """
    Maps the available power commands to
    an "action" word that can be used in
    a message
    """
    action_names = {
        Powercommands.POWERDOWN: "stop",
        Powercommands.POWERUP: "start",
        Powercommands.GRACEDOWN: "shutdown",
    }
    return action_names[cmd]


def has_permission(uid: int, lvl: Permissions) -> bool:
    """returns whether a specific user has >= the passed
    permission level according to the enum ordering"""
    if lvl == Permissions.OWNER:
        return uid == OWNER_ID
    if lvl == Permissions.ADMIN:
        return uid in ADMIN_IDS or uid == OWNER_ID
    return True


def reload_admins() -> None:
    """
    reloads the list of admins uids
    from the db
    """
    global ADMIN_IDS
    ADMIN_IDS = list(db.get_admins())
    if OWNER_ID not in ADMIN_IDS:
        ADMIN_IDS.append(OWNER_ID)


def deprecated(func: Callable[[Update, CallbackContext], None]):
    """
    decorator to mark a command as deprecated
    """

    def wrap(update: Update, ctxt: CallbackContext) -> None:
        update.message.reply_text(
            f"/{func.__name__} is deprecated and might be removed in the future"
        )
        return func(update, ctxt)

    # looks sketchy but neccessary for further
    # processing in the command decorator
    wrap.__name__ = func.__name__
    return wrap


def command(role: Permissions = Permissions.DEFAULT):
    """Decorator to make a method into a bot command.
    The command will have the name of the function. The
    decorator must be called as a function with a permission
    Level as optional argument"""

    def wrap2(func: Callable[[Update, CallbackContext], None]):
        def wrap(update: Update, ctxt: CallbackContext) -> None:
            logger.info("received %s command", func.__name__)
            if not has_permission(update.message.from_user.id, role):
                update.message.reply_text("🔒 Not authorized")
                return
            func(update, ctxt)

        updater.dispatcher.add_handler(CommandHandler(func.__name__, wrap))
        return wrap

    return wrap2


def get_to_know_host(ip_address):
    """This bypasses the ssh warning
    about a host's fingerprint not being known"""
    logger.warning("Failed to start/stop, trying to add to known_hosts file")
    ret = system(f"ssh-keyscan -t ecdsa {ip_address} >> /root/.ssh/known_hosts")
    return ret


def issue_power_command(cmd: Powercommands):
    """
    Function called the power command
    wrapper. Issues the given `Powercommand`
    to the server via either racadm or the
    selenium wrapper
    """
    if cmd == Powercommands.GRACEDOWN:
        try:
            idrac_web_puppet.graceful_shutdown(access_cfg=access_cfg)
            return 0
        except Exception:
            logger.critical("exception at shutdown", exc_info=True)
            return 1
    else:
        return system(
            f"sshpass -p '{access_cfg['password']}'"
            + "ssh {access_cfg['username']}@{access_cfg['idrac_address']}"
            + "racadm serveraction {cmd.value}"
        )


def power_command_wrapper(cmd: Powercommands):
    """
    used by all power related commands to prevent
    a lot of duplicate code. can be called to
    issue one of the available `Powercommands`
    """
    global IS_UP
    global UP_SINCE
    cmdname = cmd.value
    action_name = get_action_name(cmd)
    ret1 = issue_power_command(cmd)
    # error code for sshpass receiving the warning about unknown ssh host
    if ret1 == 1536:
        ret2 = get_to_know_host(access_cfg["idrac_address"])
        if ret2 == 0:
            ret3 = issue_power_command(cmd)
            if ret3 == 0:
                reply = (
                    f"✅ issued {cmdname} command\n"
                    + "ℹ️ Failed at first but successfully added to known_hosts file and retried"
                )
            else:
                reply = f"❌ failed to {action_name}, got error code {ret3}"
        else:
            reply = f"❌ failed to {action_name},\
                failed to add key to known hosts,\n got error: {ret2}"
    elif ret1 != 0:
        reply = f"❌ failed to {action_name}, got error code {ret1}"
    else:
        reply = f"✅ issued {cmdname} command"
        if cmd == Powercommands.POWERUP:
            IS_UP = True
            if not IS_UP:
                UP_SINCE = dt.now()
        elif cmd in (Powercommands.POWERDOWN, Powercommands.GRACEDOWN):
            IS_UP = False
    return reply


@command(Permissions.ADMIN)
def start(update: Update, _context: CallbackContext) -> None:
    """Command to boot the server"""
    reply = power_command_wrapper(Powercommands.POWERUP)
    update.message.reply_text(reply)


@command(Permissions.ADMIN)
@deprecated
def stop(update: Update, _context: CallbackContext) -> None:
    """Old command for shutting down server"""
    update.message.reply_text(
        "ℹ️stop command has changed, you are probably looking for /shutdown"
    )


@command(Permissions.OWNER)
def forcestop(update: Update, _context: CallbackContext) -> None:
    """Command to turn of the servers power. In most situations
    shutdown should be used instead"""
    reply = power_command_wrapper(Powercommands.POWERDOWN)
    update.message.reply_text(reply)


@command(Permissions.ADMIN)
def shutdown(update: Update, _context: CallbackContext) -> None:
    """Command to gracefully shut the server down"""
    reply = power_command_wrapper(Powercommands.GRACEDOWN)
    update.message.reply_text(reply)


@command(Permissions.OWNER)
def addadmin(update: Update, _context: CallbackContext) -> None:
    """Command to add a telegram uid as admin"""
    reload_admins()
    try:
        to_add_id = int(update.message.text[9:].strip().split(" ")[0])
    except Exception:
        to_add_id = -1
    if to_add_id in ADMIN_IDS or to_add_id < 0:
        update.message.reply_text(
            "🤷 Either no/invalid user id given or user is already admin"
        )
        return

    db.add_admin(to_add_id)
    reload_admins()
    update.message.reply_text(
        f"✅ the following uids are currently admins: {str(ADMIN_IDS)}"
    )


@command(Permissions.ADMIN)
def getadmins(update: Update, _context: CallbackContext) -> None:
    """Command to get a list of admin uids"""
    reload_admins()
    update.message.reply_text(
        f"ℹ️ The following uids are currently admins: {', '.join(map(str,ADMIN_IDS))}"
    )


@command(Permissions.OWNER)
def deladmin(update: Update, _context: CallbackContext) -> None:
    """Command to remove an uid from the list of admins"""
    reload_admins()
    try:
        to_del_id = int(update.message.text[9:].strip().split(" ")[0])
    except Exception:
        print(update.message.text[9:].strip().split(" "))
        to_del_id = -1
    if to_del_id not in ADMIN_IDS or to_del_id < 0:
        update.message.reply_text("🤷 Either no user id given or user isn't admin")
        return

    db.del_admin(to_del_id)
    reload_admins()
    update.message.reply_text(
        f"✅ the following uids are currently admins: {str(ADMIN_IDS)}"
    )


@command()
def whatsmyid(update: Update, _context: CallbackContext) -> None:
    """Command to find out one's own telegram uid"""
    update.message.reply_text("ℹ️ Your id is: " + str(update.message.from_user.id))


def timedelta_to_nice_time(delta: timedelta) -> str:
    """function to convert a `timedelta` into
    a nice string representation"""
    seconds = delta.seconds
    days = delta.days
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    timestring = ""
    if days > 0:
        timestring += f"{days}d "
    if hours > 0:
        timestring += f"{hours}h "
    if minutes > 0:
        timestring += f"{minutes}min "
    if seconds > 0:
        timestring += f"{seconds}s"
    return timestring


@command(Permissions.ADMIN)
@deprecated
def gettorrents(update: Update, _context: CallbackContext) -> None:
    """Old command interacting with the deluge-client module to
    return a list of active torrents"""
    if not IS_UP:
        update.message.reply_text("Server not up")
        return

    res, err = torrent.get_torrents()
    if err:
        update.message.reply_text("Failed to get torrents: " + str(err))
        return
    logger.info("[gettorrents] sending msg: %s", res)
    update.message.reply_text(res)


@command(Permissions.ADMIN)
def ping(update: Update, _context: CallbackContext) -> None:
    """Command to re-check whether the
    server is online or not"""
    global IS_UP, UP_SINCE
    was = IS_UP
    IS_UP = system(f"ping -c 1 -w 2 {access_cfg['server_address']} > /dev/null") == 0
    if IS_UP != was:
        if IS_UP:
            UP_SINCE = dt.now()
            update.message.reply_text(
                PINGRESPONSEEMOTE + "\nExpected: Offline\nActual:  Online\n🤭"
            )
        else:
            update.message.reply_text(
                PINGRESPONSEEMOTE + "\nExpected: Online\nActual:  Offline\n🤭"
            )
    else:
        if IS_UP:
            update.message.reply_text(
                PINGRESPONSEEMOTE + "\nExpected: Online\nActual:  Online\n💁"
            )
        else:
            update.message.reply_text(
                PINGRESPONSEEMOTE + "\nExpected: Offline\nActual:  Offline\n💁"
            )


@command()
def uptime(update: Update, _context: CallbackContext) -> None:
    """Command to check bot and server uptime"""
    if IS_UP:
        update.message.reply_text(
            "⌚ Server up for (at least): "
            + timedelta_to_nice_time((dt.now() - UP_SINCE))
            + "\n🤖 Bot has been running for: "
            + timedelta_to_nice_time(dt.now() - bot_start_time)
        )

    else:
        update.message.reply_text(
            "😴 Server not online (if you think it actually"
            + " is online, use /ping to have me check the status again)"
            + "\n🤖 Bot has been running for: "
            + timedelta_to_nice_time(dt.now() - bot_start_time)
        )


def errorh(_update: Update, context: CallbackContext) -> None:
    """Error handling callback function for the telegram-bot instance"""
    logger.critical(context.error, exc_info=1)
    if isinstance(context.error, HTTPError):
        sleep(60)  # give it some time


updater.dispatcher.add_error_handler(errorh)
print("Bot up!")
updater.start_polling()
updater.idle()
