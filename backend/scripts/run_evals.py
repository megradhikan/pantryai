"""Runs PantryAI evals and writes JSON to backend/eval/results/.

Usage (from the repo root):
    python backend/scripts/run_evals.py

Recipe matching eval: compares three rankers over the seeded recipe corpus
(backend/data/recipes.json) on hand-labeled pantry scenarios.
  lexical    match_recipes(), the matcher the app uses for suggestions
  embedding  cosine similarity between the pantry text and each recipe's
             embedding (all-MiniLM-L6-v2, same text format as seed_recipes.py).
             This ranks the same way as the pgvector `<=>` query, but is exact.
  hybrid     top 15 by embedding, re-ranked by match_recipes()
No LLM is called, so running this costs nothing.

OCR extraction eval: validates the receipt parsing pipeline against hand-labeled
scenarios in backend/eval/receipts/scenarios.json. Calls extract_items() on each
scenario's raw OCR text and checks how many expected item names appear in the
extracted output (case-insensitive, partial match). Requires GEMINI_API_KEY.
"""
import json
import os
import sys
from datetime import datetime, timezone

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

import numpy as np  # noqa: E402

from services.embeddings import get_model  # noqa: E402
from services.recipe_matching import match_recipes  # noqa: E402

K = 5
HYBRID_POOL = 15


def recipe_text(recipe):
    names = " ".join(i["name"] for i in recipe["ingredients"])
    return f"{recipe['title']} {names}"


def metrics(ranked_titles, relevant):
    top = ranked_titles[:K]
    hits = sum(1 for t in top if t in relevant)
    return {
        "precision": hits / K,
        "recall": hits / len(relevant),
        "hit_at_1": 1.0 if top and top[0] in relevant else 0.0,
        "max_precision": min(len(relevant), K) / K,
    }


def run_recipe_eval():
    with open(os.path.join(BACKEND, "data", "recipes.json")) as f:
        recipes = json.load(f)
    for n, r in enumerate(recipes):
        r["id"] = str(n)
    titles = {r["id"]: r["title"] for r in recipes}
    known = set(titles.values())

    with open(os.path.join(BACKEND, "eval", "recipes", "scenarios.json")) as f:
        spec = json.load(f)
    scenarios = spec["scenarios"]
    for s in scenarios:
        missing = [t for t in s["relevant"] if t not in known]
        if missing:
            raise SystemExit(f"{s['id']}: unknown recipe titles {missing}")

    model = get_model()
    recipe_vecs = model.encode([recipe_text(r) for r in recipes], normalize_embeddings=True)
    by_id = {r["id"]: r for r in recipes}

    systems = {"lexical": [], "embedding": [], "hybrid": []}
    per_scenario = []
    for s in scenarios:
        inventory = [{"name": n, "status": "fresh"} for n in s["pantry"]]
        relevant = set(s["relevant"])

        lexical = [r["title"] for r in match_recipes(inventory, recipes, limit=len(recipes))]

        query = model.encode("pantry: " + ", ".join(s["pantry"]), normalize_embeddings=True)
        order = np.argsort(-(recipe_vecs @ query))
        embedding = [recipes[i]["title"] for i in order]

        pool = [recipes[i] for i in order[:HYBRID_POOL]]
        hybrid = [r["title"] for r in match_recipes(inventory, pool, limit=len(pool))]

        row = {"id": s["id"], "pantry_size": len(s["pantry"]), "relevant": sorted(relevant)}
        for name, ranked in (("lexical", lexical), ("embedding", embedding), ("hybrid", hybrid)):
            m = metrics(ranked, relevant)
            systems[name].append(m)
            row[name] = {"top5": ranked[:K], **m}
        per_scenario.append(row)

    def mean(rows, key):
        return round(sum(r[key] for r in rows) / len(rows), 4)

    summary = {
        name: {
            "precision_at_5": mean(rows, "precision"),
            "recall_at_5": mean(rows, "recall"),
            "hit_at_1": mean(rows, "hit_at_1"),
        }
        for name, rows in systems.items()
    }
    summary["max_achievable_precision_at_5"] = mean(systems["lexical"], "max_precision")

    return {
        "eval": "recipe_matching",
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_scenarios": len(scenarios),
        "n_recipes_in_corpus": len(recipes),
        "k": K,
        "hybrid_pool_size": HYBRID_POOL,
        "embedding_model": "all-MiniLM-L6-v2",
        "labeling_rule": spec["labeling_rule"],
        "summary": summary,
        "per_scenario": per_scenario,
    }


def run_receipt_eval():
    from agents.receipt_agent import extract_items

    with open(os.path.join(BACKEND, "eval", "receipts", "scenarios.json")) as f:
        spec = json.load(f)
    scenarios = spec["scenarios"]

    results = []
    total_expected = 0
    total_hits = 0
    for s in scenarios:
        items, _, _ = extract_items(s["ocr_text"])
        extracted_names = [i.name.lower() for i in items]
        expected = [e.lower() for e in s["expected_items"]]
        hits = 0
        matched = []
        missed = []
        for exp in expected:
            # partial match: "chicken breast" hits "boneless chicken breast"
            found = any(exp in ext or ext in exp for ext in extracted_names)
            if found:
                hits += 1
                matched.append(exp)
            else:
                missed.append(exp)
        precision = hits / len(expected) if expected else 0.0
        total_expected += len(expected)
        total_hits += hits
        results.append({
            "id": s["id"],
            "expected": expected,
            "extracted": extracted_names,
            "matched": matched,
            "missed": missed,
            "precision": round(precision, 4),
        })

    overall_precision = total_hits / total_expected if total_expected else 0.0
    return {
        "eval": "receipt_ocr_extraction",
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_scenarios": len(scenarios),
        "summary": {
            "overall_precision": round(overall_precision, 4),
            "total_expected_items": total_expected,
            "total_matched_items": total_hits,
        },
        "per_scenario": results,
    }


def main():
    out_dir = os.path.join(BACKEND, "eval", "results")
    os.makedirs(out_dir, exist_ok=True)

    recipe_result = run_recipe_eval()
    path = os.path.join(out_dir, "recipe_matching.json")
    with open(path, "w") as f:
        json.dump(recipe_result, f, indent=2)
    print(f"[recipe] scenarios={recipe_result['n_scenarios']} recipes={recipe_result['n_recipes_in_corpus']}")
    print(json.dumps(recipe_result["summary"], indent=2))
    print(f"wrote {path}")

    if os.environ.get("GEMINI_API_KEY"):
        print("\n[receipt] running OCR extraction eval...")
        receipt_result = run_receipt_eval()
        path = os.path.join(out_dir, "receipt_extraction.json")
        with open(path, "w") as f:
            json.dump(receipt_result, f, indent=2)
        print(f"[receipt] overall_precision={receipt_result['summary']['overall_precision']}")
        print(f"wrote {path}")
    else:
        print("\n[receipt] skipped — GEMINI_API_KEY not set")


if __name__ == "__main__":
    main()
