import configparser
from datetime import datetime as dt
from datetime import timedelta
from os import path, system

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater

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


def reload_admins():
    global admin_ids
    admin_ids = list(map(int, config.get("TELEGRAM", "admins").split(",")))
    if owner_id not in admin_ids:
        admin_ids.append(owner_id)


def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)


def start(update: Update, context: CallbackContext) -> None:
    global is_up
    global up_since
    if update.message.from_user.id not in admin_ids:
        # Not authorized
        print(
            f"[{dt.now()}] User {update.message.from_user.name} tried to use admin-only command"
        )
        update.message.reply_text("🔒 Not authorized")
        return
    print(f"[{dt.now()}] received start command")
    ret = system(
        f"sshpass -p '{access_cfg['password']}' ssh {access_cfg['username']}@{access_cfg['idrac_address']} racadm serveraction powerup"
    )
    if ret != 0:
        update.message.reply_text("❌ failed to start, got error code " + ret)
    else:
        is_up = True
        up_since = dt.now()
        update.message.reply_text("✅ issued poweron command")


def stop(update: Update, context: CallbackContext) -> None:
    global is_up
    if update.message.from_user.id not in admin_ids:
        # Not authorized
        print(
            f"[{dt.now()}] User {update.message.from_user.name} tried to use admin-only command"
        )
        update.message.reply_text("🔒 Not authorized")
        return
    print(f"[{dt.now()}] received stop command")
    ret = system(
        f"sshpass -p '{access_cfg['password']}' ssh {access_cfg['username']}@{access_cfg['idrac_address']} racadm serveraction powerdown"
    )
    if ret != 0:
        update.message.reply_text("❌ failed to shutdown, got error code " + str(ret))
    else:
        is_up = False
        update.message.reply_text("✅ issued powerdown command")


def addadmin(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != owner_id:
        print(
            f"[{dt.now()}] User {update.message.from_user.name} tried to use owner-only command"
        )
        update.message.reply_text("🔒 Not authorized")
        return
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


def deladmin(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != owner_id:
        print(
            f"[{dt.now()}] User {update.message.from_user.name} tried to use owner-only command"
        )
        update.message.reply_text("🔒 Not authorized")
        return
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


def whatsmyid(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("ℹ️ Your id is: " + str(update.message.from_user.id))


def timedelta_to_nice_time(delta: timedelta) -> str:
    seconds = delta.seconds
    h = seconds // 3600
    seconds %= 3600
    m = seconds // 60
    seconds %= 60
    s = seconds
    timestring = ""
    if h > 0:
        timestring += f"{h}h "
    if m > 0:
        timestring += f"{m}min "
    if s > 0:
        timestring += f"{s}s"
    return timestring


def debug(update, context):
    print(update.message)


def uptime(update: Update, context: CallbackContext) -> None:
    if is_up:
        update.message.reply_text(
            "⌚ Server up for (at least): "
            + timedelta_to_nice_time((dt.now() - up_since))
            + "\n🤖 Bot has been running for: "
            + timedelta_to_nice_time(dt.now() - bot_start_time)
        )

    else:
        update.message.reply_text("😴 Server not online")


def errorh(update: Update, context: CallbackContext) -> None:
    print(update.message)
    print(context.error)


updater = Updater(token=token)
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("stop", stop))
updater.dispatcher.add_handler(CommandHandler("uptime", uptime))
updater.dispatcher.add_handler(CommandHandler("addadmin", addadmin))
updater.dispatcher.add_handler(CommandHandler("deladmin", deladmin))
updater.dispatcher.add_handler(CommandHandler("whatsmyid", whatsmyid))
updater.dispatcher.add_error_handler(errorh)

print("Bot up!")
updater.start_polling()
updater.idle()
