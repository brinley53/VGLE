'''
Name: inverted_index.py
Description: process documents and create inverted index and idf tables
Authors: Brinley Hull & Anakha Krishna
Created: 4/2/2026
Last modified: 
    4/8/2026 - send information to database, create idf tables and document vectors
'''

import os
import math
from vgle.db import get_db
from vgle.db import init_db
from flask import current_app

def create_index():
    init_db() # initialize database to create tables for inverted index and idf values

    docs = []
    doc_path = os.path.join(current_app.root_path, "docs")
    stopwords = [] # list of stopwords to ignore

    db = get_db()

    index = {} # initialize the inverted index as a dictionary
    # inverted index with term as key, value as another dict with key = docid, value = term freq
    # doc freq can be determined by checking the length of the dict

    docid = 0 
    for file in os.listdir(doc_path):
        with open(os.path.join(doc_path, file), 'r', encoding='utf-8') as doc: #open doc
            text = doc.read()
            terms = text.split()
        for term in terms: 
            if term in stopwords: # skip stopwords
                continue

            if term not in index: # create entry for term if not already in index
                index[term] = {}

            if docid not in index[term]: # if doc is not yet counted for the term
                index[term][docid] = 0
        
            index[term][docid] += 1 # add one to the term frequency for the doc
        docid += 1 # increment the docid

    # calculate idf for each term in dictionary
    N = docid # total number of documents

    sorted_terms = sorted(index) # sort the terms alphabetically
    idf = {} # create dictionary for idf
    doc_vectors = [[0 for i in range(len(index))] for j in range(N)] # create base idf values of 0 for every document. len(index) is the number of terms

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
        for doc_index in range(N): # cycle through documents
            if doc_index in index[term]: # if the doc has the term
                tf = index[term][doc_index] # term freq in document
                doc_vectors[doc_index][i] = idf[term] * tf

                # insert into database
                db.execute(
                    'INSERT INTO inverted_index (term, docid, tf)'
                    ' VALUES (?, ?, ?)',
                    (term, doc_index, tf)
                )
        i += 1

    # send inverted index and idf values to database
    db.commit()