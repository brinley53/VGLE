'''
Name: scraper.py
Description: basic web scraper
Authors: Brinley Hull & Anakha Krishna
Other sources: Real Python beautiful soup tutorial (realpython.com), GeeksForGeeks tutorials
Created: 3/22/2026
Last modified: 
    4/13/2026 - add url parsing functionality
'''

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URL = "https://www.geeksforgeeks.org/"
page = requests.get(URL) # get content of webpage

# check robots.txt 
# skip all pages if disallowed
# get all urls from page 
# add document content to database 

print(page.text)

# get all urls from page
links = set() 
soup = BeautifulSoup(page.content, "html.parser")
for a in soup.find_all("a", href=True):
    ref_url = urljoin(URL, a["href"])
    links.add(ref_url)

print(links)
# results = soup.find(id="ResultsContainer")

# python_jobs = results.find_all(
#     "h2", string=lambda text: "python" in text.lower()
# )

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