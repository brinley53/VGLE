'''
Name: inverted_index.py
Description: process documents and create inverted index
Authors: Brinley Hull & Anakha Krishna
Created: 4/2/2026
Last modified: 4/2/2026 
'''

import os

docs = []
doc_path = "docs"
stopwords = [] # list of stopwords to ignore

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

print(index)