"""Score manually adjudicated offline outputs; never call a model or a network.

Run validate_dataset.py first: this CLI has cases/predictions/judgments only,
so it cannot verify prediction quotes against source blocks, source dates, or
whether human judgments are semantically sound. Flags are external judgments,
NOT predictions' self-assessments. No execution provenance is certified here.
All rates are fractions in [0, 1]; a zero denominator produces JSON null.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from validate_dataset import (
    Row, ValidationError, check_evidence, check_kind, load_jsonl, require,
    validate_cases,
)


SCOPE_NOTE = "手工合成样例与手工裁决用于评分器自检；不是模型准确率或性能结果"


def _case_rows(rows: list[Row], cases: dict[str, Row], kind: str) -> dict[str, Row]:
    check_kind(rows, kind)
    indexed: dict[str, Row] = {}
    for row in rows:
        case_id = require(row, row.data, "case_id", str)
        if case_id in indexed:
            row.fail("case_id", f"duplicate case ID {case_id!r}")
        if case_id not in cases:
            row.fail("case_id", f"unknown case ID {case_id!r}")
        indexed[case_id] = row
    missing = set(cases) - set(indexed)
    if missing:
        rows[0].fail("case_id", f"missing cases: {sorted(missing)!r}; keep error/empty cases")
    return indexed


def validate_scoring_inputs(
    case_rows: list[Row], prediction_rows: list[Row], judgment_rows: list[Row],
) -> tuple[dict[str, Row], dict[str, Row], dict[str, dict[str, dict[str, Any]]]]:
    cases = validate_cases(case_rows)
    kind = case_rows[0].data["dataset_kind"]
    predictions = _case_rows(prediction_rows, cases, kind)
    judgments = _case_rows(judgment_rows, cases, kind)
    indexed_judgments: dict[str, dict[str, dict[str, Any]]] = {}
    for case_id, case_row in cases.items():
        prediction_row = predictions[case_id]
        status = require(prediction_row, prediction_row.data, "status", str)
        if status not in {"complete", "partial", "error"}:
            prediction_row.fail("status", "expected complete, partial or error")
        items = require(prediction_row, prediction_row.data, "items", list)
        predicted: dict[str, dict[str, Any]] = {}
        for index, item in enumerate(items):
            field = f"items[{index}]"
            if type(item) is not dict:
                prediction_row.fail(field, "expected dict")
            pred_id = require(prediction_row, item, "pred_id", str, field)
            if pred_id in predicted:
                prediction_row.fail(f"{field}.pred_id", f"duplicate prediction ID {pred_id!r}")
            require(prediction_row, item, "text", str, field)
            check_evidence(prediction_row, item, field)
            predicted[pred_id] = item

        judgment_row = judgments[case_id]
        judgments_list = require(judgment_row, judgment_row.data, "items", list)
        gold_ids = {item["item_id"] for item in case_row.data["gold_items"]}
        judged: dict[str, dict[str, Any]] = {}
        for index, item in enumerate(judgments_list):
            field = f"items[{index}]"
            if type(item) is not dict:
                judgment_row.fail(field, "expected dict")
            pred_id = require(judgment_row, item, "pred_id", str, field)
            if pred_id in judged:
                judgment_row.fail(f"{field}.pred_id", f"duplicate judgment for {pred_id!r}")
            if pred_id not in predicted:
                judgment_row.fail(f"{field}.pred_id", f"unknown prediction ID {pred_id!r}")
            matched = require(judgment_row, item, "matched_gold_id", str, field, nullable=True)
            correct = require(judgment_row, item, "correct", bool, field)
            supported = require(judgment_row, item, "citation_supported", bool, field)
            wrong_version = require(judgment_row, item, "wrong_version", bool, field)
            if matched is not None and matched not in gold_ids:
                judgment_row.fail(f"{field}.matched_gold_id", f"unknown gold ID {matched!r} in this case")
            if correct and matched is None:
                judgment_row.fail(f"{field}.matched_gold_id", "correct=true requires a valid gold ID")
            if correct and wrong_version:
                judgment_row.fail(f"{field}.wrong_version", "wrong_version=true cannot coexist with correct=true")
            if supported and not predicted[pred_id]["evidence"]:
                judgment_row.fail(f"{field}.citation_supported", "cannot support an item with no evidence")
            judged[pred_id] = item
        missing = set(predicted) - set(judged)
        if missing:
            judgment_row.fail("items", f"missing judgments for prediction IDs: {sorted(missing)!r}")
        indexed_judgments[case_id] = judged
    return cases, predictions, indexed_judgments


def ratio(numerator: int | float, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def score_eval(
    case_rows: list[Row], prediction_rows: list[Row], judgment_rows: list[Row],
) -> dict[str, Any]:
    cases, predictions, judgments = validate_scoring_inputs(
        case_rows, prediction_rows, judgment_rows
    )
    counts = {
        "cases": len(cases), "answerable_cases": 0, "unanswerable_cases": 0,
        "gold_items": 0, "prediction_items": 0, "unique_correct_hits": 0,
        "complete_cases": 0, "partial_cases": 0, "error_cases": 0,
        "full_coverage_cases": 0, "fully_correct_cases": 0,
        "correct_unanswerable_cases": 0, "citation_supported_items": 0,
        "wrong_version_items": 0,
    }
    per_case: list[dict[str, Any]] = []
    recall_sum = 0.0
    for case_id, case_row in cases.items():
        case = case_row.data
        prediction = predictions[case_id].data
        decisions = list(judgments[case_id].values())
        # Each gold contributes at most once, but EVERY prediction stays in the
        # precision denominator, including duplicates, hallucinations and errors.
        hits = {item["matched_gold_id"] for item in decisions if item["correct"]}
        gold_count = len(case["gold_items"])
        output_count = len(prediction["items"])
        recall = ratio(len(hits), gold_count)
        complete = prediction["status"] == "complete"
        full_coverage = case["answerable"] and complete and len(hits) == gold_count
        unanswerable_correct = not case["answerable"] and complete and output_count == 0
        fully_correct = unanswerable_correct or (
            full_coverage and output_count == gold_count
            and all(item["correct"] and item["citation_supported"] for item in decisions)
        )
        supported_count = sum(item["citation_supported"] for item in decisions)
        wrong_version_count = sum(item["wrong_version"] for item in decisions)
        counts["answerable_cases"] += int(case["answerable"])
        counts["unanswerable_cases"] += int(not case["answerable"])
        counts["gold_items"] += gold_count
        counts["prediction_items"] += output_count
        counts["unique_correct_hits"] += len(hits)
        counts[f"{prediction['status']}_cases"] += 1
        counts["full_coverage_cases"] += int(full_coverage)
        counts["fully_correct_cases"] += int(fully_correct)
        counts["correct_unanswerable_cases"] += int(unanswerable_correct)
        counts["citation_supported_items"] += supported_count
        counts["wrong_version_items"] += wrong_version_count
        if case["answerable"]:
            assert recall is not None
            recall_sum += recall
        per_case.append({
            "case_id": case_id, "answerable": case["answerable"],
            "status": prediction["status"], "gold_items": gold_count,
            "prediction_items": output_count, "unique_correct_hits": len(hits),
            "recall": recall, "full_coverage": bool(full_coverage),
            "fully_correct": bool(fully_correct),
            "unanswerable_correct": unanswerable_correct if not case["answerable"] else None,
            "citation_supported_items": supported_count,
            "wrong_version_items": wrong_version_count,
        })

    fractions = {
        "micro_recall": (counts["unique_correct_hits"], counts["gold_items"]),
        "macro_recall": (recall_sum, counts["answerable_cases"]),
        "precision": (counts["unique_correct_hits"], counts["prediction_items"]),
        "full_coverage_rate": (counts["full_coverage_cases"], counts["answerable_cases"]),
        "fully_correct_rate": (counts["fully_correct_cases"], counts["cases"]),
        "unanswerable_accuracy": (counts["correct_unanswerable_cases"], counts["unanswerable_cases"]),
        "citation_support_rate": (counts["citation_supported_items"], counts["prediction_items"]),
        "wrong_version_rate": (counts["wrong_version_items"], counts["prediction_items"]),
    }
    kind = case_rows[0].data["dataset_kind"]
    return {
        "dataset_kind": kind, "split": case_rows[0].data["split"],
        "is_model_benchmark": False,
        "scope_note": SCOPE_NOTE if kind == "synthetic" else (
            "公开数据与外部人工裁决的离线计分；本套件缺执行来源证据，不是经认证的模型准确率或性能结果"
        ),
        "provenance_note": "未提供或认证模型执行来源；本套件始终输出 is_model_benchmark=false，无延迟或吞吐指标。",
        "limitations": "裁决输入必须来自人工审核；评分器不认证其来源、不判断语义真伪，不验证预测证据原文或日期。请先运行数据校验器。",
        "metric_definitions": {
            "micro_recall": "逐题去重后的正确 gold 命中总数 / gold 总数；partial/error 的已有正确项也计入。",
            "macro_recall": "所有 answerable 题的 recall 均值，失败题不剔除。",
            "precision": "逐题去重后的正确 gold 命中总数 / 全部输出项数，重复项仍计入分母。",
            "full_coverage_rate": "complete 且命中全部 gold 的 answerable 题数 / answerable 题数；不排除额外错项。",
            "fully_correct_rate": "complete、无错项无重复、gold 齐全且每项引用支持的题数 / 全部题数；无答案题须 complete 且空输出。",
            "unanswerable_accuracy": "complete 且空输出的无答案题数 / 无答案题总数。",
            "citation_support_rate": "人工裁决 citation_supported=true 的输出项数 / 全部输出项数（不是逐条 citation 计数）。",
            "wrong_version_rate": "人工裁决 wrong_version=true 的输出项数 / 全部输出项数。",
        },
        "counts": counts,
        "metrics": {name: ratio(*fraction) for name, fraction in fractions.items()},
        "metric_counts": {
            name: {"numerator": fraction[0], "denominator": fraction[1]}
            for name, fraction in fractions.items()
        },
        "per_case": per_case,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--judgments", required=True)
    parser.add_argument("--output", help="JSON destination (parent must exist); default: stdout")
    args = parser.parse_args(argv)
    try:
        if args.output:
            output_path = Path(args.output).resolve()
            inputs = {Path(path).resolve() for path in (args.cases, args.predictions, args.judgments)}
            if output_path in inputs:
                raise ValidationError(f"{output_path}: --output: must not overwrite an input")
            if output_path.exists() and any(
                output_path.samefile(path) for path in inputs if path.exists()
            ):
                raise ValidationError(f"{output_path}: --output: must not overwrite an input alias")
        result = score_eval(
            load_jsonl(args.cases), load_jsonl(args.predictions), load_jsonl(args.judgments)
        )
        payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            # Do not make directories, modify inputs, or emit ancillary files.
            Path(args.output).write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
        print(f"注意：{result['scope_note']}；is_model_benchmark=false", file=sys.stderr)
    except (ValidationError, OSError) as exc:
        print(f"scoring error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
