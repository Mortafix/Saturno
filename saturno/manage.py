from json import dump, load
from os import path

from colorifix.colorifix import Background, Color, Style, erase, paint
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


def add_anime(name, link, folder, mode):
    new = {"name": name, "site": link, "folder": folder, "mode": mode}
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


# --- Menu


def pprint_row(anime_name, mode, index=False, remove=False):
    if index and remove:
        return paint(f"[#] {anime_name} [{mode}]", background=Background.RED)
    if index and not remove:
        return (
            paint("[>] ", Color.GREEN)
            + paint(anime_name, Color.GREEN)
            + paint(f" [{mode}]", Color.BLUE)
        )
    return "[ ] " + paint(anime_name) + paint(f" [{mode}]", Color.BLUE)


def pprint_anime(anime_list, index, remove=None):
    if not anime_list:
        return "No anime added.."
    return "\n".join(
        [
            pprint_row(name, mode, index == i, remove=remove)
            for i, (name, _, _, mode) in enumerate(anime_list)
        ]
    )


def pprint_actions(mode=None):
    if mode == "confirm":
        actions = {"y": "confirm", "n": "back"}
    elif mode == "add":
        actions = {"ws": "move", "c": "confirm", "b": "back"}
    elif mode == "back":
        actions = {"b": "back"}
    elif mode == "path":
        actions = {"e": "edit", "b": "back"}
    else:
        actions = {"ws": "move", "a": "add", "r": "remove", "p": "path", "q": "quit"}
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


def recap_new_anime(name, url, folder, mode):
    return (
        f"Name: {paint(name,Color.BLUE)}\n"
        f"Link: {paint(url,Color.BLUE)}\n"
        f"Folder: {paint(folder,Color.BLUE)}\n"
        f"Mode: {paint(mode,Color.BLUE)}"
    )


def manage():
    inkey = _Getch()
    index = 0
    k = "start"
    while k != "q":
        anime_list = [list(anime.values()) for anime in get_config().get("anime")]
        print(pprint_anime(anime_list, index))
        print(pprint_actions())
        k = inkey()
        erase(len(anime_list or [0]) + 2)
        if k in ("w", "s"):
            if k == "w" and index:
                index -= 1
            if k == "s" and index < len(anime_list) - 1:
                index += 1
        if k == "p":
            print(f"Current path: {paint(get_config().get('path'),Color.BLUE)}")
            print(pprint_actions(mode="path"))
            p_k = inkey()
            while p_k not in ("b", "e"):
                p_k = inkey()
            erase(3)
            if p_k == "e":
                new_path = input(paint("Path", style=Style.BOLD) + ": ")
                while not path.exists(new_path):
                    erase()
                    new_path = input(
                        paint("Wrong path! ", Color.RED)
                        + paint("Path", style=Style.BOLD)
                        + ": "
                    )
                add_new_path(new_path)
                erase(1)
        if anime_list and k == "r":
            print(pprint_anime(anime_list, index, remove=True))
            print(pprint_actions(mode="confirm"))
            while k not in ("y", "n"):
                k = inkey()
            if k == "y":
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
                q_k = inkey()
                while q_k != "b":
                    q_k = inkey()
                erase(3)
            while q_k not in ("c", "b"):
                print(pprint_query(query_list, q_index))
                print(pprint_actions(mode="add"))
                q_k = inkey()
                erase(len(query_list) + 2)
                if q_k in ("w", "s"):
                    if q_k == "w" and q_index:
                        q_index -= 1
                    if q_k == "s" and q_index < len(query_list) - 1:
                        q_index += 1
            # new anime
            if q_k == "c":
                # name
                name = input(paint("Folder name", style=Style.BOLD) + ": ")
                while not name or not is_folder_unique(name):
                    erase()
                    name = input(
                        paint("Folder name must be unique! ", Color.RED)
                        + paint("Folder name", style=Style.BOLD)
                        + ": "
                    )
                erase()
                # mode
                mode = input(paint("Mode [full|new]", style=Style.BOLD) + ": ")
                while mode not in ("full", "new"):
                    erase()
                    mode = input(
                        paint("Mode must be full or new! ", Color.RED)
                        + paint("Mode [full|new]", style=Style.BOLD)
                        + ": "
                    )
                erase()
                # confirm
                print(recap_new_anime(*query_list[q_index], name, mode))
                print(pprint_actions(mode="confirm"))
                c_k = "start"
                while c_k not in ("y", "n"):
                    c_k = inkey()
                if c_k == "y":
                    add_anime(*query_list[q_index], name, mode)
                erase(6)
                index = 0
