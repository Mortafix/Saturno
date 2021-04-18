from datetime import datetime
from json import dump, load
from os import path, walk
from re import search

from colorifix.colorifix import Background, Color, Style, erase, paint, sample
from pymortafix.utils import direct_input, strict_input
from saturno.anime import search_anime
from telegram import Bot
from telegram.error import InvalidToken

# --- Config file


def get_config():
    return load(open(f"{path.abspath(path.dirname(__file__))}/config.json"))


def save_config(config_dict):
    return dump(
        config_dict,
        open(f"{path.abspath(path.dirname(__file__))}/config.json", "w"),
        indent=4,
    )


def remove_anime(index):
    config = get_config()
    config["anime"] = [
        anime for i, anime in enumerate(config.get("anime")) if index != i
    ]
    save_config(config)


def add_anime(name, link, season, folder, mode):
    new = {"name": name, "site": link, "season": season, "folder": folder, "mode": mode}
    config = get_config()
    config["anime"] += [new]
    save_config(config)


def add_new_path(path):
    config = get_config()
    config["path"] = path
    save_config(config)


def is_folder_unique(folder_name):
    folders = [anime.get("folder") for anime in get_config().get("anime")]
    return folder_name not in folders


def add_telegram_config(bot_token, chat_id):
    config = get_config()
    config["telegram-bot-token"] = bot_token
    config["telegram-chat-id"] = chat_id
    save_config(config)


def add_colors(colors):
    json_labels = [
        "anime-name-menu",
        "season-menu",
        "mode-menu",
        "action-download",
        "anime-name-download",
        "episode-download",
        "setting",
        "button",
    ]
    colors_save = {k: c for k, c in zip(json_labels, colors)}
    config = get_config()
    config["colors"] = colors_save
    save_config(config)


# --- Pretty Print


def pprint_row(anime_name, season, mode, index=False, remove=False):
    if index and remove:
        return paint(f"[#] {anime_name} [{mode}]", background=Background.RED)
    if index and not remove:
        ret_str = paint("[>] ", c_anime_menu) + paint(anime_name, c_anime_menu)
    else:
        ret_str = "[ ] " + paint(anime_name)
    return (
        ret_str
        + paint(f" (s{season}) ", c_season_menu)
        + paint(f"[{mode}]", c_mode_menu)
    )


def pprint_anime(anime_list, index, remove=None):
    if not anime_list:
        return "No anime added.."
    return "\n".join(
        [
            pprint_row(name, season, mode, index == i, remove=remove)
            for i, (name, _, season, _, mode) in enumerate(anime_list)
        ]
    )


def pprint_actions(mode=None):
    if mode == "confirm":
        actions = {"y": "confirm", "b": "back"}
    elif mode == "add":
        actions = {"ws": "move", "c": "confirm", "b": "back"}
    elif mode == "back":
        actions = {"b": "back"}
    elif mode == "settings":
        actions = {
            "u": "backup",
            "r": "restore",
            "p": "path",
            "t": "telegram",
            "c": "colors",
            "b": "back",
        }
    elif mode == "path":
        actions = {"e": "edit", "b": "back"}
    else:
        actions = {
            "ws": "move",
            "a": "add",
            "r": "remove",
            "e": "settings",
            "q": "quit",
        }
    return (
        "-" * sum(len(action) + 5 for action in actions.values())
        + "\n"
        + " ".join(
            f"[{paint(key,style=Style.BOLD)}]:{paint(action,c_button)}"
            for key, action in actions.items()
        )
    )


def pprint_query(query_list, selected):
    return "\n".join(
        paint(f"[>] {name}", c_anime_menu) if selected == i else f"[ ] {name}"
        for i, (name, _) in enumerate(query_list)
    )


def pprint_settings():
    config = get_config()
    labels = ("Current path", "Backup", "Telegram")
    path_str = paint(config.get("path"), c_settings)
    backup = get_last_backup()
    backup_str = paint(backup, c_settings)
    telegram_str = (
        (
            paint(config.get("telegram-bot-token"), c_settings)
            + paint(":", style=Style.BOLD)
            + paint(config.get("telegram-chat-id"), c_settings)
        )
        if config.get("telegram-bot-token")
        else ""
    )
    values = (path_str, backup_str, telegram_str)
    return "\n".join(
        f"{paint(lab,style=Style.BOLD)}: {val}" for lab, val in zip(labels, values)
    )


def get_last_backup():
    _, _, files = list(walk("."))[0]
    backups = sorted(
        [file for file in files if search(r"saturno-backup\.json$", file)], reverse=True
    )
    return backups[0] if backups else ""


def recap_new_anime(name, url, season, folder, mode):
    return (
        f"Name: {paint(name,c_settings)}\n"
        f"Link: {paint(url,c_settings)}\n"
        f"Stagione {paint(season,c_settings)}\n"
        f"Folder: {paint(folder,c_settings)}\n"
        f"Mode: {paint(mode,c_settings)}"
    )


# --- Input


def is_bot_valid(token):
    try:
        Bot(token)
        return True
    except InvalidToken:
        return False


def is_color_valid(color):
    return color.lower() in COLORS.keys()


# --- Colors

COLORS = {
    "blue": Color.BLUE,
    "red": Color.RED,
    "green": Color.GREEN,
    "magenta": Color.MAGENTA,
    "cyan": Color.CYAN,
    "yellow": Color.YELLOW,
    "gray": Color.GRAY,
    "white": Color.WHITE,
    "black": Color.BLACK,
}


