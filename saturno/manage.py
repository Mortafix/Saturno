from datetime import datetime
from json import dump, load
from os import path, walk
from re import search

from colorifix.colorifix import Background, Color, Style, erase, paint
from pymortafix.utils import strict_input
from saturno.anime import search_anime
from saturno.getchar import _Getch

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
        actions = {"u": "backup", "r": "restore", "p": "path", "b": "back"}
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
    path = f"Current path: {paint(get_config().get('path'),Color.BLUE)}"
    backup = get_last_backup()
    backup_str = f"Backup: {paint(backup,Color.BLUE)}"
    return f"{path}\n{backup_str}"


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


def get_input(choices=None):
    inkey = _Getch()
    k = inkey()
    while choices and k not in choices:
        k = inkey()
    return k


# --- Manage


def manage():
    index = 0
    k = "start"
    while k != "q":
        anime_list = [list(anime.values()) for anime in get_config().get("anime")]
        print(pprint_anime(anime_list, index))
        print(pprint_actions())
        k = get_input(choices=("w", "s", "e", "a", "r", "q"))
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
                e_k = get_input(choices=("u", "r", "p", "b"))
                erase(4)
                if e_k == "p":
                    new_path = strict_input(
                        paint("Path", style=Style.BOLD) + ": ",
                        wrong_text=paint("Wrong path! ", Color.RED)
                        + paint("Path", style=Style.BOLD)
                        + ": ",
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

        if anime_list and k == "r":
            print(pprint_anime(anime_list, index, remove=True))
            print(pprint_actions(mode="confirm"))
            r_k = get_input(choices=("y", "n"))
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
                q_k = get_input(choices=("b",))
                erase(3)
            while q_k not in ("c", "b"):
                print(pprint_query(query_list, q_index))
                print(pprint_actions(mode="add"))
                q_k = get_input()
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
                c_k = get_input(choices=("y", "n"))
                if c_k == "y":
                    add_anime(*query_list[q_index], season, name, mode)
                erase(7)
                index = 0
