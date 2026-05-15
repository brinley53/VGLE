/*
Name: schema.sql
Description: SQL commands to create empty tables
Authors: Brinley Hull & Anakha Krishna
Other sources: Flask tutorial flask.com
Created: 3/22/2026
Last modified: 
  4/8/2026 - added inverted index and idf tables
  4/9/2026 - added table for documents/urls
  4/15/2026 - temporarily allow url non unique
  4/23/2026 - add doc_norm to docs table
  4/24/2026 - urls unique again
  4/26/2026 - Delete tutorial tables
  4/30/2026 - add tables and rows for HITS scores and calculations
  5/14/2026 - add position to inverted index
*/

DROP TABLE IF EXISTS links;
DROP TABLE IF EXISTS term_idf;
DROP TABLE IF EXISTS inverted_index;
DROP TABLE IF EXISTS docs;

CREATE TABLE docs (
  docid INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT UNIQUE,
  author TEXT,
  title TEXT,
  content TEXT UNIQUE,
  doc_norm REAL,
  hub_score REAL DEFAULT 0.0,
  authority_score REAL DEFAULT 0.0
);

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

CREATE TABLE links (
  src_docid INTEGER NOT NULL,
  dst_docid INTEGER NOT NULL,
  PRIMARY KEY (src_docid, dst_docid),
  FOREIGN KEY (src_docid) REFERENCES docs (docid),
  FOREIGN KEY (dst_docid) REFERENCES docs (docid)
);