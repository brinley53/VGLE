'''
Name: eval.py
Description: comparative evaluation for nDCG, P@K
Authors: Brinley Hull & Anakha Krishna
Other sources: rank_bm25 library
Created: 5/14/2026
Last modified:
    5/15/2026 - final evaluation of VGLE w/ different ranking methods and metrics
'''

import json
import math
import os
import sqlite3
from rank_bm25 import BM25Okapi

'''
HOW TO USE THIS PROGRAM:
 1. type in query in QUERY string.
 2. run python vgle/eval.py
 3. copy and paste results into relevance_judgements dictionary
 4. repeat for each query
 5. once dictionary is complete, set QUERY back to ""
 6. run python vgle/eval.py and get results
'''

QUERY = ""

'''
manual relevance judgements
structure: "docid" : judgement
example: "6" : 1

judgement grades:
0 = not relevant
1 = somewhat relevant
2 = most relevant/highly relevant
'''

relevance_judgments = {
#WARNING: THESE ARE JUST EXAMPLES I RAN ON MY MEASLY 40 DOCS. YOU WILL NEED TO RECOMPUTE THESE FOR YOUR CORPUS
#ALL SCORES DEFAULT TO 0 WHEN THEY COME OUT, SO YOU NEED TO CHANGE THE SCORES AFTER PASTING IN
    "shane marriage guide": {
        "729": 2,  # Marriage - Stardew Valley Wiki
        "3484": 2,  # Shane - Stardew Valley Wiki
        "692": 1,  # Villagers - Stardew Valley Wiki
        "3549": 0,  # Stardew Valley -   Post-Launch Progress Update: Version 1.1 
        "7352": 0,  # Morris - Stardew Valley Wiki
        "713": 1,  # Friendship - Stardew Valley Wiki
        "8788": 0,  # Bouncer - Stardew Valley Wiki
        "7429": 0,  # Grandpa - Stardew Valley Wiki
        "5324": 0,  # Birdie - Stardew Valley Wiki
        "2588": 0,  # Emily - Stardew Valley Wiki
        "3870": 0,  # How Does Royal Marriage Work In Europa Universalis 5?
        "7694": 2,  # Bouquet - Stardew Valley Wiki
        "3868": 0,  # Monolith - Last Epoch Maxroll.gg
        "2675": 0,  # Stardew Valley -   Dev Update #24
        "7680": 0,  # Void Ghost Pendant - Stardew Valley Wiki
        "1876": 0,  # Bosses help and Guides for Diablo 4 - D4 Maxroll.gg
        "9346": 0,  # Story of Seasons: Grand Bazaar | TheGamer
        "3524": 0,  # Marnie - Stardew Valley Wiki
        "3357": 0,  # Stardew Valley -   Blog
        "7390": 0  # Jas - Stardew Valley Wiki
    },
    "blue chicken": {
        "3464": 2,  # Chicken - Stardew Valley Wiki
        "6445": 1,  # Slime Egg - Stardew Valley Wiki
        "4938": 0,  # Minecraft Live is Coming Soon! – Minecraft Wiki
        "347": 1,  # Animals - Stardew Valley Wiki
        "817": 0,  # Item – Minecraft Wiki
        "2611": 0,  # Roe - Stardew Valley Wiki
        "6833": 0,  # Tiger Hat - Stardew Valley Wiki
        "6740": 0,  # Mr. Qi's Hat - Stardew Valley Wiki
        "6763": 0,  # Qi Mask - Stardew Valley Wiki
        "6886": 0,  # Dragonscale Boots - Stardew Valley Wiki
        "5819": 0,  # Golden Chicken - Stardew Valley Wiki
        "5770": 0,  # Blue Prince - IGN
        "5790": 0,  # Blue Prince Interactive Maps and Locations - IGN
        "3445": 1,  # Coop - Stardew Valley Wiki
        "3423": 0,  # The Blue Gate - ARC Raiders - IGN
        "4295": 0,  # Blue Lock Rivals codes for May 2026 | VG247
        "8284": 0,  # Blue Prince | TheGamer
        "5809": 0,  # Mount Holly - Blue Prince - IGN
        "2767": 0,  # Project: Mist on Steam
        "3776": 0,  # Traveling Merchant - Official Terraria Wiki
        "2262": 0,  # Modding:Migrate to Stardew Valley 1.6.9 - Stardew Valley Wik
        "1833": 0,  # Items - Official Terraria Wiki
        "2184": 0,  # Pets - Official Terraria Wiki
        "61": 0,  # Version History - Stardew Valley Wiki
        "2208": 0,  # Mounts - Official Terraria Wiki
        "1431": 0,  # Mounts - Official Terraria Wiki
        "2267": 0  # Miscellaneous - Official Terraria Wiki
    },
    "rennala guide": {
        "5887": 2,  # Elden Ring: How to beat Rennala, Queen of the Full Moon | Ro
        "5674": 0,  # How to respec in Elden Ring: Larval Tear locations | Rock Pa
        "5477": 0,  # Miriel, Pastor of Vows - Eldenpedia
        "1261": 2,  # Rennala, Queen of the Full Moon - Eldenpedia
        "5740": 2,  # Rennala, Queen of the Full Moon - Eldenpedia
        "2063": 0,  # Carian Royal Family - Eldenpedia
        "3062": 0,  # Radagon of the Golden Order - Eldenpedia
        "1238": 0,  # Radagon of the Golden Order - Eldenpedia
        "2034": 0,  # Academy of Raya Lucaria - Eldenpedia
        "124": 1,  # Bosses - Eldenpedia
        "3868": 0,  # Monolith - Last Epoch Maxroll.gg
        "85": 0,  # Elden Ring boss locations: All 238 Elden Ring bosses | Rock 
        "5473": 0  # Elden Ring Sellen quest walkthrough | Rock Paper Shotgun
    },
    "wandering seals locations": {
    "7408": 2,  # All Wandering Seals in Where Winds Meet | Map Genie
    "471": 1,  # Where Winds Meet Map | Map Genie
    "2034": 0,  # Academy of Raya Lucaria - Eldenpedia
    "239": 0,  # Nightreign:Locations - Eldenpedia
    "2205": 0,  # Talisman - Charms & Sets - D4 Maxroll.gg
    "5318": 0,  # Sorcerer Thops - Eldenpedia
    "2586": 0,  # Sellia, Town of Sorcery - Eldenpedia
    "8535": 0,  # All Hallownest Seals in Hollow Knight | Map Genie
    "827": 0,  # Hollow Knight Interactive Map | Map Genie
    "4472": 0,  # Sailor Piece | Eurogamer.net
    "3743": 0,  # A Wandering Trader Springs to Life! – Minecraft Wiki
    "767": 0,  # Locations - The Bendy Wiki
    "5717": 0,  # All Abyss Cressets in Crimson Desert | Map Genie
    "2440": 0  # Crimson Desert Guide - IGN
}, "genocide route": {
    "1122": 1,  # Endings - The Undertale Wiki
    "2151": 0,  # Player - The Undertale Wiki
    "6003": 0,  # Mettaton NEO - The Undertale Wiki
    "278": 0,  # Chara - The Undertale Wiki
    "4869": 0,  # Category:Enemies - The Undertale Wiki
    "651": 0,  # Vendor - The Undertale Wiki
    "5900": 0,  # Vendor - The Undertale Wiki
    "1193": 2,  # Genocide Route - The Undertale Wiki
    "1862": 0,  # Undertale Demo - The Undertale Wiki
    "1591": 0,  # Page organization - The Undertale Wiki
    "7607": 0,  # Pokémon Red/Blue Map | Map Genie
    "5230": 0  # SAVE - The Undertale Wiki
}
}

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "instance", "vsgl.sqlite")

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

