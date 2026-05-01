'''
Name: scraper.py
Description: basic web scraper
Authors: Brinley Hull & Anakha Krishna
Other sources: Real Python beautiful soup tutorial (realpython.com), GeeksForGeeks tutorials, docs.python.org threading tutorial
Created: 3/22/2026
Last modified: 
    4/13/2026 - add url parsing functionality
    4/17/2026 - basic web crawling with robots.txt
    4/24/2026 - politeness, distribute crawlers, robots efficiency
    4/26/2026 - filter some junk pages, dynamic robots for pages outside host
    4/28/2026 - real author, dedup
    5/1/2026 - populate links table for HITS
'''

from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit
import urllib.robotparser

import certifi
import requests
from bs4 import BeautifulSoup

from vgle.db import get_db
from vgle import create_app

import threading
import time
import sqlite3

min_access_time = 0.1 # politeness for hosts
    #  don't work: "https://www.igdb.com/"] #"https://www.fandom.com/"] "https://www.mobygames.com/"
start_urls = [ "https://howlongtobeat.com", "https://steamcommunity.com", "https://www.rockpapershotgun.com", "https://store.steampowered.com", 
              "https://www.ign.com",  "https://mapgenie.io", "https://maxroll.gg", "https://www.vg247.com", 
              "https://eurogamer.net", "https://planetpokemon.com", "https://www.pushsquare.com"] # "https://en.wikipedia.org/wiki/Lists_of_video_games" 
keywords = [ "game", "gaming", "play", "level", "character", "quest", "multiplayer", "singleplayer", 
            "open world", "rpg", "fps", "adventure", "puzzle", "platformer"] # partial word matching for relevant pages

visited = set()

# get robots.txt
def get_robots(url):
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}" # get base url
    robots_url = base_url + "/robots.txt" # robots.txt url

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    text = requests.get(robots_url).text.splitlines() # get robots.txt content
    rp.parse(text)

    return rp

def normalize_url(url):
    parts = urlsplit(url)

    # remove trailing slash
    path = parts.path.rstrip("/")

    # rebuild clean URL
    return urlunsplit((
        parts.scheme,
        parts.netloc,
        path,
        "",  # remove query if you want stricter dedup
        ""
    ))

def get_base_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def crawl(host):
    db = sqlite3.connect("instance/vsgl.sqlite", check_same_thread=False, timeout=10) # connect to database
    db_lock = threading.Lock()
    headers = {
        "User-Agent": "VGLE/1.0"
    } # set user agent to identify our crawler (important for robots.txt)
    queue = [host]
    robots = {}
    robots[host] = get_robots(host)

    junk_pages = ["login", "signup", "register", "account", "profile", "settings", "privacy", "terms", "contact", "support",
                  "refund", "subscribe", "zip", "apk", "id", "subscriber", "special:", "talk:", "playlist", "user:", "help", 
                  "wikipedia:", "about", "#", "?", "portal:", "%", "join", "my", "ziffdavis", "github", "flathub"] # pages we don't want to crawl
    
    while len(queue) > 0: # crawl until queue is empty
        url = queue.pop(0) # get first url
        with db_lock:
            if url in visited:
                continue
            visited.add(url) # mark url
        base_url = get_base_url(url)
        # if base_url != host: # only crawl the specific host
        #     continue

        # get relevant robots.txt
        if base_url not in robots:
            try:
                robots[base_url] = get_robots(base_url)
            except Exception as e:
                continue 
    
        robot = robots[base_url]

        try:
            page = requests.get(url, timeout=5, headers=headers, verify=certifi.where()) # get content of webpage
        except Exception as e:
            continue

        if page.status_code != 200: # check for successful response
            continue

        if not robot.can_fetch("*", url): # robots.txt: can we look at this page?
            continue 

        if not (url.startswith("http://") or url.startswith("https://")): # check for valid url
            continue

        if any(junk in url.lower() for junk in junk_pages): # get rid of junk pages (like login)
            continue

        soup = BeautifulSoup(page.content, "html.parser") # html parser

        # partial word matching to find relevant pages
        text = soup.get_text().lower()
        if not any(word in text for word in keywords):
            continue

        # get metadata
        title = soup.title
        if title:
            title = title.string # get title
        else:
            continue
        author = soup.find("meta", property="og:site_name") # get author meta tag
        if author:
            author = author["content"] # get author content
        else:
            author = title

        # get all urls from page
        outlink_urls = []
        for a in soup.find_all("a", href=True): # find a ref (linked html object)
            ref_url = urljoin(url, a["href"])
            norm_ref = normalize_url(ref_url)
            if norm_ref not in visited: # duplicate url elimination
                queue.append(ref_url)
            outlink_urls.append(norm_ref)
        outlink_urls = list(set(outlink_urls))  # deduplicate outlinks for this page

        #get content
        boo_tags = ["script", "style", "footer", "header", "nav"]
        for tag in soup(boo_tags):  # remove unwanted html tags
            tag.decompose()
        
        content = soup.get_text(separator=" ").strip()

        # insert into database
        with db_lock: # so multiple threads don't write to database at the same time
            db.execute(
                'INSERT OR IGNORE INTO docs (url, title, author, content)' # ignore ignores duplicates
                ' VALUES (?, ?, ?, ?)',
                (url, title, author, content)
            )

        db.commit()

        # put outlinks into links table for HITS computation
        with db_lock:
            src_row = db.execute(
                'SELECT docid FROM docs WHERE url = ?', (url,)
            ).fetchone()
            if src_row:
                src_docid = src_row[0]
                for dst_url in outlink_urls:
                    dst_row = db.execute(
                        'SELECT docid FROM docs WHERE url = ?', (dst_url,)
                    ).fetchone()
                    if dst_row and dst_row[0] != src_docid:  # skip self-links
                        db.execute(
                            'INSERT OR IGNORE INTO links (src_docid, dst_docid)'
                            ' VALUES (?, ?)',
                            (src_docid, dst_row[0])
                        )
                db.commit()

        time.sleep(min_access_time) # politeness for each host
    print(f"Finished crawling {host}")

def multi_crawl():
    # code from docs.python.org threading.html tutorial
    # crawl with multiple threads
    threads = []
    for url in start_urls:
        t = threading.Thread(target=crawl, args=(url,))
        threads.append(t)

    # start each thread
    for t in threads:
        t.start()

    # wait for threads to finish
    for t in threads:
        t.join()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        multi_crawl()