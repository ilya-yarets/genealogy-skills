"""Validate the portable proposal contract; does not judge historical truth."""

import argparse
import json
from pathlib import Path


def validate(data):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def text(value):
        return isinstance(value, str) and bool(value.strip())

    def fields(row, required, where):
        require(isinstance(row, dict), f"{where}: expected object")
        if not isinstance(row, dict):
            return False
        for key in required:
            require(text(row.get(key)), f"{where}.{key}: expected nonempty string")
        return all(text(row.get(key)) for key in required)

    if not isinstance(data, dict):
        return ["result: expected object"]
    require(data.get("schema_version") == "genealogy-handoff-1", "schema_version: unsupported")
    task = data.get("task")
    if fields(task, ["kind", "question", "status"], "task"):
        require(task.get("kind") in {"research", "interview", "evidence-review"}, "task.kind: invalid")
        require(task.get("status") in {"answered", "unresolved", "blocked"}, "task.status: invalid")

    arrays = {}
    for key in ["sources", "people", "claims", "hypotheses", "searches", "coverage", "next_steps"]:
        value = data.get(key)
        require(isinstance(value, list), f"{key}: expected array")
        arrays[key] = value if isinstance(value, list) else []
    ids = {}
    seen = set()
    for key in ["sources", "people", "claims", "hypotheses", "searches"]:
        ids[key] = set()
        for index, row in enumerate(arrays[key]):
            where = f"{key}[{index}]"
            if not fields(row, ["id"], where):
                continue
            ident = row.get("id")
            if text(ident):
                require(ident not in seen, f"{where}: duplicate ID {ident}")
                seen.add(ident)
                ids[key].add(ident)

    for row in arrays["sources"]:
        if not fields(row, ["title", "kind", "access", "locator", "notes"], "source"):
            continue
        require(row.get("kind") in {"document", "index", "interview", "photo", "tree", "catalog", "other"}, "source.kind: invalid")
        require(row.get("access") in {"read", "partial", "metadata-only", "unavailable", "not-inspected"}, "source.access: invalid")
        # A URL can identify supplied material without a new external access.
        if "accessed_at" in row:
            require(text(row["accessed_at"]), "source.accessed_at: expected nonempty string")
    for row in arrays["people"]:
        if fields(row, ["label", "identity", "notes"], "person"):
            require(row.get("identity") in {"supplied-person", "source-bound", "unnamed-position"}, "person.identity: invalid")
    for row in arrays["claims"]:
        if not fields(row, ["person_id", "predicate", "basis", "support", "review", "notes"], "claim"):
            continue
        require(row.get("person_id") in ids["people"], "claim.person_id: dangling reference")
        related = row.get("related_person_id")
        require(related is None or (text(related) and related in ids["people"]), "claim.related_person_id: dangling reference")
        require(text(row.get("value")) or isinstance(row.get("value"), dict), "claim.value: expected text or object")
        require(row.get("basis") in {"document", "oral", "machine", "inference", "calculation"}, "claim.basis: invalid")
        require(row.get("support") in {"unassessed", "single-source", "independent-support", "dependent", "conflicting"}, "claim.support: invalid")
        require(row.get("review") == "proposed", "claim.review: only proposals are supported")
        refs = row.get("source_refs")
        require(isinstance(refs, list) and bool(refs), "claim.source_refs: evidence reference required")
        for ref in refs if isinstance(refs, list) else []:
            if fields(ref, ["source_id", "locator"], "source_ref"):
                require(ref.get("source_id") in ids["sources"], "source_ref.source_id: dangling reference")
    for row in arrays["hypotheses"]:
        if not fields(row, ["question", "dependence", "conclusion", "resolving_evidence"], "hypothesis"):
            continue
        for key in ["candidate_ids", "for", "against"]:
            require(isinstance(row.get(key), list), f"hypothesis.{key}: expected array")
        for key in ["for", "against"]:
            grounds = row.get(key)
            if isinstance(grounds, list):
                require(all(text(x) for x in grounds), f"hypothesis.{key}: expected nonempty strings")
        candidates = row.get("candidate_ids", [])
        if isinstance(candidates, list):
            require(all(text(x) and x in ids["people"] for x in candidates), "hypothesis.candidate_ids: dangling reference")
    for row in arrays["searches"]:
        if not fields(row, ["target", "query", "scope", "origin", "outcome", "examined", "resume"], "search"):
            continue
        origin, outcome = row["origin"], row["outcome"]
        require(origin in {"planned", "performed-now", "supplied-log"}, "search.origin: invalid")
        require(outcome in {"found", "no-match-in-scope", "not-covered", "access-blocked", "error", "not-run"}, "search.outcome: invalid")
        if origin == "planned":
            require(outcome == "not-run", "search: planned search must have outcome not-run")
        if origin == "performed-now":
            require(outcome != "not-run", "search: performed-now search must have an executed outcome")
        if "searched_at" in row:
            require(text(row["searched_at"]), "search.searched_at: expected nonempty string")
            require(outcome != "not-run", "search: not-run search cannot have an execution date")
        # A literal web target is identifiable without guessing what a collection
        # name or local source ID means. Other external targets need semantic review.
        # A supplied log keeps its original date (or missing-date uncertainty).
        if origin == "performed-now" and row["target"].strip().lower().startswith(("http://", "https://")):
            require(text(row.get("searched_at")), "search.searched_at: required for a current external search")
    valid_targets = set().union(*(ids[k] for k in ["sources", "people", "claims", "hypotheses"]))
    for row in arrays["coverage"]:
        if not fields(row, ["item", "disposition", "reason"], "coverage"):
            continue
        require(row.get("disposition") in {"proposed", "lead", "conflict", "excluded", "pending"}, "coverage.disposition: invalid")
        targets = row.get("target_ids")
        require(isinstance(targets, list), "coverage.target_ids: expected array")
        if isinstance(targets, list):
            require(all(text(x) and x in valid_targets for x in targets), "coverage.target_ids: dangling reference")
            if row.get("disposition") in {"proposed", "conflict"}:
                require(bool(targets), "coverage: proposed/conflict must have targets")
                if isinstance(task, dict) and task.get("kind") == "interview":
                    require(any(text(x) and x in ids["people"] | ids["claims"] for x in targets), "interview coverage: source-only entry is not a tree proposal")
    require(all(text(x) for x in arrays["next_steps"]), "next_steps: expected strings")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.files:
        try:
            errors = validate(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError) as exc:
            errors = [str(exc)]
        failed |= bool(errors)
        print(f"{path.name}: {'FAIL' if errors else 'PASS'}")
        for message in errors:
            print(f"  {message}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