def string_to_color(color):
    return COLORS.get(color, Color.WHITE)


CONFIG_COLORS = get_config().get("colors")
c_anime_menu = string_to_color(CONFIG_COLORS.get("anime-name-menu"))
c_season_menu = string_to_color(CONFIG_COLORS.get("season-menu"))
c_mode_menu = string_to_color(CONFIG_COLORS.get("mode-menu"))
c_settings = string_to_color(CONFIG_COLORS.get("setting"))
c_button = string_to_color(CONFIG_COLORS.get("button"))

# --- Manage


def manage():
    index = 0
    k = "start"
    while k != "q":
        anime_list = [list(anime.values()) for anime in get_config().get("anime")]
        print(pprint_anime(anime_list, index))
        print(pprint_actions())
        k = direct_input(choices=("w", "s", "e", "a", "r", "q"))
        erase(len(anime_list or [0]) + 2)

        if k in ("w", "s"):
            if k == "w" and index:
                index -= 1
            if k == "s" and index < len(anime_list) - 1:
                index += 1

        if k == "e":
            e_k = "start"
            while e_k != "b":
                print(pprint_settings())
                print(pprint_actions(mode="settings"))
                e_k = direct_input(choices=("u", "r", "p", "t", "c", "b"))
                erase(5)
                if e_k == "p":
                    base = paint("Path", style=Style.BOLD) + ": "
                    new_path = strict_input(
                        base,
                        wrong_text=paint("Wrong path! ", Color.RED) + base,
                        check=path.exists,
                        flush=True,
                    )
                    add_new_path(new_path)
                    e_k = ""
                elif e_k == "r":
                    backup_filename = get_last_backup()
                    if backup_filename:
                        backup_dict = load(open(backup_filename))
                        save_config(backup_dict)
                elif e_k == "u":
                    now = datetime.now()
                    config = get_config()
                    dump(
                        config,
                        open(f"{now:%Y-%m-%d}_saturno-backup.json", "w"),
                        indent=4,
                    )
                elif e_k == "t":
                    base = paint("Telegram bot token", style=Style.BOLD) + ": "
                    telegram_bot_token = strict_input(
                        base,
                        wrong_text=paint("Invalid token! ", Color.RED) + base,
                        check=is_bot_valid,
                        flush=True,
                    )
                    base = paint("Telegram chat ID", style=Style.BOLD) + ": "
                    telegram_chat_id = strict_input(
                        base,
                        wrong_text=paint("Invalid chat ID! ", Color.RED) + base,
                        regex=r"\-?\d+$",
                        flush=True,
                    )
                    add_telegram_config(telegram_bot_token, telegram_chat_id)
                elif e_k == "c":
                    print("Color can be:", end="")
                    sample("color")
                    erase(2)
                    color_labels = [
                        "anime name [menu]",
                        "season [menu]",
                        "mode [menu]",
                        "action [download]",
                        "anime name [download]",
                        "episode [download]",
                        "setting",
                        "button legend",
                    ]
                    colors = list()
                    for label in color_labels:
                        base = "Color for " + paint(f"{label}", style=Style.BOLD) + ": "
                        color_choose = strict_input(
                            base,
                            wrong_text=paint("Invalid color! ", Color.RED) + base,
                            check=is_color_valid,
                            flush=True,
                        )
                        colors.append(color_choose)
                    erase()
                    add_colors(colors)

        if anime_list and k == "r":
            print(pprint_anime(anime_list, index, remove=True))
            print(pprint_actions(mode="confirm"))
            r_k = direct_input(choices=("y", "b"))
            if r_k == "y":
                remove_anime(index)
                index = 0
            erase(len(anime_list) + 2)

        if k == "a":
            q_index = 0
            q_k = "start"
            # anime search
            query = input(paint("Anime name", style=Style.BOLD) + ": ")
            erase()
            query_list = search_anime(query)
            if not query_list:
                print(f"No anime found with {paint(query,Color.BLUE)}!")
                print(pprint_actions(mode="back"))
                q_k = direct_input(choices=("b",))
                erase(3)
            while q_k not in ("c", "b"):
                print(pprint_query(query_list, q_index))
                print(pprint_actions(mode="add"))
                q_k = direct_input()
                erase(len(query_list) + 2)
                if q_k in ("w", "s"):
                    if q_k == "w" and q_index:
                        q_index -= 1
                    if q_k == "s" and q_index < len(query_list) - 1:
                        q_index += 1
            # new anime
            if q_k == "c":
                base = paint("Season", style=Style.BOLD) + ": "
                season = strict_input(
                    base,
                    f"{paint('This is not a season!',Color.RED)} {base}",
                    regex=r"\d{1,2}$",
                    flush=True,
                )
                base = paint("Folder name", style=Style.BOLD) + ": "
                name = strict_input(
                    base,
                    f"{paint('Folder name must be unique!', Color.RED)} {base}",
                    check=is_folder_unique,
                    flush=True,
                )
                base = paint("Mode [full|new]", style=Style.BOLD) + ": "
                mode = strict_input(
                    base,
                    f"{paint('Mode must be full or new!', Color.RED)} {base}",
                    choices=("full", "new"),
                    flush=True,
                )
                print(recap_new_anime(*query_list[q_index], season, name, mode))
                print(pprint_actions(mode="confirm"))
                c_k = direct_input(choices=("y", "n"))
                if c_k == "y":
                    add_anime(*query_list[q_index], season, name, mode)
                erase(7)
                index = 0
