"""Deterministic scorer self-tests, not model evaluation. No network or models.

Fixtures are copied in memory; negative tests never rewrite the JSONL files.
CLI output-file behavior is mocked so tests do not create evaluation artifacts.
"""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data" / "synthetic" / "smoke"
sys.path.insert(0, str(SCRIPTS))

from validate_dataset import Row, ValidationError, load_jsonl, validate_dataset
import score_eval as scorer


class EvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = [
            load_jsonl(DATA / name) for name in (
                "manifests.jsonl", "blocks.jsonl", "cases.jsonl",
                "predictions.demo.jsonl", "judgments.demo.jsonl",
            )
        ]

    def setUp(self):
        self.manifests, self.blocks, self.cases, self.predictions, self.judgments = deepcopy(self.fixtures)

    def validate(self):
        return validate_dataset(self.manifests, self.blocks, self.cases)

    def score(self):
        return scorer.score_eval(self.cases, self.predictions, self.judgments)

    def score_only(self, index):
        return scorer.score_eval(
            [self.cases[index]], [self.predictions[index]], [self.judgments[index]]
        )

    def test_normal_dataset_passes(self):
        result = self.validate()
        self.assertTrue(result["valid"])
        self.assertEqual((result["manifest_count"], result["block_count"], result["case_count"]), (3, 8, 4))
        self.assertEqual(result["dataset_kind"], "synthetic")

    def test_demo_all_quotes_exist_and_content_is_marked_synthetic(self):
        blocks = {row.data["block_id"]: row.data for row in self.blocks}
        for row in self.manifests:
            self.assertIn("合成", row.data["title"])
        for block in blocks.values():
            self.assertIn("合成", block["text"])
        for row in self.cases:
            self.assertIn("合成", row.data["query"])
        for rows, field in ((self.cases, "gold_items"), (self.predictions, "items")):
            for row in rows:
                for item in row.data[field]:
                    self.assertIn("合成", item["text"])
                    for evidence in item["evidence"]:
                        self.assertIn(evidence["quote"], blocks[evidence["block_id"]]["text"])
        measures = self.cases[0].data["gold_items"]
        self.assertEqual(len(measures), 10)
        self.assertEqual(
            {blocks[item["evidence"][0]["block_id"]]["block_type"] for item in measures},
            {"text", "table", "appendix"},
        )

    def test_duplicate_block_id(self):
        self.blocks.append(Row(deepcopy(self.blocks[0].data), "blocks.jsonl", 9))
        with self.assertRaisesRegex(ValidationError, r"blocks.jsonl:9: block_id: duplicate"):
            self.validate()

    def test_duplicate_block_order_in_version(self):
        self.blocks[1].data["block_order"] = 0
        with self.assertRaisesRegex(ValidationError, "block_order: duplicate"):
            self.validate()

    def test_duplicate_manifest_key(self):
        self.manifests.append(deepcopy(self.manifests[0]))
        with self.assertRaisesRegex(ValidationError, "duplicate manifest key"):
            self.validate()

    def test_duplicate_case_and_gold_ids(self):
        self.cases.append(deepcopy(self.cases[0]))
        with self.assertRaisesRegex(ValidationError, "case_id: duplicate"):
            self.validate()
        self.cases.pop()
        self.cases[0].data["gold_items"][1]["item_id"] = "m01"
        with self.assertRaisesRegex(ValidationError, "item_id: duplicate"):
            self.validate()

    def test_invalid_parent(self):
        for parent_id, message in (
            ("unknown-block", "unknown parent"),
            ("syn-standard-v1-heading", "same document version"),
            ("syn-measures-body", "own parent"),
        ):
            with self.subTest(parent_id=parent_id):
                self.blocks[1].data["parent_id"] = parent_id
                with self.assertRaisesRegex(ValidationError, message):
                    self.validate()

    def test_parent_cycle(self):
        self.blocks[0].data["parent_id"] = "syn-measures-body"
        with self.assertRaisesRegex(ValidationError, "parent cycle"):
            self.validate()

    def test_unknown_block_manifest(self):
        self.blocks[0].data["doc_id"] = "not-a-document"
        with self.assertRaisesRegex(ValidationError, "unknown manifest key"):
            self.validate()

    def test_manifest_without_blocks(self):
        self.blocks = self.blocks[:-2]
        with self.assertRaisesRegex(ValidationError, "has no blocks"):
            self.validate()

    def test_quote_not_in_source(self):
        self.cases[0].data["gold_items"][0]["evidence"][0]["quote"] = "[合成演示] 原文没有的句子"
        with self.assertRaisesRegex(ValidationError, r"cases.jsonl:1: gold_items\[0\].evidence\[0\].quote"):
            self.validate()

    def test_unknown_evidence_block(self):
        self.cases[0].data["gold_items"][0]["evidence"][0]["block_id"] = "unknown"
        with self.assertRaisesRegex(ValidationError, "unknown block"):
            self.validate()

    def test_expired_version_and_boundary(self):
        for as_of in ("2025-01-01", "2025-06-01"):
            with self.subTest(as_of=as_of):
                self.cases[2].data["scope"]["as_of"] = as_of
                with self.assertRaisesRegex(ValidationError, "not effective"):
                    self.validate()

    def test_historical_version_and_effective_boundary_pass(self):
        for as_of in ("2023-02-01", "2024-12-31"):
            with self.subTest(as_of=as_of):
                self.cases[2].data["scope"]["as_of"] = as_of
                self.assertTrue(self.validate()["valid"])
        self.cases[1].data["scope"]["as_of"] = "2025-01-01"
        self.assertTrue(self.validate()["valid"])

    def test_future_version_rejected(self):
        self.cases[1].data["scope"]["as_of"] = "2024-12-31"
        with self.assertRaisesRegex(ValidationError, "not effective"):
            self.validate()

    def test_illegal_calendar_dates_and_order(self):
        for value in ("2025-02-30", "2025-1-01", "2025-01-01T00:00:00", "0000-01-01"):
            with self.subTest(value=value):
                self.cases[0].data["scope"]["as_of"] = value
                with self.assertRaisesRegex(ValidationError, "scope.as_of"):
                    self.validate()
        self.cases = deepcopy(self.fixtures[2])
        self.manifests[0].data["published_at"] = "2024-02-30"
        with self.assertRaisesRegex(ValidationError, "published_at"):
            self.validate()
        self.manifests = deepcopy(self.fixtures[0])
        self.manifests[0].data["repealed_at"] = "2024-02-01"
        with self.assertRaisesRegex(ValidationError, "repealed_at"):
            self.validate()

    def test_effective_date_may_precede_publication(self):
        self.manifests[0].data["published_at"] = "2024-03-01"
        self.assertTrue(self.validate()["valid"])

    def test_version_id_must_identify_one_document(self):
        duplicate = deepcopy(self.manifests[0])
        duplicate.data["doc_id"] = "another-logical-document"
        self.manifests.append(duplicate)
        with self.assertRaisesRegex(ValidationError, "version_id: must be globally unique"):
            self.validate()

    def test_scope_region_mixing_rejected(self):
        self.cases[0].data["scope"]["region_code"] = "SYN-B"
        with self.assertRaisesRegex(ValidationError, "scope.region_code"):
            self.validate()

    def test_unknown_and_duplicate_scope_versions(self):
        for versions, message in (
            (["unknown-version"], "unknown version"),
            (["syn-measures-a-v1", "syn-measures-a-v1"], "duplicate version ID"),
        ):
            with self.subTest(versions=versions):
                self.cases[0].data["scope"]["version_ids"] = versions
                with self.assertRaisesRegex(ValidationError, message):
                    self.validate()

    def test_gold_version_must_be_in_scope(self):
        self.cases[1].data["gold_items"][0]["evidence"] = deepcopy(
            self.cases[2].data["gold_items"][0]["evidence"]
        )
        with self.assertRaisesRegex(ValidationError, "outside scope.version_ids"):
            self.validate()

    def test_field_types_and_enums(self):
        for field, value in (
            ("block_order", True), ("block_order", -1), ("page_no", 0),
            ("page_no", 1.5), ("text", ""), ("block_type", "pdf"),
            ("table_html", 3), ("parent_id", []),
        ):
            with self.subTest(field=field, value=value):
                self.blocks = deepcopy(self.fixtures[1])
                self.blocks[0].data[field] = value
                with self.assertRaisesRegex(ValidationError, field):
                    self.validate()

    def test_required_fields_and_gold_shape(self):
        del self.manifests[0].data["repealed_at"]
        with self.assertRaisesRegex(ValidationError, "repealed_at: missing"):
            self.validate()
        self.manifests = deepcopy(self.fixtures[0])
        self.cases[3].data["gold_items"] = deepcopy(self.cases[2].data["gold_items"])
        with self.assertRaisesRegex(ValidationError, "unanswerable case"):
            self.validate()
        self.cases = deepcopy(self.fixtures[2])
        self.cases[0].data["gold_items"][0]["evidence"] = []
        with self.assertRaisesRegex(ValidationError, "requires literal evidence"):
            self.validate()

    def test_mixed_dataset_kinds_rejected_within_and_across_files(self):
        self.manifests[1].data["dataset_kind"] = "public"
        with self.assertRaisesRegex(ValidationError, "mixed dataset kinds"):
            self.validate()
        self.manifests = deepcopy(self.fixtures[0])
        for row in self.blocks:
            row.data["dataset_kind"] = "public"
        with self.assertRaisesRegex(ValidationError, "mixed dataset kinds"):
            self.validate()
        self.predictions[1].data["dataset_kind"] = "public"
        with self.assertRaisesRegex(ValidationError, "mixed dataset kinds"):
            self.score()
        self.predictions = deepcopy(self.fixtures[3])
        self.judgments[0].data["dataset_kind"] = "public"
        with self.assertRaisesRegex(ValidationError, "mixed dataset kinds"):
            self.score()

    def test_public_marker_supported_but_not_certified(self):
        # Merely exercises the alternative marker; these remain synthetic fixtures.
        for rows in (self.manifests, self.blocks, self.cases, self.predictions, self.judgments):
            for row in rows:
                row.data["dataset_kind"] = "public"
        self.assertEqual(self.validate()["dataset_kind"], "public")
        result = self.score()
        self.assertEqual(result["dataset_kind"], "public")
        self.assertIs(result["is_model_benchmark"], False)

    def test_private_marker_rejected(self):
        self.manifests[0].data["dataset_kind"] = "private"
        with self.assertRaisesRegex(ValidationError, "only synthetic or public"):
            self.validate()

    def test_prediction_case_set_must_match(self):
        self.predictions.pop()
        with self.assertRaisesRegex(ValidationError, "missing cases.*syn-city-b-no-answer"):
            self.score()

    def test_judgment_case_set_must_match(self):
        self.judgments.pop()
        with self.assertRaisesRegex(ValidationError, "missing cases"):
            self.score()

    def test_unknown_and_duplicate_prediction_cases(self):
        self.predictions[0].data["case_id"] = "extra-case"
        with self.assertRaisesRegex(ValidationError, "unknown case ID"):
            self.score()
        self.predictions = deepcopy(self.fixtures[3])
        self.predictions.append(deepcopy(self.predictions[0]))
        with self.assertRaisesRegex(ValidationError, "duplicate case ID"):
            self.score()

    def test_duplicate_prediction_id(self):
        self.predictions[0].data["items"][1]["pred_id"] = "p01"
        with self.assertRaisesRegex(ValidationError, "duplicate prediction ID"):
            self.score()

    def test_missing_judgment_never_silently_skipped(self):
        self.judgments[0].data["items"].pop()
        with self.assertRaisesRegex(ValidationError, "missing judgments.*p-extra"):
            self.score()

    def test_duplicate_and_unknown_judgment_ids(self):
        self.judgments[0].data["items"].append(deepcopy(self.judgments[0].data["items"][0]))
        with self.assertRaisesRegex(ValidationError, "duplicate judgment"):
            self.score()
        self.judgments = deepcopy(self.fixtures[4])
        self.judgments[0].data["items"][0]["pred_id"] = "unknown"
        with self.assertRaisesRegex(ValidationError, "unknown prediction ID"):
            self.score()

    def test_illegal_judgment(self):
        for updates, message in (
            ({"matched_gold_id": None}, "requires a valid gold ID"),
            ({"matched_gold_id": "limit-history"}, "unknown gold ID"),
            ({"wrong_version": True}, "cannot coexist"),
            ({"correct": 1}, "expected bool"),
            ({"citation_supported": "true"}, "expected bool"),
            ({"wrong_version": None}, "expected bool"),
        ):
            with self.subTest(updates=updates):
                self.judgments = deepcopy(self.fixtures[4])
                self.judgments[0].data["items"][0].update(updates)
                with self.assertRaisesRegex(ValidationError, message):
                    self.score()

    def test_missing_judgment_flag_rejected(self):
        del self.judgments[0].data["items"][0]["correct"]
        with self.assertRaisesRegex(ValidationError, "correct: missing"):
            self.score()

    def test_supported_requires_evidence(self):
        self.predictions[0].data["items"][0]["evidence"] = []
        with self.assertRaisesRegex(ValidationError, "no evidence"):
            self.score()

    def test_no_answer_error_or_partial_is_not_correct(self):
        self.predictions[3].data["items"] = []
        self.judgments[3].data["items"] = []
        for status, expected in (("error", 0.0), ("partial", 0.0), ("complete", 1.0)):
            with self.subTest(status=status):
                self.predictions[3].data["status"] = status
                result = self.score_only(3)
                self.assertEqual(result["metrics"]["unanswerable_accuracy"], expected)
                self.assertEqual(result["metrics"]["fully_correct_rate"], expected)
                for metric in ("micro_recall", "macro_recall", "precision", "full_coverage_rate", "citation_support_rate", "wrong_version_rate"):
                    self.assertIsNone(result["metrics"][metric])

    def test_failure_or_partial_keeps_recall_but_not_full_coverage(self):
        for status in ("partial", "error"):
            with self.subTest(status=status):
                self.predictions[2].data["status"] = status
                result = self.score_only(2)
                self.assertEqual(result["metrics"]["micro_recall"], 1.0)
                self.assertEqual(result["metrics"]["precision"], 1.0)
                self.assertEqual(result["metrics"]["full_coverage_rate"], 0.0)
                self.assertEqual(result["metrics"]["fully_correct_rate"], 0.0)

    def test_duplicate_answer_cannot_raise_recall(self):
        prediction = deepcopy(self.predictions[2].data["items"][0])
        judgment = deepcopy(self.judgments[2].data["items"][0])
        prediction["pred_id"] = judgment["pred_id"] = "duplicate-output"
        self.predictions[2].data["items"].append(prediction)
        self.judgments[2].data["items"].append(judgment)
        result = self.score_only(2)
        self.assertEqual(result["metrics"]["micro_recall"], 1.0)
        self.assertEqual(result["metrics"]["macro_recall"], 1.0)
        self.assertEqual(result["metrics"]["precision"], 0.5)
        self.assertEqual(result["metrics"]["full_coverage_rate"], 1.0)
        self.assertEqual(result["metrics"]["fully_correct_rate"], 0.0)
        self.assertEqual(result["counts"]["unique_correct_hits"], 1)

    def test_full_coverage_is_not_fully_correct_with_extra_wrong_item(self):
        self.predictions[2].data["items"].append(deepcopy(self.predictions[0].data["items"][-1]))
        self.judgments[2].data["items"].append(deepcopy(self.judgments[0].data["items"][-1]))
        result = self.score_only(2)
        self.assertEqual(result["metrics"]["full_coverage_rate"], 1.0)
        self.assertEqual(result["metrics"]["fully_correct_rate"], 0.0)
        self.assertEqual(result["metrics"]["precision"], 0.5)

    def test_correct_but_unsupported_is_not_fully_correct(self):
        self.judgments[2].data["items"][0]["citation_supported"] = False
        result = self.score_only(2)
        self.assertEqual(result["metrics"]["micro_recall"], 1.0)
        self.assertEqual(result["metrics"]["fully_correct_rate"], 0.0)
        self.assertEqual(result["metrics"]["citation_support_rate"], 0.0)

    def test_zero_predictions_null_precision_but_recall_zero(self):
        for rows in (self.predictions, self.judgments):
            for row in rows:
                row.data["items"] = []
        result = self.score()
        self.assertEqual(result["metrics"]["micro_recall"], 0.0)
        self.assertEqual(result["metrics"]["macro_recall"], 0.0)
        self.assertIsNone(result["metrics"]["precision"])
        self.assertIsNone(result["metrics"]["citation_support_rate"])
        self.assertIsNone(result["metrics"]["wrong_version_rate"])
        self.assertEqual(result["metrics"]["fully_correct_rate"], 0.25)
        self.assertIn('"precision": null', json.dumps(result, allow_nan=False))

    def test_demo_expected_metrics(self):
        result = self.score()
        expected = {
            "micro_recall": 10 / 12, "macro_recall": (9 / 10 + 0 + 1) / 3,
            "precision": 10 / 13, "full_coverage_rate": 1 / 3,
            "fully_correct_rate": 1 / 4, "unanswerable_accuracy": 0.0,
            "citation_support_rate": 10 / 13, "wrong_version_rate": 1 / 13,
        }
        self.assertEqual(set(result["metrics"]), set(expected))
        for metric, value in expected.items():
            with self.subTest(metric=metric):
                self.assertAlmostEqual(result["metrics"][metric], value)
        self.assertEqual(result["counts"]["gold_items"], 12)
        self.assertEqual(result["counts"]["prediction_items"], 13)
        self.assertEqual(result["counts"]["unique_correct_hits"], 10)
        self.assertEqual(result["dataset_kind"], "synthetic")
        self.assertEqual(result["split"], "smoke")
        self.assertIs(result["is_model_benchmark"], False)
        self.assertEqual(result["scope_note"], scorer.SCOPE_NOTE)
        self.assertIn("不是模型准确率或性能结果", result["scope_note"])
        self.assertNotIn("latency", result["metrics"])
        self.assertNotIn("throughput", result["metrics"])

    def test_cannot_self_certify_benchmark(self):
        for row in self.predictions:
            row.data["is_model_benchmark"] = True
        self.assertIs(self.score()["is_model_benchmark"], False)

    def test_jsonl_diagnostics_and_duplicate_keys(self):
        for content, message in (
            ("{}\nnot-json\n", r"broken.jsonl:2: \$: invalid JSON"),
            ('{"x":1,"x":2}\n', "duplicate JSON key"),
            ('{"x":NaN}\n', "non-JSON numeric constant"),
            ("[]\n", "expected an object"),
            ("\n", "invalid JSON"),
            ("", "empty JSONL file"),
        ):
            with self.subTest(content=content):
                with patch.object(Path, "open", return_value=io.StringIO(content)):
                    with self.assertRaisesRegex(ValidationError, message):
                        load_jsonl(ROOT / "broken.jsonl")

    def test_cli_from_arbitrary_cwd(self):
        commands = (
            ("validate_dataset.py", ["--manifests", str(DATA / "manifests.jsonl"), "--blocks", str(DATA / "blocks.jsonl"), "--cases", str(DATA / "cases.jsonl")]),
            ("score_eval.py", ["--cases", str(DATA / "cases.jsonl"), "--predictions", str(DATA / "predictions.demo.jsonl"), "--judgments", str(DATA / "judgments.demo.jsonl")]),
        )
        for script, args in commands:
            with self.subTest(script=script):
                completed = subprocess.run(
                    [sys.executable, "-B", str(SCRIPTS / script), *args],
                    cwd=ROOT.parent, capture_output=True, text=True, check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(json.loads(completed.stdout)["dataset_kind"], "synthetic")
                if script == "score_eval.py":
                    self.assertIn("不是模型准确率或性能结果", completed.stderr)

    def test_cli_bad_input_returns_nonzero(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "validate_dataset.py"),
             "--manifests", str(DATA / "absent.jsonl"),
             "--blocks", str(DATA / "blocks.jsonl"), "--cases", str(DATA / "cases.jsonl")],
            cwd=ROOT.parent, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("absent.jsonl", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_output_cli_writes_json_without_creating_extra_files(self):
        args = [
            "--cases", str(DATA / "cases.jsonl"),
            "--predictions", str(DATA / "predictions.demo.jsonl"),
            "--judgments", str(DATA / "judgments.demo.jsonl"),
            "--output", str(ROOT / "runs" / "synthetic-smoke-demo.json"),
        ]
        with patch.object(Path, "write_text") as write, redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            self.assertEqual(scorer.main(args), 0)
            write.assert_called_once()
            result = json.loads(write.call_args.args[0])
            self.assertIs(result["is_model_benchmark"], False)
            self.assertAlmostEqual(result["metrics"]["precision"], 10 / 13)

    def test_output_cannot_overwrite_input(self):
        args = [
            "--cases", str(DATA / "cases.jsonl"),
            "--predictions", str(DATA / "predictions.demo.jsonl"),
            "--judgments", str(DATA / "judgments.demo.jsonl"),
            "--output", str(DATA / "cases.jsonl"),
        ]
        with patch.object(Path, "write_text") as write, redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(scorer.main(args), 1)
            write.assert_not_called()
            self.assertIn("must not overwrite an input", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
