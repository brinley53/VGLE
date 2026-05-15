'''
Name: inverted_index.py
Description: process documents and create inverted index and idf tables
Authors: Brinley Hull & Anakha Krishna
Created: 4/2/2026
Last modified: 
    4/8/2026 - send information to database, create idf tables and document vectors
    4/15/2026 - change document retrieval from folder/files to database
    4/15/2026 - update/simplify document iteration to support non-consecutive docids and use 1-based incrementing instead of 0-based so that the last doc is not skipped
                remove unused doc_vector calculation
    4/17/2026 - delete temporary database table creation
    4/24/2026 - calculate cosine similarity for documents
    4/30/2026 - add some stopwords
    5/14/2026 - delete unused code that was commented out, add position information for terms in docs, increase efficiency
'''

import math
from vgle.db import get_db
from vgle import create_app
import json

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "has", "have", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "not", "no", "nor", "so",
    "yet", "as", "if", "then", "than", "that", "this", "these", "those",
    "it", "its", "they", "their", "them", "we", "our", "you", "your",
    "i", "my", "he", "she", "his", "her", "who", "which", "what", "how",
    "when", "where", "about", "out", "up", "all", "each", "more", "most",
    "other", "some", "only", "same", "also", "any", "many", "just",
}

def create_index():
    db = get_db()

    # make sure docs table exists before indexing
    if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='docs'").fetchone():
        return
    
        
    db.executescript('''
        DROP TABLE IF EXISTS term_idf;
        DROP TABLE IF EXISTS inverted_index;

        CREATE TABLE term_idf (
            term TEXT PRIMARY KEY,
            idf REAL,
            df INTEGER
        );

        CREATE TABLE inverted_index (
            term TEXT,
            docid INTEGER,
            tf INTEGER,
            positions TEXT,
            PRIMARY KEY (term, docid),
            FOREIGN KEY (docid) REFERENCES docs (docid)
        );
    ''')

    db.commit()

    # inverted index with term as key, value as another dict with key = docid, value = term freq
    # doc freq can be determined by checking the length of the dict

    docs = db.execute('SELECT * FROM docs') # retrieve documents
    term_df = {}
    doc_tf = {}

    i = 0
    rows = []   # batch buffer for executemany

    for doc in docs:
        docid = doc["docid"]
        term_tf = {}
        term_pos = {}
        
        text = doc["content"].split()
        position = 0

        for term in text: 
            # preprocessing
            term = term.lower() # convert to lowercase
            term = ''.join(ch for ch in term if ch.isalnum()) # remove punctuation (only keep characters that are alpha numeric)
            if term == "" or term in STOPWORDS: # skip stopwords
                continue

            if term not in term_tf: # create entry for term if not already in index
                term_tf[term] = 0
                term_pos[term] = []
                if term not in term_df: # doc frequency (only counts once per doc)
                    term_df[term] = 1
                else:
                    term_df[term] += 1

            term_tf[term] += 1
            term_pos[term].append(position)

            position += 1

        for term in term_tf:
            rows.append((term, docid, term_tf[term], json.dumps(term_pos[term])))

        doc_tf[docid] = term_tf

        i += 1
        if i % 1000 == 0:
            db.executemany(
                'INSERT INTO inverted_index (term, docid, tf, positions) VALUES (?, ?, ?, ?)',
                rows
            )
            rows.clear()
            db.commit()

    # Flush remaining rows
    if rows:
        db.executemany(
            'INSERT INTO inverted_index (term, docid, tf, positions) VALUES (?, ?, ?, ?)',
            rows
        )
        
    db.commit()

    # calculate idf for each term in dictionary
    N = db.execute('SELECT COUNT(*) FROM docs').fetchone()[0] # total number of documents
    sorted_terms = sorted(term_df) # sort the terms alphabetically
    idf = {} # create dictionary for idf    
    idf_rows = []
    i = 0
    for term in sorted_terms:
        df = term_df[term]
        term_idf_val = math.log10(N / df)
        idf[term] = term_idf_val
        idf_rows.append((term, term_idf_val, df))
        i += 1
        if i % 1000 == 0:
            db.executemany('INSERT INTO term_idf (term, idf, df) VALUES (?, ?, ?)', idf_rows)
            idf_rows.clear()
            db.commit()

    if idf_rows:
        db.executemany('INSERT INTO term_idf (term, idf, df) VALUES (?, ?, ?)', idf_rows)
    db.commit()

    # calculate doc norms
    doc_norm_rows = []
    i = 0
    for docid, term_tf in doc_tf.items():
        sum_sq = 0.0

        for term, tf in term_tf.items():
            term_idf = idf[term]
            weight = tf * term_idf
            sum_sq += weight * weight

        doc_norm_rows.append((math.sqrt(sum_sq), docid))

        if i % 1000 == 0:
            db.executemany('UPDATE docs SET doc_norm = ? WHERE docid = ?', doc_norm_rows)
            doc_norm_rows.clear()
            db.commit()
        i += 1

    if doc_norm_rows:
        db.executemany('UPDATE docs SET doc_norm = ? WHERE docid = ?', doc_norm_rows)
    db.commit()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_index()