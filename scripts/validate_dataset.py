"""Offline JSONL validation, Python 3.10+, standard library only.

This checks structure, identities, region/date scope and literal evidence, NOT
legal authenticity, semantic entailment, parsing completeness or answer coverage.
No URI is fetched; ``parse_status=complete`` is a supplied assertion, not proof.
Validity is [effective_at, repealed_at); dates must be YYYY-MM-DD.
Identifiers are unique within their owning case, except globally unique block_id,
case_id and version_id. Manifest identity is the pair (doc_id, version_id), and
global version IDs keep the case scope unambiguous.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
import sys
from typing import Any


class ValidationError(ValueError):
    """An actionable file:line:field diagnostic."""


@dataclass(frozen=True)
class Row:
    data: dict[str, Any]
    source: str
    line: int

    def fail(self, field: str, message: str) -> None:
        raise ValidationError(f"{self.source}:{self.line}: {field}: {message}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-JSON numeric constant {value!r}")


def load_jsonl(path: str | Path) -> list[Row]:
    """Reject blank records, duplicate JSON keys, non-objects and empty files."""
    path = Path(path)
    rows: list[Row] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                try:
                    data = json.loads(
                        line, object_pairs_hook=_unique_object,
                        parse_constant=_reject_constant,
                    )
                except ValueError as exc:
                    raise ValidationError(
                        f"{path}:{line_number}: $: invalid JSON: {exc}"
                    ) from exc
                if not isinstance(data, dict):
                    raise ValidationError(
                        f"{path}:{line_number}: $: expected an object"
                    )
                rows.append(Row(data, str(path), line_number))
    except (OSError, UnicodeError) as exc:
        raise ValidationError(f"{path}: $: cannot read UTF-8 JSONL: {exc}") from exc
    if not rows:
        raise ValidationError(f"{path}:1: $: empty JSONL file")
    return rows


def require(
    row: Row, obj: dict[str, Any], key: str, expected: type,
    prefix: str = "", *, nullable: bool = False,
) -> Any:
    field = f"{prefix}.{key}" if prefix else key
    if key not in obj:
        row.fail(field, "missing required field")
    value = obj[key]
    if value is None and nullable:
        return None
    # Exact types deliberately reject bool as int (e.g. page_no=true).
    if type(value) is not expected:
        row.fail(field, f"expected {expected.__name__}{' or null' if nullable else ''}")
    if expected is str and not value.strip():
        row.fail(field, "must be a non-empty string")
    return value


def date_value(row: Row, field: str, value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        row.fail(field, "expected calendar date YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError:
        row.fail(field, f"invalid calendar date {value!r}")
    raise AssertionError("unreachable")


def check_kind(rows: list[Row], expected: str | None = None) -> str:
    if not rows:
        raise ValidationError("$: at least one record is required")
    kind = expected
    for row in rows:
        value = require(row, row.data, "dataset_kind", str)
        if value not in {"synthetic", "public"}:
            row.fail("dataset_kind", "only synthetic or public is supported")
        if kind is None:
            kind = value
        if value != kind:
            row.fail("dataset_kind", f"mixed dataset kinds: expected {kind}, got {value}")
    assert kind is not None
    return kind


def check_evidence(row: Row, item: dict[str, Any], prefix: str) -> list[dict[str, Any]]:
    evidence = require(row, item, "evidence", list, prefix)
    for index, entry in enumerate(evidence):
        field = f"{prefix}.evidence[{index}]"
        if type(entry) is not dict:
            row.fail(field, "expected dict")
        require(row, entry, "block_id", str, field)
        require(row, entry, "quote", str, field)
    return evidence


def validate_cases(rows: list[Row], expected_kind: str | None = None) -> dict[str, Row]:
    """Standalone case schema checks reused by the scorer (no source access)."""
    check_kind(rows, expected_kind)
    cases: dict[str, Row] = {}
    for row in rows:
        data = row.data
        case_id = require(row, data, "case_id", str)
        if case_id in cases:
            row.fail("case_id", f"duplicate ID {case_id!r}")
        cases[case_id] = row
        split = require(row, data, "split", str)
        if split != "smoke":
            row.fail("split", "this small suite supports split='smoke' only")
        require(row, data, "query", str)
        scope = require(row, data, "scope", dict)
        require(row, scope, "region_code", str, "scope")
        as_of = require(row, scope, "as_of", str, "scope")
        date_value(row, "scope.as_of", as_of)
        versions = require(row, scope, "version_ids", list, "scope")
        seen_versions: set[str] = set()
        for index, version in enumerate(versions):
            field = f"scope.version_ids[{index}]"
            if type(version) is not str or not version.strip():
                row.fail(field, "expected a non-empty string")
            if version in seen_versions:
                row.fail(field, f"duplicate version ID {version!r}")
            seen_versions.add(version)
        answerable = require(row, data, "answerable", bool)
        gold = require(row, data, "gold_items", list)
        if answerable and (not gold or not versions):
            row.fail("gold_items/scope.version_ids", "answerable case requires gold and versions")
        if not answerable and gold:
            row.fail("gold_items", "unanswerable case must have no gold items")
        seen_items: set[str] = set()
        for index, item in enumerate(gold):
            field = f"gold_items[{index}]"
            if type(item) is not dict:
                row.fail(field, "expected dict")
            item_id = require(row, item, "item_id", str, field)
            if item_id in seen_items:
                row.fail(f"{field}.item_id", f"duplicate ID {item_id!r}")
            seen_items.add(item_id)
            require(row, item, "text", str, field)
            if not check_evidence(row, item, field):
                row.fail(f"{field}.evidence", "gold item requires literal evidence")
    return cases


def validate_dataset(
    manifests: list[Row], blocks: list[Row], cases: list[Row],
) -> dict[str, Any]:
    kind = check_kind(manifests)
    check_kind(blocks, kind)
    case_map = validate_cases(cases, kind)
    documents: dict[tuple[str, str], Row] = {}
    dates: dict[tuple[str, str], tuple[date, date | None]] = {}
    by_version: dict[str, list[tuple[str, str]]] = {}
    for row in manifests:
        data = row.data
        doc_id = require(row, data, "doc_id", str)
        version_id = require(row, data, "version_id", str)
        key = (doc_id, version_id)
        if key in documents:
            row.fail("doc_id/version_id", f"duplicate manifest key {key!r}")
        for field in ("title", "region_code", "source_uri"):
            require(row, data, field, str)
        if kind == "synthetic" and not data["source_uri"].startswith("synthetic://"):
            row.fail("source_uri", "synthetic input requires synthetic:// URI")
        if require(row, data, "parse_status", str) != "complete":
            row.fail("parse_status", "expected 'complete'")
        date_value(row, "published_at", require(row, data, "published_at", str))
        effective = date_value(row, "effective_at", require(row, data, "effective_at", str))
        repealed_raw = require(row, data, "repealed_at", str, nullable=True)
        repealed = date_value(row, "repealed_at", repealed_raw) if repealed_raw else None
        # Retrospective effectiveness must not be rejected just because it
        # predates publication. The source/annotation process verifies that fact.
        if repealed is not None and repealed <= effective:
            row.fail("repealed_at", "must be later than effective_at")
        if version_id in by_version:
            row.fail("version_id", "must be globally unique; qualify it with doc_id")
        documents[key] = row
        dates[key] = (effective, repealed)
        by_version.setdefault(version_id, []).append(key)

    block_map: dict[str, Row] = {}
    orders: dict[tuple[str, str], set[int]] = {}
    for row in blocks:
        data = row.data
        block_id = require(row, data, "block_id", str)
        if block_id in block_map:
            row.fail("block_id", f"duplicate block ID {block_id!r}")
        key = (require(row, data, "doc_id", str), require(row, data, "version_id", str))
        if key not in documents:
            row.fail("doc_id/version_id", f"unknown manifest key {key!r}")
        order = require(row, data, "block_order", int)
        if order < 0:
            row.fail("block_order", "must be non-negative")
        if order in orders.setdefault(key, set()):
            row.fail("block_order", f"duplicate order {order} in version {key!r}")
        orders[key].add(order)
        require(row, data, "parent_id", str, nullable=True)
        if require(row, data, "block_type", str) not in {"heading", "text", "table", "appendix"}:
            row.fail("block_type", "expected heading, text, table or appendix")
        if require(row, data, "page_no", int) < 1:
            row.fail("page_no", "must be at least 1")
        require(row, data, "text", str)
        require(row, data, "table_html", str, nullable=True)
        block_map[block_id] = row

    for key, row in documents.items():
        if key not in orders:
            row.fail("doc_id/version_id", f"manifest {key!r} has no blocks")
    for block_id, row in block_map.items():
        parent_id = row.data["parent_id"]
        if parent_id is None:
            continue
        parent = block_map.get(parent_id)
        if parent is None:
            row.fail("parent_id", f"unknown parent block {parent_id!r}")
        if (parent.data["doc_id"], parent.data["version_id"]) != (
            row.data["doc_id"], row.data["version_id"]
        ):
            row.fail("parent_id", "parent must belong to the same document version")
        if parent_id == block_id:
            row.fail("parent_id", "block cannot be its own parent")
    # Iterative traversal also catches longer cycles without recursion depth limits.
    finished: set[str] = set()
    for block_id, row in block_map.items():
        chain: set[str] = set()
        current: str | None = block_id
        while current is not None and current not in finished:
            if current in chain:
                block_map[current].fail("parent_id", "parent cycle detected")
            chain.add(current)
            current = block_map[current].data["parent_id"]
        finished.update(chain)

    def active(key: tuple[str, str], as_of: date) -> bool:
        effective, repealed = dates[key]
        return effective <= as_of and (repealed is None or as_of < repealed)

    for row in case_map.values():
        scope = row.data["scope"]
        as_of = date_value(row, "scope.as_of", scope["as_of"])
        # Globally unique version IDs make the scope unambiguous; evidence
        # additionally resolves its exact document version through block_id.
        for index, version in enumerate(scope["version_ids"]):
            field = f"scope.version_ids[{index}]"
            keys = by_version.get(version, [])
            if not keys:
                row.fail(field, f"unknown version {version!r}")
            regional = [key for key in keys if documents[key].data["region_code"] == scope["region_code"]]
            if not regional:
                row.fail(field, "version does not belong to scope.region_code")
            if not any(active(key, as_of) for key in regional):
                row.fail(field, f"version is not effective at {scope['as_of']} (expired or future)")
        for index, item in enumerate(row.data["gold_items"]):
            for evidence_index, evidence in enumerate(item["evidence"]):
                field = f"gold_items[{index}].evidence[{evidence_index}]"
                block = block_map.get(evidence["block_id"])
                if block is None:
                    row.fail(f"{field}.block_id", f"unknown block {evidence['block_id']!r}")
                key = (block.data["doc_id"], block.data["version_id"])
                if key[1] not in scope["version_ids"]:
                    row.fail(f"{field}.block_id", "evidence version is outside scope.version_ids")
                if documents[key].data["region_code"] != scope["region_code"]:
                    row.fail(f"{field}.block_id", "evidence region differs from scope.region_code")
                if not active(key, as_of):
                    row.fail(f"{field}.block_id", "evidence version is not effective at scope.as_of")
                if evidence["quote"] not in block.data["text"]:
                    row.fail(f"{field}.quote", "quote is not an exact substring of block.text")

    return {
        "valid": True, "dataset_kind": kind, "split": "smoke",
        "manifest_count": len(documents), "block_count": len(block_map),
        "case_count": len(case_map),
        "limitations": "仅检查结构、地域/日期范围及证据原文存在性；不验证法规真实性、语义支持、答案完整性或解析质量；不访问 source_uri。",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifests", required=True)
    parser.add_argument("--blocks", required=True)
    parser.add_argument("--cases", required=True)
    args = parser.parse_args(argv)
    try:
        result = validate_dataset(
            load_jsonl(args.manifests), load_jsonl(args.blocks), load_jsonl(args.cases)
        )
    except ValidationError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
