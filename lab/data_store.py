"""Read-only access to teacher-provided company documents and CSV tables."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import pandas as pd

from lab import config
from lab.errors import DataError

DEFAULT_QUERY_LIMIT = 100
MAX_QUERY_LIMIT = 1000
VALID_AGGREGATIONS = {"sum", "mean", "median", "min", "max", "count", "nunique", "std"}


@dataclass(frozen=True)
class CompanyFile:
    name: str
    kind: str
    size: int
    modified: str


@dataclass
class QueryResult:
    frame: pd.DataFrame
    matched_rows: int
    total_rows: int
    grouped: bool
    limited: bool


def _is_ignored(relative: Path) -> bool:
    if any(part.startswith(".") or part.startswith("_") for part in relative.parts):
        return True
    if relative.name.lower() == "readme.md":
        return True
    if relative.name.upper().startswith("TEACHER"):
        return True
    return False


def _relative_files() -> Iterable[Path]:
    root = config.TEACHER_DIR
    if not root.exists():
        return []
    return sorted(
        (path.relative_to(root) for path in root.rglob("*") if path.is_file() and not _is_ignored(path.relative_to(root))),
        key=lambda p: (p.suffix.lower() != ".csv", p.as_posix().lower()),
    )


def list_company_files(kind: str | None = None) -> list[CompanyFile]:
    files = []
    for relative in _relative_files():
        suffix = relative.suffix.lower()
        if suffix not in config.SUPPORTED_DATA_SUFFIXES:
            continue
        file_kind = "table" if suffix in config.SUPPORTED_TABLE_SUFFIXES else "document"
        if kind and file_kind != kind:
            continue
        path = config.TEACHER_DIR / relative
        stat = path.stat()
        files.append(CompanyFile(
            name=relative.as_posix(),
            kind=file_kind,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        ))
    return files


def company_file_names(kind: str | None = None) -> list[str]:
    return [item.name for item in list_company_files(kind)]


def _split_reference(reference: str) -> tuple[str, str]:
    raw = (reference or "").strip().replace("\\", "/")
    if not raw or "\x00" in raw:
        raise DataError("An empty or invalid company file reference was provided.")
    base, _, fragment = raw.partition("#")
    return base.strip(), fragment.strip()


def resolve_company_file(reference: str) -> Path:
    base, _ = _split_reference(reference)
    if base.startswith("/") or re.match(r"^[A-Za-z]:", base):
        raise DataError(f"Use a path relative to teacher_materials, not an absolute path: {reference}")
    root = config.TEACHER_DIR.resolve()
    candidate = (root / base).resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        raise DataError(f"Company file must stay inside teacher_materials: {reference}") from None
    if not candidate.exists() or not candidate.is_file():
        raise DataError(f"Company file not found: {reference}")
    if _is_ignored(relative):
        raise DataError(f"Not a discoverable company data file: {reference}")
    if candidate.suffix.lower() not in config.SUPPORTED_DATA_SUFFIXES:
        raise DataError(f"Unsupported company file type: {candidate.suffix}")
    return candidate


def normalize_company_reference(reference: str) -> str:
    base, fragment = _split_reference(reference)
    path = resolve_company_file(reference)
    relative = path.relative_to(config.TEACHER_DIR.resolve()).as_posix()
    return f"{relative}#{fragment}" if fragment else relative


def read_document(reference: str) -> str:
    path = resolve_company_file(reference)
    if path.suffix.lower() not in config.SUPPORTED_DOC_SUFFIXES:
        raise DataError(f"{reference} is a table, not a document. Use a CSV query for tabular data.")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise DataError(f"{reference} is not valid UTF-8 text.") from None
    except OSError as exc:
        raise DataError(f"Could not read {reference}: {exc}") from exc


def _table_path(reference: str) -> Path:
    path = resolve_company_file(reference)
    if path.suffix.lower() != ".csv":
        raise DataError(f"{reference} is not a CSV table.")
    return path


@lru_cache(maxsize=16)
def _load_csv_cached(path_str: str, modified_ns: int) -> pd.DataFrame:
    path = Path(path_str)
    try:
        frame = pd.read_csv(path, low_memory=False)
    except pd.errors.EmptyDataError:
        raise DataError(f"{path.name} is empty.") from None
    except pd.errors.ParserError as exc:
        raise DataError(f"Could not parse {path.name}: {exc}") from exc
    except OSError as exc:
        raise DataError(f"Could not open {path.name}: {exc}") from exc
    if frame.columns.empty:
        raise DataError(f"{path.name} has no columns.")
    return frame


def load_table(reference: str) -> pd.DataFrame:
    path = _table_path(reference)
    return _load_csv_cached(str(path), path.stat().st_mtime_ns)


def table_shape(reference: str) -> tuple[int, int]:
    frame = load_table(reference)
    return len(frame), len(frame.columns)


def _json_value(value):
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def table_profile(frame: pd.DataFrame) -> dict:
    columns = []
    for name in frame.columns:
        series = frame[name]
        samples = [_json_value(v) for v in series.dropna().head(3).tolist()]
        columns.append({
            "name": str(name),
            "dtype": str(series.dtype),
            "non_null": int(series.notna().sum()),
            "missing": int(series.isna().sum()),
            "unique": int(series.nunique(dropna=True)),
            "sample": samples,
        })

    numeric = frame.select_dtypes(include="number")
    numeric_summary = []
    if not numeric.empty:
        described = numeric.describe().transpose()
        for name, row in described.iterrows():
            numeric_summary.append({
                "column": str(name),
                "count": float(row.get("count", 0)),
                "mean": float(row.get("mean", 0)),
                "std": float(row.get("std", 0)) if pd.notna(row.get("std")) else None,
                "min": float(row.get("min", 0)),
                "median": float(row.get("50%", 0)),
                "max": float(row.get("max", 0)),
            })

    categoricals = {}
    for name in frame.select_dtypes(include=["object", "bool", "category"]).columns:
        counts = frame[name].value_counts(dropna=False).head(6)
        categoricals[str(name)] = [
            {"value": _json_value(index), "count": int(count)} for index, count in counts.items()
        ]

    return {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "missing_cells": int(frame.isna().sum().sum()),
        "memory_bytes": int(frame.memory_usage(deep=True).sum()),
        "column_details": columns,
        "numeric_summary": numeric_summary,
        "categorical_top": categoricals,
    }


def _format_cell(value, max_width: int = 48) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, pd.Timestamp):
        text = value.strftime("%Y-%m-%d")
    elif isinstance(value, float):
        text = f"{value:,.2f}" if abs(value) >= 1000 else f"{value:.4g}"
    elif isinstance(value, int):
        text = f"{value:,}"
    else:
        text = str(value)
    text = text.replace("\r", " ").replace("\n", " ").replace("|", "\\|").strip()
    if len(text) > max_width:
        text = text[: max_width - 1] + "…"
    return text


def frame_to_markdown(frame: pd.DataFrame, max_rows: int = 50, max_width: int = 48) -> str:
    if frame is None or frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows)
    headers = [str(column) for column in shown.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in shown.iterrows():
        lines.append("| " + " | ".join(_format_cell(value, max_width) for value in row.tolist()) + " |")
    if len(frame) > max_rows:
        lines.append(f"\n_Showing {max_rows:,} of {len(frame):,} rows._")
    return "\n".join(lines)


def _parse_filter(expression: str) -> tuple[str, str, str]:
    match = re.match(r"^\s*([A-Za-z0-9 _\-]+?)\s*(>=|<=|!=|==|=|>|<|~)\s*(.*?)\s*$", expression or "")
    if not match:
        raise DataError(
            f"Invalid filter '{expression}'. Use COLUMN=VALUE, COLUMN>VALUE, or COLUMN~TEXT."
        )
    column, operator, value = match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
    if value[:1] == value[-1:] and value[:1] in {'"', "'"}:
        value = value[1:-1]
    if value == "":
        raise DataError(f"Filter '{expression}' is missing a value.")
    return column, operator, value


def _resolve_column(frame: pd.DataFrame, requested: str) -> str:
    if requested in frame.columns:
        return requested
    matches = [str(column) for column in frame.columns if str(column).lower() == requested.lower()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise DataError(f"Column '{requested}' not found. Available columns: {', '.join(map(str, frame.columns))}")
    raise DataError(f"Column name '{requested}' is ambiguous: {', '.join(matches)}")


def _apply_filters(frame: pd.DataFrame, filters: Iterable[str]) -> pd.DataFrame:
    filtered = frame
    for expression in filters:
        column, operator, value = _parse_filter(expression)
        resolved = _resolve_column(filtered, column)
        series = filtered[resolved]
        if operator == "~":
            mask = series.astype(str).str.contains(value, case=False, regex=False, na=False)
            filtered = filtered[mask]
        elif pd.api.types.is_bool_dtype(series):
            lowered = value.lower()
            if lowered not in {"true", "false", "yes", "no", "1", "0"}:
                raise DataError(f"Filter '{expression}' needs a true/false value for {resolved}.")
            target = lowered in {"true", "yes", "1"}
            filtered = filtered[series == target] if operator in {"=", "=="} else filtered[series != target]
        elif pd.api.types.is_numeric_dtype(series):
            try:
                numeric = float(value)
            except ValueError:
                raise DataError(f"Filter '{expression}' needs a numeric value for {resolved}.") from None
            if operator in {"=", "=="}:
                filtered = filtered[series == numeric]
            elif operator == "!=":
                filtered = filtered[series != numeric]
            elif operator == ">":
                filtered = filtered[series > numeric]
            elif operator == ">=":
                filtered = filtered[series >= numeric]
            elif operator == "<":
                filtered = filtered[series < numeric]
            elif operator == "<=":
                filtered = filtered[series <= numeric]
        elif pd.api.types.is_datetime64_any_dtype(series):
            try:
                timestamp = pd.Timestamp(value)
            except Exception:
                raise DataError(f"Filter '{expression}' needs a date value for {resolved}.") from None
            if operator == ">":
                filtered = filtered[series > timestamp]
            elif operator == ">=":
                filtered = filtered[series >= timestamp]
            elif operator == "<":
                filtered = filtered[series < timestamp]
            elif operator == "<=":
                filtered = filtered[series <= timestamp]
            elif operator in {"=", "=="}:
                filtered = filtered[series == timestamp]
            elif operator == "!=":
                filtered = filtered[series != timestamp]
        else:
            text_series = series.astype(str)
            if operator in {"=", "=="}:
                filtered = filtered[text_series.str.lower() == value.lower()]
            elif operator == "!=":
                filtered = filtered[text_series.str.lower() != value.lower()]
            elif operator == ">":
                filtered = filtered[text_series > value]
            elif operator == ">=":
                filtered = filtered[text_series >= value]
            elif operator == "<":
                filtered = filtered[text_series < value]
            elif operator == "<=":
                filtered = filtered[text_series <= value]
    return filtered


def _split_list(values: str | Iterable[str] | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [part.strip() for part in values.split(",") if part.strip()]
    return [str(part).strip() for part in values if str(part).strip()]


def _parse_metrics(metrics: Iterable[str]) -> list[tuple[str, str]]:
    parsed = []
    for expression in metrics:
        if ":" not in expression:
            raise DataError(f"Metric '{expression}' must look like sum:Revenue or mean:Salary.")
        aggregation, column = expression.split(":", 1)
        aggregation = aggregation.strip().lower()
        column = column.strip()
        if aggregation not in VALID_AGGREGATIONS:
            raise DataError(f"Unsupported aggregation '{aggregation}'. Use one of: {', '.join(sorted(VALID_AGGREGATIONS))}.")
        if not column:
            raise DataError(f"Metric '{expression}' is missing a column.")
        parsed.append((aggregation, column))
    return parsed


def query_table(
    reference: str,
    filters: Iterable[str] | None = None,
    group_by: str | Iterable[str] | None = None,
    metrics: Iterable[str] | None = None,
    sort_by: str | None = None,
    limit: int = DEFAULT_QUERY_LIMIT,
) -> QueryResult:
    frame = load_table(reference)
    total_rows = len(frame)
    if isinstance(filters, str):
        filters = [filters]
    if isinstance(metrics, str):
        metrics = _split_list(metrics)
    filtered = _apply_filters(frame, filters or [])
    group_columns = _split_list(group_by)
    metric_specs = _parse_metrics(metrics or [])

    resolved_groups = []
    for column in group_columns:
        resolved_groups.append(_resolve_column(filtered, column))
    group_columns = resolved_groups

    if group_columns:
        grouped = filtered.groupby(group_columns, dropna=False)
        pieces = []
        if metric_specs:
            named = {}
            count_star_name = None
            for index, (aggregation, column) in enumerate(metric_specs):
                if aggregation == "count" and column in {"*", "rows"}:
                    count_star_name = "Rows"
                    continue
                resolved = _resolve_column(filtered, column)
                output_name = f"{aggregation}_{resolved}"
                while output_name in named:
                    output_name += "_2"
                named[output_name] = pd.NamedAgg(column=resolved, aggfunc=aggregation)
            if named:
                pieces.append(grouped.agg(**named).reset_index())
            if count_star_name:
                pieces.append(grouped.size().reset_index(name=count_star_name))
            if len(pieces) == 1:
                result = pieces[0]
            else:
                result = pieces[0]
                for piece in pieces[1:]:
                    result = result.merge(piece, on=group_columns, how="outer")
        else:
            result = grouped.size().reset_index(name="Rows")
        grouped_result = True
    elif metric_specs:
        values = {}
        for aggregation, column in metric_specs:
            if aggregation == "count" and column in {"*", "rows"}:
                values["Rows"] = len(filtered)
                continue
            resolved = _resolve_column(filtered, column)
            output_name = f"{aggregation}_{resolved}"
            while output_name in values:
                output_name += "_2"
            series = filtered[resolved]
            if aggregation == "count":
                values[output_name] = int(series.count())
            else:
                values[output_name] = getattr(series, aggregation)()
        result = pd.DataFrame([values])
        grouped_result = True
    else:
        result = filtered.copy()
        grouped_result = False

    if sort_by:
        parts = sort_by.split(":")
        sort_column = parts[0].strip()
        descending = len(parts) > 1 and parts[1].strip().lower() in {"desc", "descending", "d"}
        try:
            sort_column = _resolve_column(result, sort_column)
        except DataError:
            metric_matches = [str(column) for column in result.columns if str(column).endswith(f"_{sort_column}")]
            if len(metric_matches) == 1:
                sort_column = metric_matches[0]
            else:
                raise
        result = result.sort_values(by=sort_column, ascending=not descending, kind="mergesort")

    clamped_limit = max(1, min(int(limit or DEFAULT_QUERY_LIMIT), MAX_QUERY_LIMIT))
    limited = len(result) > clamped_limit
    result = result.head(clamped_limit).reset_index(drop=True)
    return QueryResult(
        frame=result,
        matched_rows=len(filtered),
        total_rows=total_rows,
        grouped=grouped_result,
        limited=limited,
    )


def format_query_result(result: QueryResult, fmt: str = "table") -> str:
    if fmt == "csv":
        return result.frame.to_csv(index=False)
    if fmt == "json":
        payload = {
            "matched_rows": result.matched_rows,
            "total_rows": result.total_rows,
            "returned_rows": len(result.frame),
            "grouped": result.grouped,
            "rows": json.loads(result.frame.to_json(orient="records", force_ascii=False)),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)
    lines = [f"Matched {result.matched_rows:,} of {result.total_rows:,} rows."]
    lines.append(frame_to_markdown(result.frame, max_rows=min(100, len(result.frame))))
    if result.limited:
        lines.append(f"_Output limited to {len(result.frame):,} rows. Narrow the query or use --limit._")
    return "\n".join(lines)


def describe_table(reference: str) -> str:
    frame = load_table(reference)
    profile = table_profile(frame)
    lines = [
        f"# {reference}",
        "",
        f"- Rows: {profile['rows']:,}",
        f"- Columns: {profile['columns']:,}",
        f"- Missing cells: {profile['missing_cells']:,}",
        f"- Memory: {profile['memory_bytes'] / 1024 / 1024:.2f} MB",
        "",
        "## Columns",
        "",
        "| Column | Type | Non-null | Missing | Unique | Sample |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for column in profile["column_details"]:
        sample = "; ".join(_format_cell(value, 32) for value in column["sample"])
        lines.append(
            f"| {column['name']} | {column['dtype']} | {column['non_null']:,} | "
            f"{column['missing']:,} | {column['unique']:,} | {sample} |"
        )

    if profile["numeric_summary"]:
        lines.extend(["", "## Numeric summary", ""])
        summary = pd.DataFrame(profile["numeric_summary"])
        summary = summary.rename(columns={
            "column": "Column", "count": "Count", "mean": "Mean", "std": "Std",
            "min": "Min", "median": "Median", "max": "Max",
        })
        lines.append(frame_to_markdown(summary, max_rows=50, max_width=24))

    if profile["categorical_top"]:
        lines.extend(["", "## Top values", ""])
        for column, values in profile["categorical_top"].items():
            rendered = ", ".join(f"{item['value']} ({item['count']:,})" for item in values)
            lines.append(f"- **{column}**: {rendered}")

    lines.extend(["", "## Sample rows", "", frame_to_markdown(frame.head(5), max_rows=5)])
    return "\n".join(lines)


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return ""


def company_name() -> str:
    candidates = []
    if config.TEACHER_DIR.exists():
        preferred = config.TEACHER_DIR / "company_profile.md"
        if preferred.exists():
            candidates.append(preferred)
        candidates.extend(
            path for path in sorted(config.TEACHER_DIR.glob("*.md"))
            if path != preferred and "company" in path.name.lower() and "profile" in path.name.lower()
        )
    for path in candidates:
        try:
            heading = _first_heading(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if heading:
            return heading
    return config.COMPANY_FALLBACK


def data_digest(max_columns: int = 24) -> str:
    files = list_company_files()
    if not files:
        return "_No teacher-provided company data was found._"
    lines = [f"Company: **{company_name()}**", "", "## Company files"]
    for item in files:
        if item.kind == "table":
            try:
                frame = load_table(item.name)
                columns = [str(column) for column in frame.columns]
                shown = ", ".join(columns[:max_columns])
                if len(columns) > max_columns:
                    shown += f", … ({len(columns) - max_columns} more)"
                lines.append(f"- **{item.name}** — {len(frame):,} rows; columns: {shown}")
            except DataError as exc:
                lines.append(f"- **{item.name}** — unreadable: {exc}")
        else:
            try:
                text = read_document(item.name)
                heading = _first_heading(text)
                descriptor = f"heading: {heading}" if heading else f"{len(text):,} characters"
                lines.append(f"- **{item.name}** — document; {descriptor}")
            except DataError as exc:
                lines.append(f"- **{item.name}** — unreadable: {exc}")
    return "\n".join(lines)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_manifest() -> dict:
    files = {}
    for relative in _relative_files():
        path = config.TEACHER_DIR / relative
        stat = path.stat()
        files[relative.as_posix()] = {
            "size": stat.st_size,
            "sha256": file_sha256(path),
        }
    return {
        "version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "files": files,
    }


def write_manifest() -> Path:
    if not config.TEACHER_DIR.exists():
        raise DataError(f"Teacher materials folder not found: {config.TEACHER_DIR}")
    manifest = compute_manifest()
    config.MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = config.MANIFEST_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(config.MANIFEST_PATH)
    return config.MANIFEST_PATH


def check_manifest() -> dict:
    if not config.MANIFEST_PATH.exists():
        return {
            "status": "untracked",
            "summary": "No dataset manifest has been created yet.",
            "changed": [],
            "missing": [],
            "added": [],
        }
    try:
        manifest = json.loads(config.MANIFEST_PATH.read_text(encoding="utf-8"))
        recorded = manifest.get("files", {})
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "invalid",
            "summary": f"Dataset manifest could not be read: {exc}",
            "changed": [], "missing": [], "added": [],
        }

    current_files = {relative.as_posix(): config.TEACHER_DIR / relative for relative in _relative_files()}
    changed, missing, added = [], [], []
    for name, info in recorded.items():
        path = config.TEACHER_DIR / name
        if not path.exists():
            missing.append(name)
        elif file_sha256(path) != info.get("sha256"):
            changed.append(name)
    for name in current_files:
        if name not in recorded:
            added.append(name)
    if changed or missing or added:
        status = "changed"
        summary = "Teacher data differs from the manifest."
    else:
        status = "verified"
        summary = "All teacher data files match the recorded manifest."
    return {
        "status": status,
        "summary": summary,
        "changed": sorted(changed),
        "missing": sorted(missing),
        "added": sorted(added),
    }
