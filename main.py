import csv
from os.path import exists
from pathlib import Path

from slugify import slugify
import requests
from bs4 import BeautifulSoup as bs


OUTPUT_PATH = Path('./output')
ROOT_ARCHIVE_URL = "https://www.thisamericanlife.org"
ARCHIVE_URL_TMPL = ROOT_ARCHIVE_URL + "/archive?page={}"


def scrape_podcast(id_, title, url):
    r = requests.get(url)
    soup = bs(r.text, features="html.parser")
    download_url = soup.find(class_="download").find("a")["href"]
    r = requests.get(download_url, stream=True)
    slug = slugify(f"{id_} {title}")
    filepath = OUTPUT_PATH / f"{slug}.mp3"
    if exists(filepath):
        return

    with open(filepath, "wb") as f:
        for chunk in r.iter_content(chunk_size=512 * 1024):
            if chunk:
                f.write(chunk)


def scrape_page(page=0):
    r = requests.get(ARCHIVE_URL_TMPL.format(page))
    soup = bs(r.text, features="html.parser")
    return [{
        'id_': x["href"].split("/")[1],
        'title': x.text,
        'url': ROOT_ARCHIVE_URL + x["href"],
        } for x in soup.select(".node-episode h2 a")]


if __name__ == "__main__":
    podcasts = []
    page = 0
    while True:
        podcast_page = scrape_page(page)
        podcasts += podcast_page
        with open(OUTPUT_PATH / 'podcasts.csv', 'w') as f:
            w = csv.DictWriter(f, fieldnames=podcasts[0].keys())
            w.writeheader()
            w.writerows(podcasts)
        if len(podcast_page) < 20:
            break
        page += 1

    for podcast in podcasts:
        scrape_podcast(**podcast)
