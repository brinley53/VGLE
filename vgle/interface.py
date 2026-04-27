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
                Add unnormalized ranking based on tf x idf
    4/24/2026 - query normalization and retrieval based on cosine similarity
    4/26/2026 - Blank page with no query, delete tutorial pages
'''

import math

from flask import (
    Blueprint, app, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

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

        # deduplicate terms while preserving order so each term contributes idf once to query vector. query vector has 1 dim per unique term
        unique_query_terms = list(dict.fromkeys(processed_query))

        # save query to file
        with open('vgle/query.txt', 'w') as query_file: # w erases previous results
            query_file.write(" ".join(processed_query))

    # access database
    db = get_db()

    if request.method == 'POST' and processed_query:
        # compute query norm: sqrt(SUM(idf(t)^2)) for query terms found in the index
        query_norm = 0.0
        placeholders_qn = ', '.join(['?'] * len(unique_query_terms))
        idf_rows = db.execute(
            'SELECT idf FROM term_idf WHERE term IN (' + placeholders_qn + ')',
            unique_query_terms
        ).fetchall()
        for row in idf_rows:
            query_norm += row['idf'] * row['idf']
        query_norm = math.sqrt(query_norm)

        if query_norm == 0.0:
            # if no query terms found in index --> return unranked list (make this into no results later)
            docs = db.execute('SELECT * FROM docs d').fetchall()
        else:
            # cosine similarity: dot(q,d) / (|q| * |d|)
            # dot product = SUM(tf * idf^2) to rewards rare terms --> w(t,q)=idf(t) for query and w(t,d)=tf(t,d)*idf(t) for doc
            placeholders = ', '.join(['?'] * len(unique_query_terms))
            raw_docs = db.execute(
                'SELECT d.docid, d.url, d.author, d.title, d.content, d.doc_norm,'
                '       SUM(ii.tf * ti.idf * ti.idf) AS dot_product'
                ' FROM docs d'
                ' JOIN inverted_index ii ON d.docid = ii.docid'
                ' JOIN term_idf ti ON ii.term = ti.term'
                ' WHERE ii.term IN (' + placeholders + ')'
                ' AND d.doc_norm IS NOT NULL AND d.doc_norm > 0'
                ' GROUP BY d.docid, d.url, d.author, d.title, d.content, d.doc_norm'
                ' ORDER BY (dot_product / d.doc_norm) DESC',
                unique_query_terms
            ).fetchall()

            # divide by query_norm to get cosine similarity in [0, 1]
            # copy everything over to a dictionary and do calculations since we don't store anything about query in db
            docs = []
            for row in raw_docs:
                docs.append({
                    'docid': row['docid'],
                    'url': row['url'],
                    'author': row['author'],
                    'title': row['title'],
                    'content': row['content'],
                    'score': row['dot_product'] / (row['doc_norm'] * query_norm)
                })
    else:
        docs = []

    return render_template('interface/index.html', docs=docs)