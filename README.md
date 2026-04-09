## Run application
1. Activate virtual environment by running the following command in terminal from project folder: <br>
. .venv/bin/activate

2. Next, run the following command: <br>
flask --app vgle run --debug

3. Visit website:
http://127.0.0.1:5000/[file] 

## Starter code from flask.com tutorial
https://flask.palletsprojects.com/en/stable/tutorial/ 

## Changing CSS
To see changes, refresh browser page; if changes do not show, clear browser cache

## Testing
Run pytest command in terminal. To see test code coverage, run: <br>
coverage run -m pytest <br>
coverage report

# Initializing Database (running schema script)
Run flask --app vgle init-db