ALPHA = 0.8   # cosine similarity weight
BETA  = 0.15  # term proximity weight
GAMMA = 0.05  # HITS authority weight

def preprocess(text):
    processed = []
    for term in text.split(" "): # split into list of words
        term = term.lower() # convert to lowercase
        term = ''.join(ch for ch in term if ch.isalnum())  # remove punctuation (only keep characters that are alpha numeric)
        if not term or term in STOPWORDS: # skip empty tokens and stopwords
            continue
        processed.append(term)
    return processed

# BM25 baseline eval: standard metric for IR
def bm25_eval(db, query_str, top_k=200):
    rows = db.execute("SELECT docid, url, title, content FROM docs").fetchall()

    docids = []
    urls = []
    titles = []
    corpus = []
    for row in rows:
        docids.append(row["docid"])
        urls.append(row["url"])
        titles.append(row["title"])
        corpus.append(preprocess(row["content"]))

    bm25 = BM25Okapi(corpus)

    query_tokens = preprocess(query_str)
    if len(query_tokens) == 0:
        return []

    scores = bm25.get_scores(query_tokens)

    # create (docid, url, title, score)
    combined = []
    for i in range(len(docids)):
        combined.append((docids[i], urls[i], titles[i], float(scores[i])))

    # sort by score descending
    combined.sort(key=lambda x: x[3], reverse=True)

    # keep docs only scored higher than 0
    results = []
    for item in combined[:top_k]:
        if item[3] > 0.0:
            results.append(item)

    return results

