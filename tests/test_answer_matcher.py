"""Deterministic scorer — ``ahnexp.evaluate.score_row`` (open_decisions.md #7).

Replaces the old containment `is_correct` characterisation. Every case asserts the
full outcome: one of correct / wrong / abstained / malformed, plus the canonical
value. The nine cases the previous suite flagged as bugs are pinned at the bottom
and now pass.

Pure: no model, no torch, no GPU.

    python -m unittest discover -s tests
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import dataset
from ahnexp.evaluate import SCORER_VERSION, clean_answer, rescore, score_row

# Concrete golds from the generators the run pipeline uses.
NUM = dataset.numerical(0)          # "100000"
TMP = dataset.temporal(1)           # "Person_1"   (foil: Person_2)
ENT = dataset.entity_attribute(2, slot=0)   # "blue"
HOP = dataset.multi_hop(3, slot=0)          # "Google"
CON = dataset.contradictory(4, slot=0)      # new "London", old "Paris"


def outcome(pred: str, gold: str, fact_type: str) -> str:
    r = score_row(pred, gold, fact_type)
    if r["abstained"]:
        return "abstained"
    if r["malformed"]:
        return "malformed"
    return "correct" if r["correct"] else "wrong"


@dataclass(frozen=True)
class Case:
    fact_type: str
    name: str
    prediction: str
    gold: str
    expect: str          # correct | wrong | abstained | malformed
    canonical: str = None  # expected answer_canonical when scoreable


CASES = [
    # ---- numerical -------------------------------------------------------------
    Case("numerical", "bare", "100000", NUM.answer, "correct", "100000"),
    Case("numerical", "full sentence (>4 words)", "Person_0's employee ID is 100000.", NUM.answer, "malformed"),
    Case("numerical", "thousands separator", "100,000", NUM.answer, "correct", "100000"),
    Case("numerical", "trailing punctuation + case", "  100000.  ", NUM.answer, "correct", "100000"),
    Case("numerical", "wrong number", "999999", NUM.answer, "wrong", "999999"),
    Case("numerical", "off by one", "100001", NUM.answer, "wrong", "100001"),
    Case("numerical", "wrong asserted, gold also named", "100685 not 100000", NUM.answer, "malformed"),
    Case("numerical", "two competing numbers", "100000 or 100137", NUM.answer, "malformed"),
    Case("numerical", "no digits", "the employee identifier", NUM.answer, "malformed"),
    # ---- temporal -------------------------------------------------------------
    Case("temporal", "bare", "Person_1", TMP.answer, "correct", "person_1"),
    Case("temporal", "space for underscore", "Person 1", TMP.answer, "correct", "person_1"),
    Case("temporal", "lowercase + period", "person_1.", TMP.answer, "correct", "person_1"),
    Case("temporal", "the foil", "Person_2", TMP.answer, "wrong", "person_2"),
    Case("temporal", "wrong order, both named", "Person_2 arrived before Person_1", TMP.answer, "malformed"),
    Case("temporal", "question echoed", TMP.question, TMP.answer, "malformed"),
    Case("temporal", "hallucinated entity", "Person_9", TMP.answer, "wrong", "person_9"),
    # ---- entity-attribute ---------------------------------------------------------
    Case("entity-attribute", "bare", "blue", ENT.answer, "correct", "blue"),
    Case("entity-attribute", "capitalised + period", "Blue.", ENT.answer, "correct", "blue"),
    Case("entity-attribute", "quoted", '"blue"', ENT.answer, "correct", "blue"),
    Case("entity-attribute", "wrong colour", "green", ENT.answer, "wrong", "green"),
    Case("entity-attribute", "negated gold", "not blue", ENT.answer, "malformed"),
    Case("entity-attribute", "gold + another colour", "not blue, it's green", ENT.answer, "malformed"),
    Case("entity-attribute", "bare mention in prose", "Person_2's favorite color is blue", ENT.answer, "malformed"),
    Case("entity-attribute", "adjacent word form", "bluish", ENT.answer, "malformed"),
    # ---- multi-hop -------------------------------------------------------------
    Case("multi-hop", "bare", "Google", HOP.answer, "correct", "google"),
    Case("multi-hop", "lowercase", "google", HOP.answer, "correct", "google"),
    Case("multi-hop", "different company", "Amazon", HOP.answer, "wrong", "amazon"),
    Case("multi-hop", "intermediate person", "Person_4", HOP.answer, "malformed"),
    Case("multi-hop", "wrong company asserted, gold named", "Person_4 works for Amazon, not Google", HOP.answer, "malformed"),
    # ---- contradictory --------------------------------------------------------
    Case("contradictory", "bare new city", "London", CON.answer, "correct", "london"),
    Case("contradictory", "uppercase + padding", "  LONDON  ", CON.answer, "correct", "london"),
    Case("contradictory", "superseded city", "Paris", CON.answer, "wrong", "paris"),
    Case("contradictory", "both cities named", "lived in Paris, now London", CON.answer, "malformed"),
    Case("contradictory", "unrelated city", "Berlin", CON.answer, "wrong", "berlin"),
    # ---- abstention ---------------------------------------------------------------
    Case("numerical", "exact idk", "I don't know", NUM.answer, "abstained"),
    Case("entity-attribute", "exact idk lowercase", "i don't know", ENT.answer, "abstained"),
    Case("multi-hop", "idk in prose is not abstention", "I don't know, maybe Google", HOP.answer, "malformed"),
]


def _mk(case: Case):
    def test(self):
        got = outcome(case.prediction, case.gold, case.fact_type)
        self.assertEqual(
            got, case.expect,
            f"\n  {case.fact_type} / {case.name}"
            f"\n  prediction : {case.prediction!r}"
            f"\n  gold       : {case.gold!r}"
            f"\n  expected   : {case.expect}   got: {got}"
            f"\n  full       : {score_row(case.prediction, case.gold, case.fact_type)}",
        )
        if case.canonical is not None and case.expect in ("correct", "wrong"):
            self.assertEqual(
                score_row(case.prediction, case.gold, case.fact_type)["answer_canonical"],
                case.canonical,
            )
    return test


class TestScorer(unittest.TestCase):
    pass


for _i, _c in enumerate(CASES):
    _slug = f"{_c.fact_type}_{_c.name}".lower()
    _slug = "".join(ch if ch.isalnum() else "_" for ch in _slug)
    setattr(TestScorer, f"test_{_i:02d}_{_slug}"[:90], _mk(_c))


class TestRequiredEquivalences(unittest.TestCase):
    def test_numeric_comma_equivalence(self):
        self.assertEqual(score_row("100,000", "100000", "numerical")["correct"], 1)
        self.assertEqual(score_row("100000", "100,000", "numerical")["correct"], 1)

    def test_person_underscore_space_equivalence(self):
        for pred in ("Person_1", "Person 1", "person 1", "PERSON_1"):
            self.assertEqual(score_row(pred, "Person_1", "temporal")["correct"], 1, pred)

    def test_case_and_terminal_punctuation_ignored(self):
        for pred in ("blue", "Blue", "BLUE.", " blue ", "blue!"):
            self.assertEqual(score_row(pred, "blue", "entity-attribute")["correct"], 1, pred)


class TestRequiredFailures(unittest.TestCase):
    def test_bare_gold_mention_in_prose(self):
        r = score_row("Person_2's favorite color is blue", "blue", "entity-attribute")
        self.assertEqual((r["correct"], r["malformed"]), (0, 1))

    def test_negated_gold(self):
        self.assertEqual(score_row("not blue", "blue", "entity-attribute")["correct"], 0)
        self.assertEqual(score_row("never Google", "Google", "multi-hop")["malformed"], 1)

    def test_question_echo(self):
        r = score_row("Who arrived first, Person_1 or Person_2?", "Person_1", "temporal")
        self.assertEqual((r["correct"], r["malformed"]), (0, 1))

    def test_multiple_competing_candidates_get_no_credit(self):
        for ft, pred, gold in [
            ("numerical", "100000 or 100137", "100000"),
            ("entity-attribute", "blue or green", "blue"),
            ("multi-hop", "Google, not Amazon", "Google"),
            ("contradictory", "Paris then London", "London"),
        ]:
            r = score_row(pred, gold, ft)
            self.assertEqual((r["correct"], r["malformed"]), (0, 1), f"{ft}: {pred!r}")

    def test_superseded_city_not_credited(self):
        self.assertEqual(score_row("Paris", "London", "contradictory")["correct"], 0)

    def test_wrong_temporal_entity(self):
        self.assertEqual(score_row("Person_2", "Person_1", "temporal")["correct"], 0)


class TestExactAbstention(unittest.TestCase):
    def test_exact_only(self):
        self.assertEqual(score_row("I don't know", "blue", "entity-attribute")["abstained"], 1)
        self.assertEqual(score_row("i do not know", "blue", "entity-attribute")["abstained"], 1)

    def test_substring_is_not_abstention(self):
        # "unknown" inside a longer string must not trigger abstention.
        r = score_row("the unknown soldier statue", "blue", "entity-attribute")
        self.assertEqual(r["abstained"], 0)


class TestRawPreservationAndRescore(unittest.TestCase):
    def test_score_row_reads_only_the_first_line_but_does_not_mutate(self):
        raw = "blue\nthis explanation should be ignored by the scorer"
        before = raw
        r = score_row(raw, "blue", "entity-attribute")
        self.assertEqual(r["correct"], 1)
        self.assertEqual(raw, before)  # caller keeps the full string verbatim
        self.assertEqual(clean_answer(raw), "blue")

    def test_rescore_is_deterministic_and_pure(self):
        import pandas as pd
        df = pd.DataFrame([
            dict(prediction="100,000", gold="100000", fact_type="numerical"),
            dict(prediction="not blue", gold="blue", fact_type="entity-attribute"),
            dict(prediction="Person 1", gold="Person_1", fact_type="temporal"),
            dict(prediction="London.", gold="London", fact_type="contradictory"),
        ])
        a = rescore(df)
        b = rescore(df)
        self.assertTrue(a.equals(b))
        self.assertEqual(list(a["correct"]), [1, 0, 1, 1])
        self.assertEqual(list(a["malformed"]), [0, 1, 0, 0])
        self.assertTrue((a["scorer_version"] == SCORER_VERSION).all())
        self.assertIn("prediction", a.columns)  # raw kept

    def test_rescore_rejects_frame_without_raw(self):
        import pandas as pd
        with self.assertRaises(ValueError):
            rescore(pd.DataFrame([dict(gold="blue", fact_type="entity-attribute")]))


class TestFormerlyFailingCases(unittest.TestCase):
    """The nine the containment matcher got wrong. All deterministic now."""

    def test_all_nine(self):
        nine = [
            ("numerical", "100685 not 100000", "100000", "malformed"),
            ("numerical", "100,000", "100000", "correct"),
            ("temporal", "Person 1", "Person_1", "correct"),
            ("temporal", "Person_2 arrived before Person_1", "Person_1", "malformed"),
            ("temporal", "Who arrived first, Person_1 or Person_2?", "Person_1", "malformed"),
            ("entity-attribute", "not blue, it's green", "blue", "malformed"),
            ("multi-hop", "Person_4 works for Amazon, not Google", "Google", "malformed"),
            ("contradictory", "now Paris, used to be London", "London", "malformed"),
            ("contradictory", "London then back to Paris", "London", "malformed"),
        ]
        for ft, pred, gold, expect in nine:
            self.assertEqual(outcome(pred, gold, ft), expect, f"{ft}: {pred!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
