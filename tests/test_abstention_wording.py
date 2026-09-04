"""Shared abstention-clause wording (open_decisions.md #7).

The clause was changed from "If the answer is not stated above, reply with
exactly: I don't know" to "If the answer cannot be determined from the statements
above, reply with exactly: I don't know" after the staged pilot showed the old
wording was read as "verbatim span only", which broke `temporal` (gold entailed,
not stated): 25% exact accuracy / 75% abstention vs 100% for the four verbatim
types.

This guards: identical clause for every fact type, the old clause gone, the
scorer's "I don't know" recognition unchanged, prompt/template/token accounting
still valid. No GPU.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import config, dataset, evaluate

_NEW_CLAUSE = "If the answer cannot be determined from the statements above, reply with exactly: I don't know"
_OLD_CLAUSE = "If the answer is not stated above"
_FACT_TYPES = ("numerical", "temporal", "entity-attribute", "multi-hop", "contradictory")


class _PlainTokenizer:
    def __call__(self, text, **_):
        return {"input_ids": text.split()}

    def __len__(self):
        return 50_000


class _TemplatedTokenizer(_PlainTokenizer):
    chat_template = "stub"

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return f"<<user>> {messages[0]['content']} <<end>>\n<<assistant>>"


class TestAbstentionClause(unittest.TestCase):
    def setUp(self):
        self.items = dataset.generate_items(10, seed=0, pool_size=400)  # 2 per fact type

    def test_shared_prompt_carries_only_the_new_clause(self):
        self.assertIn(_NEW_CLAUSE, dataset._PROMPT)
        self.assertNotIn(_OLD_CLAUSE, dataset._PROMPT)
        self.assertNotIn("not stated above", dataset._PROMPT)

    def test_every_fact_type_gets_the_identical_new_clause(self):
        seen_types = set()
        for it in self.items:
            for pressure in (0, 128, 512):
                tj = dataset.build_trajectory(it, _PlainTokenizer(),
                                              tokens_after_target=pressure, seed=0)
                self.assertIn(_NEW_CLAUSE, tj["prompt"])
                self.assertNotIn(_OLD_CLAUSE, tj["prompt"])
                self.assertNotIn("not stated above", tj["prompt"])
                # exactly one abstention clause, identical text, last line of the body
                self.assertEqual(tj["prompt"].count("reply with exactly: I don't know"), 1)
            seen_types.add(it.fact.fact_type)
        self.assertEqual(seen_types, set(_FACT_TYPES))

    def test_abstention_token_string_is_unchanged(self):
        # the scorer keys on the literal phrase; it must survive verbatim in the prompt
        for it in self.items:
            tj = dataset.build_trajectory(it, _PlainTokenizer(), tokens_after_target=0, seed=0)
            self.assertIn("I don't know", tj["prompt"])

    def test_no_option_set_leaked_by_the_new_clause(self):
        banned = [c.lower() for c in (*dataset.COLORS, *dataset.COMPANIES,
                                      *dataset.CITIES_FROM, *dataset.CITIES_TO)]
        for it in self.items:
            tj = dataset.build_trajectory(it, _PlainTokenizer(), tokens_after_target=10, seed=0)
            instruction = tj["prompt"].split("Question:")[1].split(it.fact.question)[1]
            leaked = [w for w in banned
                      if f" {w} " in f" {instruction.lower()} " and w != it.fact.answer.lower()]
            self.assertEqual(leaked, [], f"{it.item_id}: instruction leaks {leaked}")


class TestScorerAbstentionUnchanged(unittest.TestCase):
    def test_i_dont_know_scores_as_abstention_for_every_fact_type(self):
        golds = {"numerical": "100000", "temporal": "Person_1", "entity-attribute": "blue",
                 "multi-hop": "Google", "contradictory": "London"}
        for ft in _FACT_TYPES:
            out = evaluate.score_row("I don't know", golds[ft], ft)
            self.assertEqual(out, {"correct": 0, "abstained": 1, "malformed": 0,
                                   "answer_canonical": ""})

    def test_abstention_synonyms_and_casing_still_recognised(self):
        for text in ("I don't know", "i dont know", "  I don't know.  ", "I do not know",
                     "unknown", "cannot be determined"):
            out = evaluate.score_row(text, "blue", "entity-attribute")
            self.assertEqual((out["abstained"], out["malformed"], out["correct"]), (1, 0, 0))

    def test_a_real_answer_is_still_scored_normally(self):
        self.assertEqual(evaluate.score_row("blue", "blue", "entity-attribute")["correct"], 1)
        self.assertEqual(evaluate.score_row("Person_1", "Person_1", "temporal")["correct"], 1)


class TestPromptStructureStillValid(unittest.TestCase):
    def setUp(self):
        self.items = dataset.generate_items(10, seed=0, pool_size=400)

    def test_plain_and_templated_paths_intact(self):
        plain = dataset.build_trajectory(self.items[1], _PlainTokenizer(),
                                         tokens_after_target=64, seed=0)
        self.assertTrue(plain["prompt"].startswith("You are given a set of factual statements."))
        templ = dataset.build_trajectory(self.items[1], _TemplatedTokenizer(),
                                         tokens_after_target=64, seed=0)
        self.assertTrue(templ["prompt"].startswith("<<user>>"))
        self.assertIn("<<assistant>>", templ["prompt"])
        self.assertIn(self.items[1].fact.text, templ["prompt"])
        self.assertIn(_NEW_CLAUSE, templ["prompt"])

    def test_token_accounting_ordering_holds(self):
        tok = _TemplatedTokenizer()
        for it in self.items[:5]:
            offsets = set()
            for pressure in (0, 128, 256, 512, 768):
                tj = dataset.build_trajectory(it, tok, tokens_after_target=pressure, seed=0)
                self.assertLessEqual(tj["tokens_after_target"], tj["model_tokens_after_target"])
                self.assertLessEqual(tj["model_tokens_after_target"], tj["context_tokens"])
                self.assertEqual(tj["requested_tokens_after_target"], pressure)
                offsets.add(tj["model_tokens_after_target"] - tj["tokens_after_target"])
            # the question/instruction/template block is fixed per item, so the offset
            # between realised distractor tokens and model-input-after-target tokens is
            # ~constant across the sweep -> the new clause did not distort curve shapes
            self.assertLessEqual(max(offsets) - min(offsets), 2, f"{it.item_id}: {offsets}")

    def test_h1_independent_variable_untouched_by_the_wording(self):
        for pressure in (0, 128, 512):
            plain = dataset.build_trajectory(self.items[3], _PlainTokenizer(),
                                             tokens_after_target=pressure, seed=0)
            templ = dataset.build_trajectory(self.items[3], _TemplatedTokenizer(),
                                             tokens_after_target=pressure, seed=0)
            self.assertEqual(plain["tokens_after_target"], templ["tokens_after_target"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