# tfidf cosine similarity only eval: baseline to show improvement w/ HITS and term proximity
def tfidf_eval(db, query_str, top_k=200):
    processed = preprocess(query_str)

    # get unique terms, preserve order
    unique_terms = []
    seen = set()
    for term in processed:
        if term not in seen:
            unique_terms.append(term)
            seen.add(term)

    if len(unique_terms) == 0:
        return []

    placeholders = ','.join(['?'] * len(unique_terms))

    idf_rows = db.execute(
        "SELECT idf FROM term_idf WHERE term IN (" + placeholders + ")",
        unique_terms
    ).fetchall()

    query_norm_sq = 0.0
    for row in idf_rows:
        query_norm_sq += row["idf"] * row["idf"]
    query_norm = math.sqrt(query_norm_sq)

    if query_norm == 0.0:
        return []

    raw = db.execute(
        "SELECT d.docid, d.url, d.title, d.doc_norm,"
        "       SUM(ii.tf * ti.idf * ti.idf) AS dot_product"
        " FROM docs d"
        " JOIN inverted_index ii ON d.docid = ii.docid"
        " JOIN term_idf ti ON ii.term = ti.term"
        " WHERE ii.term IN (" + placeholders + ")"
        "   AND d.doc_norm IS NOT NULL AND d.doc_norm > 0"
        " GROUP BY d.docid",
        unique_terms
    ).fetchall()

    results = []
    for row in raw:
        cosine_sim = row["dot_product"] / (row["doc_norm"] * query_norm)
        results.append((row["docid"], row["url"], row["title"], cosine_sim))

    results.sort(key=lambda x: x[3], reverse=True)
    return results[:top_k]


# vgle eval: blended score of cosine similarity, term proximity, and authority score
def compute_term_proximity(positions):
    term_list = list(positions.keys())
    if len(term_list) < 2:
        return 0.0

    smallest_dist = float('inf')
    for i in range(len(term_list)):
        for j in range(i + 1, len(term_list)):
            for p1 in positions[term_list[i]]:
                for p2 in positions[term_list[j]]:
                    dist = abs(p1 - p2)
                    if dist < smallest_dist:
                        smallest_dist = dist

    if smallest_dist == float('inf'):
        return 0.0
    return 1.0 / smallest_dist


def vgle_eval(db, query_str, top_k=200):
    processed = preprocess(query_str)

    unique_terms = []
    seen = set()
    for term in processed:
        if term not in seen:
            unique_terms.append(term)
            seen.add(term)

    if len(unique_terms) == 0:
        return []

    placeholders = ','.join(['?'] * len(unique_terms))

    idf_rows = db.execute(
        "SELECT idf FROM term_idf WHERE term IN (" + placeholders + ")",
        unique_terms
    ).fetchall()

    query_norm_sq = 0.0
    for row in idf_rows:
        query_norm_sq += row["idf"] * row["idf"]
    query_norm = math.sqrt(query_norm_sq)

    if query_norm == 0.0:
        return []

    raw = db.execute(
        "SELECT d.docid, d.url, d.title, d.doc_norm, d.authority_score,"
        "       ii.term, ii.positions,"
        "       (ii.tf * ti.idf * ti.idf) AS term_dot"
        " FROM docs d"
        " JOIN inverted_index ii ON d.docid = ii.docid"
        " JOIN term_idf ti ON ii.term = ti.term"
        " WHERE ii.term IN (" + placeholders + ")"
        "   AND d.doc_norm IS NOT NULL AND d.doc_norm > 0",
        unique_terms
    ).fetchall()

    docs = {}
    for row in raw:
        docid = row["docid"]
        if docid not in docs:
            docs[docid] = {
                "docid":     docid,
                "url":       row["url"],
                "title":     row["title"],
                "doc_norm":  row["doc_norm"],
                "authority": row["authority_score"] or 0.0,
                "dot_sum":   0.0,
                "positions": {}
            }
        docs[docid]["dot_sum"] += row["term_dot"]
        docs[docid]["positions"][row["term"]] = json.loads(row["positions"])

    results = []
    for doc in docs.values():
        cosine_sim = doc["dot_sum"] / (doc["doc_norm"] * query_norm)
        proximity  = compute_term_proximity(doc["positions"])
        score = ALPHA * cosine_sim + BETA * proximity + GAMMA * doc["authority"]
        results.append((doc["docid"], doc["url"], doc["title"], score))

    results.sort(key=lambda x: x[3], reverse=True)
    return results[:top_k]


