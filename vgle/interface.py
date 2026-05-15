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
    4/30/2026 - integrate stopwords
    5/1/2026 - factor in HITS for ranking
    5/2/2026 - restrict to top 200 results, keep query in search bar
               Retrieve the excerpt of text where the query terms are in the document
    5/3/2026 - increase query speed with extra sql filtering
    5/14/2026 - deleted unused code AND TERM PROXIMITY SCORING BABY
    5/15/2026 - fix cosine similiarity calculations
'''

import json
import math

from flask import (
    Blueprint, app, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from vgle.db import get_db
from vgle.inverted_index import STOPWORDS

from flask import current_app

# current limitation: only shows excerpt for the first thing it matches in query
def get_excerpt(content, query_terms, chars=150): # chars: how many characters that show on either side of the term
    content_lower = content.lower()
    best_pos = -1

    for term in query_terms:
        if not term:
            continue
        pos = content_lower.find(term)
        if pos != -1 and (best_pos == -1 or pos < best_pos):
            best_pos = pos

    # do a sliding window to find the terms
    if best_pos == -1:
        return content[:300]  # if no terms found, fallback to return first 300 chars of doc

    start = max(0, best_pos - chars)
    end = min(len(content), best_pos + chars)

    # move start forward to word boundary so no words get cut off
    if start > 0:
        space = content.find(' ', start)
        if space != -1 and space < best_pos:
            start = space + 1

    # move end back to word boundary
    if end < len(content):
        space = content.rfind(' ', start, end)
        if space != -1:
            end = space

    excerpt = content[start:end].strip()

    if start > 0:
        excerpt = '...' + excerpt
    if end < len(content):
        excerpt = excerpt + '...'

    return excerpt

bp = Blueprint('interface', __name__)

@bp.route('/', methods=('GET', 'POST')) # home page
def index():
    query_text = request.form.get('search', '')
    if request.method == 'POST': # if search query is submitted
        query = query_text.split(" ") # split into list of words
        # preprocessing
        processed_query = []

        for term in query:
            term = term.lower() # convert to lowercase
            term = ''.join(ch for ch in term if ch.isalnum()) # remove punctuation (only keep characters that are alpha numeric)
            if not term or term in STOPWORDS: # skip empty tokens and stopwords
                continue

            processed_query.append(term)

        # deduplicate terms while preserving order so each term contributes idf once to query vector. query vector has 1 dim per unique term
        unique_query_terms = list(dict.fromkeys(processed_query))

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
            docs = []  # no matching terms in index: return empty results
        else:
            # cosine similarity: dot(q,d) / (|q| * |d|)
            # dot product = SUM(tf * idf^2) to rewards rare terms --> w(t,q)=idf(t) for query and w(t,d)=tf(t,d)*idf(t) for doc
            placeholders = ', '.join(['?'] * len(unique_query_terms))
            raw_docs = db.execute(
                'SELECT d.docid, d.url, d.author, d.title, d.content, d.doc_norm,'
                '       d.authority_score, ii.positions, ii.term, ii.tf'
                #'       SUM(ii.tf * ti.idf * ti.idf) AS dot_product'
                ' FROM docs d'
                ' JOIN inverted_index ii ON d.docid = ii.docid'
                ' JOIN term_idf ti ON ii.term = ti.term'
                ' WHERE ii.term IN (' + placeholders + ')'
                ' AND d.doc_norm IS NOT NULL AND d.doc_norm > 0',
                # ' GROUP BY d.docid, ii.term'
                # ' ORDER BY (dot_product / d.doc_norm) DESC'
                # ' LIMIT 200',
                unique_query_terms
            ).fetchall()

            # combine cosine similarity (query-dependent) with HITS score (query-independent)
            # ALPHA = trade-off: higher = more weight on textual relevance
            # ALPHA = cosine sim weight
            # BETA = term proximity weight 
            # GAMMA = authority weight
            ALPHA = 0.8
            BETA = 0.15
            GAMMA = 0.05
            docs = {}
            for row in raw_docs:
                docid = row['docid']
                if docid not in docs:
                    authority  = row['authority_score'] if row['authority_score'] is not None else 0.0
                    docs[docid] = {
                        'docid':   row['docid'],
                        'url':     row['url'],
                        'author':  row['author'],
                        'title':   row['title'],
                        'content': row['content'],
                        'doc_norm': row['doc_norm'],
                        'dot_product': 0.0,
                        'positions': {}
                    }

                docs[docid]['dot_product'] += row['tf'] * row['idf'] * row['idf'] # accumulate dot product for cosine similarity
                docs[docid]['positions'][row['term']] = json.loads(row['positions'])

            # term proximity reranking
            ranked_docs = []

            for doc in docs.values():
                cosine_sim = doc['dot_product'] / (doc['doc_norm'] * query_norm)
                proximity = compute_term_proximity(doc['positions'])

                ranked_docs.append({
                    'docid': doc['docid'],
                    'url': doc['url'],
                    'author': doc['author'],
                    'title': doc['title'],
                    'content': doc['content'],
                    'excerpt': get_excerpt(doc['content'], unique_query_terms),
                    'score': ALPHA * cosine_sim + BETA * proximity + GAMMA * authority
                })

            docs = sorted(ranked_docs, key=lambda x: x['score'], reverse=True) # sort by final score
            docs = docs[:200] # restrict to top 200 results
    else:
        docs = []

    return render_template('interface/index.html', docs=docs, query=query_text)

def compute_term_proximity(positions):
    if len(positions) == 1: # if only one word is found in doc, no term proximity score
        return 0.0
    
    smallest_dist = float('inf')

    for i in range(len(positions)):
        term1 = list(positions.keys())[i]
        for j in range(i + 1, len(positions)):
            term2 = list(positions.keys())[j]
            for pos1 in positions[term1]:
                for pos2 in positions[term2]:
                    dist = abs(pos1 - pos2)
                    if dist < smallest_dist:
                        smallest_dist = dist
    
    if smallest_dist == float('inf'):
        return 0.0

    return 1/smallest_dist