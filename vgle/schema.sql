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
*/

DROP TABLE IF EXISTS term_idf;
DROP TABLE IF EXISTS inverted_index;
DROP TABLE IF EXISTS docs;

CREATE TABLE docs (
  docid INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT, /*UNIQUE*/
  author TEXT,
  title TEXT,
  content TEXT
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

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);