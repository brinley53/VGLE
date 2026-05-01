'''
Name: hits.py
Description: Compute HITS hub and authority scores for all crawled documents
Authors: Brinley Hull & Anakha Krishna
Created: 4/30/2026
Last modified: 
    5/1/2026: HITS
'''

import math
from vgle.db import get_db
from vgle import create_app


def compute_hits(num_iterations=100, tol=1e-6): # tol = convergence tolerance
    db = get_db()

    doc_rows = db.execute('SELECT docid FROM docs').fetchall()
    docids = [r['docid'] for r in doc_rows]
    n = len(docids)
    if n == 0:
        return

    # map docid -> array index for list-based math
    idx = {docid: i for i, docid in enumerate(docids)}

    out_edges = [[] for _ in range(n)]
    in_edges  = [[] for _ in range(n)]

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
        new_auth = [sum(hub[i] for i in in_edges[j]) for j in range(n)]
        # hub(i) = sum of auth scores of pages i links to
        new_hub  = [sum(new_auth[j] for j in out_edges[i]) for i in range(n)]

        # L2 norm
        auth_norm = math.sqrt(sum(a * a for a in new_auth))
        hub_norm  = math.sqrt(sum(h * h for h in new_hub))

        if auth_norm > 0:
            new_auth = [a / auth_norm for a in new_auth]
        if hub_norm > 0:
            new_hub  = [h / hub_norm  for h in new_hub]

        # check convergence --> max absolute change in authority scores
        delta = max(abs(new_auth[i] - auth[i]) for i in range(n))
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
