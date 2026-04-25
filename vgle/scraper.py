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
'''

from urllib.parse import urljoin, urlparse
import urllib.robotparser

import requests
from bs4 import BeautifulSoup

from vgle.db import get_db
from vgle import create_app

import threading
import time
import sqlite3

min_access_time = 0.1 # politeness for hosts
start_urls = ["https://www.ign.com/", "https://en.wikipedia.org/wiki/Lists_of_video_games"]

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

def crawl(host):
    db = sqlite3.connect("instance/vsgl.sqlite", check_same_thread=False, timeout=10) # connect to database
    headers = {
        "User-Agent": "VGLE/1.0"
    } # set user agent to identify our crawler (important for robots.txt)
    queue = [host]
    visited = set()
    robots = get_robots(host)
    
    while len(queue) > 0: # crawl until queue is empty
        url = queue.pop(0) # get first url
        visited.add(url) # mark url

        page = requests.get(url, headers=headers) # get content of webpage

        if page.status_code != 200: # check for successful response
            continue

        if not robots.can_fetch("*", url): # robots.txt: can we look at this page?
            print("hello")
            continue 

        if not (url.startswith("http://") or url.startswith("https://")): # check for valid url
            continue

        soup = BeautifulSoup(page.content, "html.parser") # html parser

        # if we're not allowed to index this page, skip it
        # robots_tag = soup.find("meta", attrs={"name": "robots"})
        # if robots_tag:
        #     print("hi")
        #     if "noindex" in robots_tag.get("content", "").lower():
        #         continue

        # get all urls from page
        for a in soup.find_all("a", href=True): # find a ref (linked html object)
            ref_url = urljoin(url, a["href"])
            if ref_url not in visited: # duplicate url elimination
                queue.append(ref_url)

        # get metadata
        title = soup.title.string # get title
        author = "placeholder"

        #get content
        boo_tags = ["script", "style", "footer", "header", "nav"]
        for tag in soup(boo_tags):  # remove unwanted html tags
            tag.decompose()
        
        content = soup.get_text(separator=" ").strip()

        # insert into database
        db.execute(
            'INSERT OR IGNORE INTO docs (url, title, author, content)' # ignore ignores duplicates
            ' VALUES (?, ?, ?, ?)',
            (url, title, author, content)
        )

        db.commit()

        time.sleep(min_access_time) # politeness for each host

def multi_crawl():
    # "https://store.steampowered.com", 
    #     # don't work: "https://www.igdb.com/"] #"https://www.fandom.com/"] "https://www.mobygames.com/"

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

    
        
    # ALSO NEED TO ACCOUNT FOR JS

    #print(page.text)



    # results = soup.find(id="ResultsContainer")
# python_jobs = results.find_all(
#     "h2", string=lambda text: "python" in text.lower()
# )
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        multi_crawl()
# python_job_cards = [
#     h2_element.parent.parent.parent for h2_element in python_jobs
# ]

# for job_card in python_job_cards:
#     title_element = job_card.find("h2", class_="title")
#     company_element = job_card.find("h3", class_="company")
#     location_element = job_card.find("p", class_="location")
#     print(title_element.text.strip())
#     print(company_element.text.strip())
#     print(location_element.text.strip())
#     link_url = job_card.find_all("a")[1]["href"]
#     print(f"Apply here: {link_url}\n")