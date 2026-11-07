"""Portable regressions for typed proposal references; all material is invented."""

import copy
import importlib.util
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "reference_validator", Path(__file__).resolve().parents[1] / "tools/validate_genealogy_handoff.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sample():
    return {
        "schema_version": "genealogy-handoff-1",
        "task": {"kind": "interview", "question": "What does the supplied account say?", "status": "unresolved"},
        "sources": [{"id": "S1", "title": "Invented account", "kind": "interview", "access": "read",
                     "locator": "line 1", "notes": "Synthetic supplied text."}],
        "people": [{"id": "P1", "label": "Invented narrator", "identity": "source-bound", "notes": "Named speaker."},
                   {"id": "P2", "label": "Unnamed custodian", "identity": "unnamed-position", "notes": "Reported role only."}],
        "claims": [{"id": "C1", "person_id": "P1", "predicate": "reported_custody", "value": "A photograph was kept.",
                    "related_person_id": None, "basis": "oral", "support": "single-source", "review": "proposed",
                    "source_refs": [{"source_id": "S1", "locator": "line 1"}], "notes": "Reported storage, not authorship."}],
        "hypotheses": [], "searches": [],
        "coverage": [{"item": "S1, line 1", "disposition": "proposed", "target_ids": ["C1"], "reason": "Reported role preserved."}],
        "next_steps": [],
    }


BINARY_PREDICATES = (
    "parent", "mother", "father", "child", "son", "daughter",
    "sibling", "brother", "sister", "spouse", "grandparent", "grandmother", "grandfather", "cousin",
    "parent_of", "mother_of", "father_of", "child_of", "son_of", "daughter_of",
    "sibling_of", "brother_of", "sister_of", "spouse_of", "grandparent_of", "grandmother_of", "grandfather_of",
    "cousin_of", "stepfather_of", "stepmother_of",
)


class HandoffReferenceValidation(unittest.TestCase):
    def assert_validation(self, data, expected):
        before = copy.deepcopy(data)
        self.assertEqual(MODULE.validate(data), expected)
        self.assertEqual(data, before, "Validation must not repair or normalize a result.")

    def test_typed_references_accept_existing_targets_and_empty_groups(self):
        for references in [[], ["P2"], ["P1", "P2"]]:
            with self.subTest(references=references):
                data = sample()
                data["claims"][0]["value"] = {
                    "parent_ids": references, "child_ids": references,
                    "participant_ids": references, "source_id": "S1",
                }
                self.assert_validation(data, [])

    def test_person_arrays_reject_dangling_and_wrong_kind_ids(self):
        for field in ["parent_ids", "child_ids", "participant_ids"]:
            for ident in ["MISSING-PERSON", "S1", "C1", "", " \t "]:
                with self.subTest(field=field, ident=ident):
                    data = sample()
                    data["claims"][0]["value"] = {field: ["P1", ident]}
                    self.assert_validation(data, [f"claim.value.{field}: dangling person reference"])

    def test_person_arrays_reject_wrong_containers(self):
        for field in ["parent_ids", "child_ids", "participant_ids"]:
            for value in [None, False, True, 0, "P1", {}, {"id": "P1"}]:
                with self.subTest(field=field, value=value):
                    data = sample()
                    data["claims"][0]["value"] = {field: value}
                    self.assert_validation(data, [f"claim.value.{field}: expected array of person IDs"])

    def test_person_arrays_reject_nontext_members_without_crashing(self):
        for field in ["parent_ids", "child_ids", "participant_ids"]:
            for value in [None, False, True, 0, [], ["P1"], {}, {"id": "P1"}]:
                with self.subTest(field=field, value=value):
                    data = sample()
                    data["claims"][0]["value"] = {field: ["P1", value]}
                    self.assert_validation(data, [f"claim.value.{field}: dangling person reference"])

    def test_source_reference_rejects_wrong_kind_dangling_and_wrong_types(self):
        for value in ["MISSING-SOURCE", "P1", "C1", "", " \t ", None, False, True, 0, [], ["S1"], {}, {"id": "S1"}]:
            with self.subTest(value=value):
                data = sample()
                data["claims"][0]["value"] = {"source_id": value}
                self.assert_validation(data, ["claim.value.source_id: dangling source reference"])

    def test_unavailable_source_can_be_referenced_without_claiming_it_was_read(self):
        data = sample()
        source = copy.deepcopy(data["sources"][0])
        source.update(id="S2", kind="photo", access="unavailable", notes="Mentioned photograph; image not supplied.")
        data["sources"].append(source)
        data["claims"][0]["value"] = {"source_id": "S2"}
        self.assert_validation(data, [])

    def test_every_claim_is_checked_without_mutation(self):
        data = sample()
        second = copy.deepcopy(data["claims"][0])
        second.update(id="C2", value={"parent_ids": ["MISSING-PERSON"]})
        data["claims"].append(second)
        self.assert_validation(data, ["claim.value.parent_ids: dangling person reference"])

    def test_binary_relationships_require_and_accept_known_second_participant(self):
        for predicate in BINARY_PREDICATES:
            with self.subTest(predicate=predicate):
                data = sample()
                data["claims"][0].update(predicate=predicate, related_person_id="P2")
                self.assert_validation(data, [])
                data["claims"][0]["related_person_id"] = None
                self.assert_validation(data, ["claim.related_person_id: required for binary relationship"])
                data["claims"][0].pop("related_person_id")
                self.assert_validation(data, ["claim.related_person_id: required for binary relationship"])

    def test_binary_relationship_rejects_wrong_kind_and_malformed_second_participant(self):
        for value in ["S1", "C1", "MISSING-PERSON", "", " \t ", False, 0, [], {}, ["P2"]]:
            with self.subTest(value=value):
                data = sample()
                data["claims"][0].update(predicate="sibling", related_person_id=value)
                self.assert_validation(data, ["claim.related_person_id: dangling reference"])

    def test_unresolved_kinship_term_is_a_mention_without_a_binary_edge(self):
        data = sample()
        data["claims"][0].update(
            person_id="P2", predicate="reported_kinship_term",
            value={"term": "cousin", "second_participant": "not specified"},
            notes="The speaker reported a cousin as custodian without identifying whose cousin.",
        )
        data["coverage"][0].update(disposition="lead", target_ids=["P2", "C1"], reason="Second participant unresolved.")
        self.assert_validation(data, [])

    def test_group_relationship_does_not_require_a_binary_target(self):
        data = sample()
        data["claims"][0].update(predicate="shared_parent_group", value={"parent_ids": ["P1"], "child_ids": ["P2"]})
        self.assert_validation(data, [])

    def test_id_like_prose_and_arbitrary_nested_extension_data_remain_valid(self):
        values = [
            "The inscription literally says NONEXISTENT-PERSON; this is not a link.",
            {"text": "P404 and S404 are literal source text.", "unknown_person_id": "P404"},
            {"quoted_data": {"parent_ids": ["P404"], "source_id": "S404"}},
        ]
        for value in values:
            with self.subTest(value=value):
                data = sample()
                data["claims"][0]["value"] = value
                self.assert_validation(data, [])


if __name__ == "__main__":
    unittest.main()
