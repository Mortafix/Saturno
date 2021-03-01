from re import search

from bs4 import BeautifulSoup as bs
from requests import get

SEARCH_URL = "https://www.animesaturn.it/animelist?search="


def search_anime(query):
    soup = bs(get(f"{SEARCH_URL}{query}").text, "html.parser")
    return [
        (group.find("h3").text[1:-1], group.find("a").get("href"))
        for group in soup.findAll("ul", {"class": "list-group"})
    ]


def get_episodes_link(anime_link):
    soup = bs(get(anime_link).text, "html.parser")
    a_refs = soup.find("div", {"class": "tab-content"}).findAll("a")
    links = [link.get("href") for link in a_refs]
    episodes = [int(search(r"ep-(\d+)", link.get("href")).group(1)) for link in a_refs]
    return links, episodes


def get_download_link(episode_link):
    soup = bs(get(episode_link).text, "html.parser")
    ep_page = soup.find("div", {"class": "card-body"}).find("a").get("href")
    ep_soup = bs(get(ep_page).text, "html.parser")
    link = search(r"\"(.*\.(m3u8|mp4))\"", str(ep_soup))
    return ep_page, (link.group(1) or (s := ep_soup.find("source")) and s.get("src"))
