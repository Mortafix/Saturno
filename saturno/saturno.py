from argparse import ArgumentParser
from datetime import datetime
from os import makedirs, path, walk
from re import search
from subprocess import PIPE, STDOUT, Popen
from time import sleep

from colorifix.colorifix import Color, paint
from emoji import emojize
from halo import Halo
from pymortafix.utils import multisub
from requests import get
from saturno.anime import get_download_link, get_episodes_link
from saturno.manage import get_config, manage
from telegram import Bot
from youtube_dl import YoutubeDL

CONFIG = get_config()
SPINNER = Halo()


def last_episodes_downloaded(folder_name, season):
    tree = list(walk(path.join(CONFIG.get("path"), folder_name, f"Stagione {season}")))
    if not tree:
        return []
    _, _, files = tree[0]
    return [
        int(se_ep.group(1)) for file in files if (se_ep := search(r"_s\d+e(\d+)", file))
    ]


def sanitize_name(name):
    return multisub({":": "", " ": "_"}, name)


def send_telegram_log(name, season, episode, success=True):
    config = get_config()
    bot_token = config.get("telegram-bot-token")
    chat_id = config.get("telegram-chat-id")
    if bot_token and chat_id:
        emoji = ":white_check_mark:" if success else ":no_entry:"
        title = "Download Succesfull" if success else "Download Failed"
        msg = (
            f"{emoji} *{title}* {emoji}\n\n"
            f":clapper: *{name}*\n"
            f":cyclone: Episode *{season}*×*{episode}*\n"
            f":calendar: {datetime.now():%d.%m.%Y}\n"
        )
        Bot(bot_token).send_message(
            chat_id, emojize(msg, use_aliases=True), parse_mode="Markdown"
        )


def download_video(url, name, filename):
    with YoutubeDL({"o": filename, "quiet": True, "no_warnings": True}) as ydl:
        ydl.download([url])


def download(action):
    anime_list = [list(anime.values()) for anime in CONFIG.get("anime")]
    for name, url, season, folder, mode in anime_list:
        downloaded_eps = last_episodes_downloaded(folder, season)
        links, eps_available = get_episodes_link(url)
        if mode == "full":
            eps_to_download = [ep for ep in eps_available if ep not in downloaded_eps]
        else:
            last_ep_downloaded = 0 if not downloaded_eps else max(downloaded_eps)
            eps_to_download = [ep for ep in eps_available if ep > last_ep_downloaded]
        for ep in eps_to_download:
            if action == "run":
                episode_link, download_link = get_download_link(links[ep - 1])
                basepath = path.join(CONFIG.get("path"), folder, f"Stagione {season}")
                if not path.exists(basepath):
                    makedirs(basepath)
                filename = path.join(
                    basepath, f"{sanitize_name(name)}_s{int(season):02d}e{ep:02d}.mp4"
                )
                SPINNER.start(
                    f"Downloading {paint(name,Color.BLUE)} "
                    f"{paint(f'{season}x{ep}',Color.MAGENTA)}"
                )
                try:
                    download_video(episode_link, name, filename)
                except Exception:
                    SPINNER.fail(
                        f"Fail to download {paint(name,Color.BLUE)} "
                        f"{paint(f'{season}x{ep}',Color.MAGENTA)}"
                    )
                    send_telegram_log(name, season, ep, success=False)
                    break
                SPINNER.succeed(
                    f"Downloaded {paint(name,Color.BLUE)} "
                    f"{paint(f'{season}x{ep}',Color.MAGENTA)}"
                )
                send_telegram_log(name, season, ep)
            elif action == "test":
                SPINNER.info(
                    f"Found {paint(name, Color.BLUE)} "
                    + paint(f"{season}x{ep}", Color.MAGENTA)
                )


def argparsing():
    parser = ArgumentParser(
        prog="Saturno",
        description="We are weebs.",
        usage=("saturno action:{manage, run, test}"),
    )
    parser.add_argument(
        "action",
        type=str,
        nargs=1,
        help="action to do",
        choices=("manage", "run", "test"),
    )
    return parser.parse_args()


def main():
    args = argparsing()
    if args.action[0] == "manage":
        manage()
    if args.action[0] in ("run", "test"):
        download(args.action[0])


if __name__ == "__main__":
    main()
