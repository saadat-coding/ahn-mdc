"""Prompt construction, chat templating, and the three token-distance quantities
(open_decisions.md #1 / #7). No GPU; the model is never loaded.

    python -m unittest discover -s tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import config, dataset, schema

FACT_TYPES = ("numerical", "temporal", "entity-attribute", "multi-hop", "contradictory")


class _PlainTokenizer:
    """Whitespace tokenizer, NO chat template -> body passes through unchanged."""

    def __call__(self, text, **_):
        return {"input_ids": text.split()}

    def __len__(self):
        return 50_000


class _TemplatedTokenizer(_PlainTokenizer):
    """Whitespace tokenizer that DOES wrap content, to exercise the template path."""

    chat_template = "stub"

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        body = messages[0]["content"]
        return f"<<user>> {body} <<end>>\n<<assistant>>"


class TestPromptConstruction(unittest.TestCase):
    def setUp(self):
        self.items = dataset.generate_items(20, seed=0, pool_size=60)

    def test_answer_hint_and_abstention_present_no_option_set_leaked(self):
        hints = config.facts()["types"]
        banned = [c.lower() for c in (*dataset.COLORS, *dataset.COMPANIES,
                                      *dataset.CITIES_FROM, *dataset.CITIES_TO)]
        for it in self.items:
            tj = dataset.build_trajectory(it, _PlainTokenizer(), tokens_after_target=10, seed=0)
            hint = hints[it.fact.fact_type]["answer_hint"]
            self.assertIn(hint, tj["prompt"])
            self.assertIn("I don't know", tj["prompt"])
            # the instruction text itself must not enumerate the closed answer set
            instruction = tj["prompt"].split("Question:")[1].split(it.fact.question)[1]
            leaked = [w for w in banned if f" {w} " in f" {instruction.lower()} " or w == it.fact.answer.lower()]
            leaked = [w for w in leaked if w != it.fact.answer.lower()]
            self.assertEqual(leaked, [], f"instruction leaks options: {leaked}")

    def test_every_fact_type_has_a_hint(self):
        for ft in FACT_TYPES:
            self.assertIn("answer_hint", config.facts()["types"][ft])


class TestChatTemplate(unittest.TestCase):
    def setUp(self):
        self.items = dataset.generate_items(10, seed=0, pool_size=60)

    def test_plain_tokenizer_passes_body_through(self):
        tj = dataset.build_trajectory(self.items[0], _PlainTokenizer(), tokens_after_target=8, seed=0)
        self.assertFalse(tj["prompt"].startswith("<<user>>"))
        self.assertTrue(tj["prompt"].startswith("You are given a set of factual statements."))

    def test_templated_tokenizer_wraps_body(self):
        tj = dataset.build_trajectory(self.items[0], _TemplatedTokenizer(), tokens_after_target=8, seed=0)
        self.assertTrue(tj["prompt"].startswith("<<user>>"))
        self.assertIn("<<assistant>>", tj["prompt"])
        self.assertIn(self.items[0].fact.text, tj["prompt"])

    def test_real_qwen_tokenizer_uses_its_chat_template(self):
        try:
            from transformers import AutoTokenizer
            tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
        except Exception as exc:  # offline / not installed
            self.skipTest(f"Qwen tokenizer unavailable: {exc}")
        self.assertIsNotNone(tok.chat_template)
        tj = dataset.build_trajectory(self.items[2], tok, tokens_after_target=64, seed=1)
        self.assertTrue(tj["prompt"].startswith("<|im_start|>"))
        self.assertIn("<|im_start|>assistant", tj["prompt"])
        self.assertIn(self.items[2].fact.text, tj["prompt"])


class TestTokenAccounting(unittest.TestCase):
    """distractor tokens  <  total model-input tokens after target;  boundary uses the latter."""

    def setUp(self):
        self.items = dataset.generate_items(15, seed=0, pool_size=400)

    def test_three_quantities_distinct_and_ordered(self):
        tok = _TemplatedTokenizer()
        for it in self.items[:5]:
            overheads = set()
            for pressure in (0, 16, 64, 200):
                tj = dataset.build_trajectory(it, tok, tokens_after_target=pressure, seed=0)
                self.assertLessEqual(tj["tokens_after_target"], tj["model_tokens_after_target"])
                self.assertLessEqual(tj["model_tokens_after_target"], tj["context_tokens"])
                overheads.add(tj["model_tokens_after_target"] - tj["tokens_after_target"])
            # for one trial the question/instruction/template block is fixed, so the
            # offset between the two counts is constant across the pressure sweep and
            # curve shapes are untouched; only the exact/recurrent boundary shifts.
            self.assertLessEqual(max(overheads) - min(overheads), 2,
                                 f"{it.item_id}: overhead not ~constant across pressure: {overheads}")

    def test_h1_iv_unchanged_by_prompt_format(self):
        # tokens_after_target must equal the distractor-block token count, whether or
        # not a chat template is applied.
        for pressure in (0, 32, 96):
            plain = dataset.build_trajectory(self.items[3], _PlainTokenizer(),
                                             tokens_after_target=pressure, seed=0)
            templ = dataset.build_trajectory(self.items[3], _TemplatedTokenizer(),
                                             tokens_after_target=pressure, seed=0)
            self.assertEqual(plain["tokens_after_target"], templ["tokens_after_target"])

    def test_memory_condition_boundary_uses_model_tokens(self):
        import pandas as pd
        df = pd.DataFrame([
            # target still in window by distractors alone, but the question block pushes it out
            dict(item_id="x", architecture="a", seed=0,
                 tokens_after_target=250, model_tokens_after_target=300, sliding_window=256),
            dict(item_id="y", architecture="a", seed=0,
                 tokens_after_target=250, model_tokens_after_target=250, sliding_window=256),
        ])
        out = schema.derive_memory_condition(df)
        self.assertEqual(list(out["memory_condition"]), ["recurrent_memory", "exact_memory"])

    def test_memory_condition_falls_back_when_model_tokens_absent(self):
        import pandas as pd
        df = pd.DataFrame([dict(item_id="x", architecture="a", seed=0,
                                tokens_after_target=300, sliding_window=256)])
        out = schema.derive_memory_condition(df)
        self.assertEqual(out["memory_condition"].iloc[0], "recurrent_memory")


class TestGenerationStopStringApi(unittest.TestCase):
    """stop_strings must be a real feature of the installed transformers, not assumed."""

    def test_stop_strings_supported(self):
        try:
            import transformers
            from transformers import GenerationConfig
        except Exception as exc:
            self.skipTest(f"transformers unavailable: {exc}")
        self.assertTrue(transformers.__version__.startswith("4.51"),
                        f"pinned 4.51 expected, got {transformers.__version__}")
        self.assertTrue(hasattr(GenerationConfig(), "stop_strings"))
        src_ok = False
        try:
            import inspect
            from transformers.generation.utils import GenerationMixin
            src_ok = "StopStringCriteria" in inspect.getsource(GenerationMixin._get_stopping_criteria)
        except Exception:
            src_ok = None  # torch not importable here; the attribute check above still stands
        if src_ok is not None:
            self.assertTrue(src_ok)

    def test_config_declares_newline_stop(self):
        gen = config.experiment()["models"]["matched"]["generation"]
        self.assertEqual(gen.get("stop_strings"), ["\n"])
        self.assertEqual(gen["max_new_tokens"], 12)  # unchanged for now (open_decisions.md #7 item 5)

    def test_run_trial_passes_tokenizer_with_stop_strings(self):
        import inspect
        from ahnexp import evaluate
        src = inspect.getsource(evaluate.run_trial)
        self.assertIn("stop_strings", src)
        self.assertIn('"tokenizer": tokenizer', src)
        self.assertIn("n_new_tokens", src)


class TestSchemaColumns(unittest.TestCase):
    def test_new_columns_registered(self):
        names = {c.name for c in schema.COLUMNS}
        for expected in ("malformed", "answer_canonical", "n_new_tokens", "model_tokens_after_target"):
            self.assertIn(expected, names)
        self.assertIn("prediction", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
