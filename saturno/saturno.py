from argparse import ArgumentParser
from os import mkdir, path, walk
from re import search
from subprocess import PIPE, STDOUT, Popen

from colorifix.colorifix import Color, Style, paint
from halo import Halo
from pymortafix.utils import multisub
from requests import get
from saturno.anime import get_download_link, get_episodes_link
from saturno.manage import get_config, manage

CONFIG = get_config()
SPINNER = Halo()


def last_episodes_downloaded(folder_name):
    tree = list(walk(path.join(CONFIG.get("path"), folder_name)))
    if not tree:
        return []
    _, _, files = tree[0]
    return [
        int(se_ep.group(1)) for file in files if (se_ep := search(r"_Ep(\d+)", file))
    ]


def sanitize_name(name):
    return multisub({":": "", " ": "_"}, name)


def download_mp4(url, name, ep, folder):
    basepath = path.join(CONFIG.get("path"), folder)
    if not path.exists(basepath):
        mkdir(basepath)
    filename = path.join(basepath, f"{sanitize_name(name)}_Ep{ep}.mp4")
    chunk_size = 8192
    with get(url, stream=True) as r:
        r.raise_for_status()
        size = int(r.headers.get("Content-Length"))
        with open(filename, "wb") as f:
            downloaded = 0
            for chunk in r.iter_content(chunk_size=chunk_size):
                downloaded += chunk_size
                SPINNER.start(
                    f"Downloading {paint(name,Color.BLUE)} "
                    f"ep {paint(ep,Color.MAGENTA)} "
                    f"[{paint(f'{downloaded/size*100:.1f}',style=Style.BOLD)}%]"
                )
                f.write(chunk)
        SPINNER.succeed(
            f"Downloaded {paint(name,Color.BLUE)} ep {paint(ep,Color.MAGENTA)}"
        )
    return filename


def download_m3u8(url, name, ep, folder):
    basepath = path.join(CONFIG.get("path"), folder)
    if not path.exists(basepath):
        mkdir(basepath)
    filename = path.join(basepath, f"{sanitize_name(name)}_Ep{ep}.mp4")
    popen = Popen(
        f"ffmpeg -y -i {url} '{filename}'",
        shell=True,
        stdout=PIPE,
        stderr=STDOUT,
    )
    size = 0
    while True:
        next_line = popen.stdout.readline()
        line = next_line.rstrip().decode("utf8")
        size = (m := search(r"size=\s*(\d+)[a-zA-Z]{2}", line)) and m.group(1) or size
        SPINNER.start(
            f"Downloading {paint(name,Color.BLUE)} "
            f"ep {paint(ep,Color.MAGENTA)} "
            f"[{paint(f'{int(size)/1024:.1f}',style=Style.BOLD)} MB]"
        )
        if line == "" and popen.poll() is not None:
            break
    return filename


def download():
    anime_list = [list(anime.values()) for anime in CONFIG.get("anime")]
    for name, url, folder, mode in anime_list:
        downloaded_eps = last_episodes_downloaded(folder)
        links, eps_available = get_episodes_link(url)
        if mode == "full":
            eps_to_download = [ep for ep in eps_available if ep not in downloaded_eps]
        else:
            last_ep_downloaded = 0 if not downloaded_eps else max(downloaded_eps)
            eps_to_download = [ep for ep in eps_available if ep > last_ep_downloaded]
        for ep in eps_to_download:
            download_link = get_download_link(links[ep - 1])
            if search("m3u8", download_link):
                download_m3u8(download_link, name, ep, folder)
            if search("mp4", download_link):
                download_mp4(download_link, name, ep, folder)


def argparsing():
    parser = ArgumentParser(
        prog="Saturno",
        description="We are weebs.",
        usage=("saturno action:{manage,run}"),
    )
    parser.add_argument(
        "action",
        type=str,
        nargs=1,
        help="action to do",
        choices=("manage", "run"),
    )
    return parser.parse_args()


def main():
    args = argparsing()
    if args.action[0] == "manage":
        manage()
    if args.action[0] == "run":
        download()


if __name__ == "__main__":
    main()
