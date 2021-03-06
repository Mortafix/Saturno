from datetime import datetime
from json import dump, load
from os import path, walk
from re import search

from colorifix.colorifix import Background, Color, Style, erase, paint
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


def add_youtube_dl(ytd_path):
    config = get_config()
    config["youtube-dl-path"] = ytd_path
    save_config(config)


# --- Pretty Print


def pprint_row(anime_name, season, mode, index=False, remove=False):
    if index and remove:
        return paint(f"[#] {anime_name} [{mode}]", background=Background.RED)
    if index and not remove:
        ret_str = paint("[>] ", Color.GREEN) + paint(anime_name, Color.GREEN)
    else:
        ret_str = "[ ] " + paint(anime_name)
    return (
        ret_str + paint(f" (s{season}) ", Color.CYAN) + paint(f"[{mode}]", Color.BLUE)
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
        actions = {"y": "confirm", "n": "back"}
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
            "y": "youtube-dl",
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
            f"[{paint(key,style=Style.BOLD)}]:{paint(action,Color.MAGENTA)}"
            for key, action in actions.items()
        )
    )


def pprint_query(query_list, selected):
    return "\n".join(
        paint(f"[>] {name}", Color.GREEN) if selected == i else f"[ ] {name}"
        for i, (name, _) in enumerate(query_list)
    )


def pprint_settings():
    config = get_config()
    labels = ("Current path", "Backup", "Telegram", "Youtube-dl")
    path_str = paint(config.get("path"), Color.BLUE)
    backup = get_last_backup()
    backup_str = paint(backup, Color.BLUE)
    telegram_str = (
        (
            paint(config.get("telegram-bot-token"), Color.BLUE)
            + paint(":", style=Style.BOLD)
            + paint(config.get("telegram-chat-id"), Color.BLUE)
        )
        if config.get("telegram-bot-token")
        else ""
    )
    youtube_dl_str = paint(config.get("youtube-dl-path"), Color.BLUE)
    values = (path_str, backup_str, telegram_str, youtube_dl_str)
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
        f"Name: {paint(name,Color.BLUE)}\n"
        f"Link: {paint(url,Color.BLUE)}\n"
        f"Stagione {paint(season,Color.BLUE)}\n"
        f"Folder: {paint(folder,Color.BLUE)}\n"
        f"Mode: {paint(mode,Color.BLUE)}"
    )


# --- Input


def is_bot_valid(token):
    try:
        Bot(token)
        return True
    except InvalidToken:
        return False


def is_yt_download_valid(ytd_path):
    return search(r"youtube-dl$", ytd_path) and path.exists(ytd_path)


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
                e_k = direct_input(choices=("u", "r", "p", "t", "y", "b"))
                erase(6)
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
                elif e_k == "y":
                    base = paint("Youtube-dl path", style=Style.BOLD) + ": "
                    youtube_dl_path = strict_input(
                        base,
                        wrong_text=paint(
                            "Wrong path, MUST include 'youtube-dl'! ", Color.RED
                        )
                        + base,
                        check=is_yt_download_valid,
                        flush=True,
                    )
                    add_youtube_dl(youtube_dl_path)

        if anime_list and k == "r":
            print(pprint_anime(anime_list, index, remove=True))
            print(pprint_actions(mode="confirm"))
            r_k = direct_input(choices=("y", "n"))
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
