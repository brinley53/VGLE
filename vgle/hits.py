'''
Name: hits.py
Description: Compute HITS hub and authority scores for all crawled documents
Authors: Brinley Hull & Anakha Krishna
Other sources: Used https://networkx.org/documentation/stable/_modules/networkx/algorithms/link_analysis/hits_alg.html#hits as a reference for tolerance
Created: 4/30/2026
Last modified: 
    5/1/2026: HITS
'''

import math
from vgle.db import get_db
from vgle import create_app


def compute_hits(num_iterations=200, tol=1e-6): 
    db = get_db()

    doc_rows = db.execute('SELECT docid FROM docs').fetchall()
    docids = []
    for r in doc_rows:
        docids.append(r['docid'])
    n = len(docids)
    if n == 0:
        return

    # map docid -> array index for list-based math
    idx = {}
    for i, docid in enumerate(docids):
        idx[docid] = i

    out_edges = []
    in_edges = []
    for _ in range(n):
        out_edges.append([])
        in_edges.append([])

    for row in db.execute('SELECT src_docid, dst_docid FROM links').fetchall():
        src_i = idx.get(row['src_docid'])
        dst_i = idx.get(row['dst_docid'])
        if src_i is None or dst_i is None:
            continue
        out_edges[src_i].append(dst_i)
        in_edges[dst_i].append(src_i)

    hub  = [1.0] * n
    auth = [1.0] * n

    for iteration in range(num_iterations):
        # authority(j) = sum of hub scores of pages that link to j
        new_auth = []
        for j in range(n):
            total = 0.0
            for i in in_edges[j]:
                total += hub[i]
            new_auth.append(total)

        # hub(i) = sum of auth scores of pages i links to
        new_hub = []
        for i in range(n):
            total = 0.0
            for j in out_edges[i]:
                total += new_auth[j]
            new_hub.append(total)

        # L2 norm
        auth_sum = 0.0
        for a in new_auth:
            auth_sum += a * a
        auth_norm = math.sqrt(auth_sum)

        hub_sum = 0.0
        for h in new_hub:
            hub_sum += h * h
        hub_norm = math.sqrt(hub_sum)

        if auth_norm > 0:
            for i in range(n):
                new_auth[i] = new_auth[i] / auth_norm
        if hub_norm > 0:
            for i in range(n):
                new_hub[i] = new_hub[i] / hub_norm

        # check convergence --> max absolute change in authority scores
        delta = 0.0
        for i in range(n):
            change = abs(new_auth[i] - auth[i])
            if change > delta:
                delta = change
        hub, auth = new_hub, new_auth

        if delta < tol:
            print(f"HITS converged. iteration: {iteration + 1}")
            break
    else:
        print(f"HITS did NOT converge. iteration: {num_iterations}")

    for docid, i in idx.items():
        db.execute(
            'UPDATE docs SET hub_score = ?, authority_score = ? WHERE docid = ?',
            (hub[i], auth[i], docid)
        )
    db.commit()
    print(f"HITS scores written for {n} documents")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        compute_hits()
