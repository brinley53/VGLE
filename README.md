## Run application
1. Activate virtual environment by running the following command in terminal from project folder: ```shell
. .venv/bin/activate
```

2. Next, run the following command: 
```shell
flask --app vgle run --debug
```

3. Visit website:
http://127.0.0.1:5000

## Starter code from flask.com tutorial
https://flask.palletsprojects.com/en/stable/tutorial/ 

## Changing CSS
To see changes, refresh browser page; if changes do not show, clear browser cache

## Initializing Database (running schema script)
```shell
flask --app vgle init-db
```

## Running Crawler
If running the complete crawler or smaller crawl, it will automatically call index and hits.
```shell
python vgle/scraper.py [max docs per thread for shorter crawl, optional]
python vgle/inverted_index.py
python vgle/hits.py
```