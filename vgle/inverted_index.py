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
'''

import math
from vgle.db import get_db
from vgle import create_app

def create_index():
    db = get_db()

    stopwords = [] # list of stopwords to ignore

    index = {} # initialize the inverted index as a dictionary
    # inverted index with term as key, value as another dict with key = docid, value = term freq
    # doc freq can be determined by checking the length of the dict

    docs = db.execute('SELECT * FROM docs') # retrieve documents
    
    for doc in docs:
        text = doc["content"].split()
        for term in text: 
            # preprocessing
            term = term.lower() # convert to lowercase
            term = ''.join(ch for ch in term if ch.isalnum()) # remove punctuation (only keep characters that are alpha numeric)
            if term == "" or term in stopwords: # skip stopwords
                continue

            if term not in index: # create entry for term if not already in index
                index[term] = {}

            if doc["docid"] not in index[term]: # if doc is not yet counted for the term
                index[term][doc["docid"]] = 0
        
            index[term][doc["docid"]] += 1 # add one to the term frequency for the doc

    # calculate idf for each term in dictionary
    N = db.execute('SELECT COUNT(*) FROM docs').fetchone()[0] # total number of documents

    sorted_terms = sorted(index) # sort the terms alphabetically
    idf = {} # create dictionary for idf

    i = 0
    for term in sorted_terms: # go through words
        df = len(index[term])
        idf[term] = math.log10(N/df) # calculate idf for each term
        
        # insert into database
        db.execute(
            'INSERT INTO term_idf (term, idf, df)'
            ' VALUES (?, ?, ?)',
            (term, idf[term], df)
        )
        
        # create document vectors
        for actual_docid, tf in index[term].items(): # iterate through every document that has the current term. "actual_docid" to be safe for naming collisions
                # insert into database
                db.execute(
                    'INSERT INTO inverted_index (term, docid, tf)'
                    ' VALUES (?, ?, ?)',
                    (term, actual_docid, tf)
                )
        i += 1

    # send inverted index and idf values to database
    db.commit()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_index()