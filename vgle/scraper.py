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
               limit for crawler
    5/2/2026 - add wikis to crawl list, catch errors, crawl only specified hosts, FIX POLITENESS BUG
               implement front and back queue for more politeness (much slower :( )
    5/3/2026 - account for near duplicates
    5/14/2026 - delete unused code that was commented out
'''

from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit
import urllib.robotparser

import certifi
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from vgle import create_app
from vgle.db import init_db

import threading
import time
import sqlite3
import warnings

import sys

min_access_time = 5 # politeness for hosts
start_urls = ["https://powerwashsimulator.wiki.gg", "https://bendy.wiki.gg", "https://nookipedia.com", "https://dredge.wiki.gg", 
              "https://undertale.wiki", "https://eldenring.wiki.gg", "https://minecraft.wiki", "https://eurogamer.net",
              "https://terraria.wiki.gg", "https://stardewvalleywiki.com", "https://howlongtobeat.com", "https://steamcommunity.com",
              "https://ign.com",  "https://mapgenie.io", "https://vg247.com",
              "https://rockpapershotgun.com", "https://maxroll.gg",  "https://planetpokemon.com", "https://pushsquare.com", "https://nintendo.com",
              "https://stardewvalley.net", "https://thegamer.com", "https://store.steampowered.com"] 
keywords = [ "game", "gaming", "multiplayer", "singleplayer", "rpg", "fps", "platformer"] # partial word matching for relevant pages
frontqueue = {}
backqueue = {}
for url in start_urls:
    frontqueue[url] = [url]
    backqueue[url] = time.time() # track last access time for each host to enforce politeness
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
    netloc = parsed.netloc.lower()

    if netloc.startswith("www."):
        netloc = netloc[4:]
    return f"{parsed.scheme}://{netloc}"

def crawl(hosts, depth_limit=1000):
    try:
        db = sqlite3.connect("instance/vsgl.sqlite", check_same_thread=False, timeout=10) # connect to database
        db_lock = threading.Lock()
        depth = 0
        headers = {
                "User-Agent": "VGLE/1.0",
                "Accept": "text/html",
                "Accept-Language": "en-US,en;q=0.9",
        } # set user agent to identify our crawler (important for robots.txt)
        robots = {}
        frontier_len = 0
        for host in hosts:
            robots[host] = get_robots(host)
            frontier_len += len(frontqueue[host])

        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

        junk_pages = ["login", "signup", "register", "account", "profile", "settings", "privacy", "terms", "contact", "support",
                    "refund", "subscribe", "zip", "apk", "subscriber", "special:", "talk:", "playlist", "user:", "help", 
                    "wikipedia:", "#", "portal:", "join", "/my/", "ziffdavis", "github", "flathub", "jira", "File:", "#"] # pages we don't want to crawl

        while frontier_len > 0 and depth < depth_limit: # crawl until queue is empty or we hit the depth limit
            frontier_len = sum([len(frontqueue[host]) for host in hosts]) # calculate if queue is empty
            # check back queue access times
            host = None
            for url in hosts:
                if time.time() - backqueue[url] >= min_access_time and len(frontqueue[url]) > 0:
                    host = url 
                    break
                
            if host is None:
                time.sleep(2)
                continue
            
            url = frontqueue[host].pop(0) # get first url
            url = normalize_url(url) # normalize for duplicates
            if url in visited:
                print(f"{url} already visited")
                depth += 1
                continue
            with db_lock:
                visited.add(url) # mark url
            base_url = get_base_url(url)
            if base_url != host: # only crawl the specific host
                print(f"Base url {base_url} != host {host}")
                continue
        
            robot = robots[host]

            if not (url.startswith("http://") or url.startswith("https://")): # check for valid url
                print(f"{url} not a valid url")
                continue

            if not robot.can_fetch("*", url): # robots.txt: can we look at this page?
                print(f"Robots disallowed for {url}")
                continue 

            if any(junk in url.lower() for junk in junk_pages): # get rid of junk pages (like login)
                print(f"{url} junky page")
                continue

            try:
                page = requests.get(url, timeout=10, headers=headers, verify=certifi.where()) # get content of webpage
                page.encoding = page.apparent_encoding # set encoding to apparent encoding to avoid issues with non-utf-8 pages
                backqueue[host] = time.time() # store last access time
            except Exception as e:
                print(f"Page request exception for {url}")
                continue

            if page.status_code != 200: # check for successful response
                print(f"Page request unsuccessful for {url}")
                continue

            soup = BeautifulSoup(page.content, "html.parser") # html parser
            
            title = soup.title
            if title:
                title = title.string # get title
            else:
                title = url
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
                    frontqueue[host].append(norm_ref)
                outlink_urls.append(norm_ref)
            outlink_urls = list(set(outlink_urls))  # deduplicate outlinks for this page
            #get content
            boo_tags = ["script", "style", "footer", "header", "nav"]
            for tag in soup(boo_tags):  # remove unwanted html tags
                tag.decompose()
            
            content = soup.get_text(separator=" ").strip()

            try:
                # insert into database
                db.execute(
                    'INSERT OR IGNORE INTO docs (url, title, author, content)' # ignore ignores duplicates
                    ' VALUES (?, ?, ?, ?)',
                    (url, title, author, content)
                )

                # put outlinks into links table for HITS computation
                src_row = db.execute(
                    'SELECT docid FROM docs WHERE url = ?', (url,)
                ).fetchone()
                if src_row:
                    src_docid = src_row[0]
                    with db_lock:
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
            except Exception as e:
                print("Database error, continuing crawl")
    except Exception as e:
        print(f"Error in crawl, skipping remaining host queue {e}")
    print(f"Finished crawling {hosts}")

def multi_crawl(depth_limit=1000):
    # code from docs.python.org threading.html tutorial
    # crawl with multiple threads
    thread_count = len(start_urls)//3 + 1
    threads = []
    for i in range(thread_count):
        t = threading.Thread(target=crawl, args=(start_urls[i*3:i*3+3], depth_limit))
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
        init_db() 
        multi_crawl(depth_limit=int(sys.argv[1]) if len(sys.argv) > 1 else float('inf')) # run crawl, get depth limit from command line
        print("Crawling complete")
        # run inverted index and HITS after crawling is done
        from vgle.inverted_index import create_index
        create_index()
        print("Inverted index built")
        from vgle.hits import compute_hits
        compute_hits()
        print("HITS computed")