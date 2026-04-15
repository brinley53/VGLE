'''
Name: interface.py
Description: query interface home page
Authors: Brinley Hull & Anakha Krishna
Other sources: Flask tutorial flask.com
Created: 3/22/2026
Last modified: 
    4/1/2026 - Query writes to file
    4/9/2026 - Show docs from database
    4/15/2026 - Make new inverted index with every post (temp)
'''

from flask import (
    Blueprint, app, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from vgle.auth import login_required
from vgle.db import get_db

bp = Blueprint('interface', __name__)

@bp.route('/', methods=('GET', 'POST')) # home page
def index():
    if request.method == 'POST': # if search query is submitted
        query = request.form['search'] # get search query from form
        query = query.split(" ") # split into list of words
        # preprocessing
        stopwords = []
        processed_query = []

        for term in query:
            term = term.lower() # convert to lowercase
            term = ''.join(ch for ch in term if ch.isalnum()) # remove punctuation (only keep characters that are alpha numeric)
            if term in stopwords: # skip stopwords
                continue

            processed_query.append(term)
    
        # save query to file
        with open('vgle/query.txt', 'w') as query_file: # w erases previous results
            query_file.write(" ".join(processed_query))

    # access database
    db = get_db()
    docs = db.execute(
        'SELECT *'
        ' FROM docs d' # will need to update this for ranking,idf
    ).fetchall()

    return render_template('interface/index.html', docs=docs)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO docs (title, content, author, url)'
                ' VALUES (?, ?, ?, ?)',
                (title, content, g.user['id'], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            )
            db.commit()
            from . import inverted_index
            inverted_index.create_index()
            return redirect(url_for('interface.index'))

    return render_template('interface/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('interface.index'))

    return render_template('interface/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('interface.index'))