# metrics

# dcg for nDCG usage
def dcg_at_k(relevances, k):
    score = 0.0
    for i in range(min(k, len(relevances))):
        rel = relevances[i]
        score += (2 ** rel - 1) / math.log2(i + 2)  # i+2 because log2(rank+1), rank starts at 1
    return score

# nDCG
def ndcg_at_k(relevances, all_grades, k):
    ideal = sorted(all_grades, reverse=True)
    idcg = dcg_at_k(ideal, k)
    if idcg == 0.0:
        return 0.0
    return dcg_at_k(relevances, k) / idcg

# P@K
def precision_at_k(relevances, k):
    count = 0
    for i in range(min(k, len(relevances))):
        if relevances[i] >= 1:
            count += 1
    return count / k

def full_eval(db, method_name, method_fn, judgments):
    print("==method: " + method_name + "==")

    total_ndcg5 = 0.0
    total_ndcg10 = 0.0
    total_p5 = 0.0
    count = 0

    for query_str in judgments:
        query_judgments = judgments[query_str]
        results = method_fn(db, query_str, top_k=10)

        relevances = []
        for item in results:
            docid = str(item[0])
            if docid in query_judgments:
                relevances.append(query_judgments[docid])
            else:
                relevances.append(0)

        all_grades = list(query_judgments.values())

        ndcg5 = ndcg_at_k(relevances, all_grades,5)
        ndcg10 = ndcg_at_k(relevances, all_grades, 10)
        p5 = precision_at_k(relevances, 5)

        print("Query: " + query_str)
        print("nDCG@5 = " + str(round(ndcg5, 4)))
        print("nDCG@10 = " + str(round(ndcg10, 4)))
        print("P@5 = " + str(round(p5, 4)))
        print()

        total_ndcg5 += ndcg5
        total_ndcg10 += ndcg10
        total_p5 += p5
        count += 1

    print("Average for all queries:")
    print("nDCG@5 = " + str(round(total_ndcg5 / count, 4)))
    print("nDCG@10 = " + str(round(total_ndcg10 / count, 4)))
    print("P@5 = " + str(round(total_p5 / count, 4)))
    print()

    return total_ndcg5 / count, total_ndcg10 / count, total_p5 / count


# get all docs for each method for the query
def fetch_query_docs(db, query_str):
    print("docs for: " + query_str)
    print()

    all_results = {}
    all_results["BM25"] = bm25_eval(db, query_str, top_k=10)
    all_results["TF-IDF"] = tfidf_eval(db, query_str, top_k=10)
    all_results["VGLE"] = vgle_eval(db, query_str, top_k=10)

    for method_name in all_results:
        print(method_name + ":")
        results = all_results[method_name]
        for i in range(len(results)):
            docid = results[i][0]
            title = results[i][2]
            print(str(i + 1) + ") docid=" + str(docid) + "  " + str(title))
        print()

    # get unique docids for all methods
    seen_docids = []
    seen_set = set()
    for method_name in all_results:
        for item in all_results[method_name]:
            docid = item[0]
            if docid not in seen_set:
                seen_docids.append(item)
                seen_set.add(docid)

    print('copy structure into relevance judgements:')
    print('"' + query_str + '": {')
    for i in range(len(seen_docids)):
        docid = seen_docids[i][0]
        title = seen_docids[i][2]
        comma = "," if i < len(seen_docids) - 1 else ""
        print('    "' + str(docid) + '": 0' + comma + '  # ' + str(title)[:60])
    print('},')

def main():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    if QUERY != "":
        fetch_query_docs(db, QUERY)
        db.close()
        return

    # skip queries with no judgments filled in yet
    active_judgments = {}
    for query in relevance_judgments:
        if len(relevance_judgments[query]) > 0:
            active_judgments[query] = relevance_judgments[query]

    if len(active_judgments) == 0:
        print("no judgements")
        db.close()
        return

    methods = {
        "BM25": bm25_eval,
        "TF-IDF": tfidf_eval,
        "VGLE": vgle_eval,
    }

    averages = {}
    for name in methods:
        ndcg5, ndcg10, p5 = full_eval(db, name, methods[name], active_judgments)
        averages[name] = (ndcg5, ndcg10, p5)

    print("+==SUMMARY==+")
    for name in averages:
        print(name + ":")
        print("nDCG@5 = " + str(round(averages[name][0], 4)))
        print("nDCG@10 = " + str(round(averages[name][1], 4)))
        print("P@5 = " + str(round(averages[name][2], 4)))
        print()

    db.close()

if __name__ == "__main__":
    main()