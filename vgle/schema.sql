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
*/

DROP TABLE IF EXISTS term_idf;
DROP TABLE IF EXISTS inverted_index;
DROP TABLE IF EXISTS docs;

CREATE TABLE docs (
  docid INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT UNIQUE,
  author TEXT,
  title TEXT,
  content TEXT,
  doc_norm REAL
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
  PRIMARY KEY (term, docid),
  FOREIGN KEY (docid) REFERENCES docs (docid)
);