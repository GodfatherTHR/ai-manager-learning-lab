"""Student-authored Markdown management instructions."""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from lab import config
from lab.errors import InstructionError

MAX_INSTRUCTION_BYTES = 1_000_000
RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for", "from",
    "has", "have", "how", "i", "in", "into", "is", "it", "its", "of", "on", "or", "our",
    "should", "that", "the", "their", "them", "this", "to", "was", "we", "what", "when",
    "where", "which", "who", "why", "will", "with", "you", "your",
}


@dataclass(frozen=True)
class InstructionFile:
    name: str
    size: int
    modified: str
    words: int
    heading: str


@dataclass(frozen=True)
class InstructionMatch:
    name: str
    score: float
    matched_terms: tuple[str, ...]
    heading: str


def _root() -> Path:
    config.STUDENT_DIR.mkdir(parents=True, exist_ok=True)
    return config.STUDENT_DIR


def _is_ignored(relative: Path) -> bool:
    if any(part.startswith(".") or part.startswith("_") for part in relative.parts):
        return True
    if relative.suffix.lower() != ".md":
        return True
    if relative.name.lower() == "readme.md":
        return True
    return False


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^\s*#{1,3}\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return ""


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def validate_instruction_name(name: str) -> str:
    raw = (name or "").strip().replace("\\", "/")
    if not raw:
        raise InstructionError("Enter a file name.")
    if len(raw) > 160:
        raise InstructionError("The file name is too long (maximum 160 characters).")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise InstructionError("Use a relative file name, not an absolute path.")
    parts = [part for part in raw.split("/") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        raise InstructionError("The file name contains an invalid path.")
    for part in parts:
        if part.startswith("_") or part.startswith("."):
            raise InstructionError("File and folder names cannot start with '_' or '.'; those are reserved.")
        if part.endswith(" ") or part.endswith("."):
            raise InstructionError("File and folder names cannot end with a space or a dot.")
        if not re.match(r"^[A-Za-z0-9][A-Za-z0-9 _\-().]*$", part):
            raise InstructionError(
                "Use letters, numbers, spaces, hyphens, underscores, dots and parentheses only."
            )
        if part.split(".")[0].upper() in RESERVED_WINDOWS_NAMES:
            raise InstructionError(f"'{part}' is a reserved Windows file name.")
    if not parts[-1].lower().endswith(".md"):
        raise InstructionError("Instruction files must end with .md")
    if parts[-1].lower() == "readme.md":
        raise InstructionError("README.md is reserved. Choose a descriptive instruction file name.")
    return "/".join(parts)


def resolve_instruction(name: str) -> Path:
    raw = (name or "").strip().replace("\\", "/")
    if not raw:
        raise InstructionError("An empty instruction file name was provided.")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise InstructionError("Instruction paths must be relative to student_instructions.")
    root = _root().resolve()
    candidate = (root / raw).resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        raise InstructionError("Instruction paths cannot leave the student_instructions folder.") from None
    if _is_ignored(relative):
        raise InstructionError(f"Not an active instruction file: {name}")
    if not candidate.exists() or not candidate.is_file():
        raise InstructionError(f"Instruction file not found: {name}")
    return candidate


def list_instructions() -> list[InstructionFile]:
    root = _root()
    files = []
    for path in sorted(root.rglob("*.md"), key=lambda item: item.as_posix().lower()):
        relative = path.relative_to(root)
        if _is_ignored(relative):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        stat = path.stat()
        files.append(InstructionFile(
            name=relative.as_posix(),
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            words=word_count(text),
            heading=_first_heading(text),
        ))
    return files


def instruction_names() -> list[str]:
    return [item.name for item in list_instructions()]


def read_instruction(name: str) -> str:
    path = resolve_instruction(name)
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise InstructionError(f"{name} is not valid UTF-8 text.") from None
    except OSError as exc:
        raise InstructionError(f"Could not read {name}: {exc}") from exc


def _atomic_write(path: Path, content: str) -> None:
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_INSTRUCTION_BYTES:
        raise InstructionError("Instruction files must be smaller than 1 MB.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(content, encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink(missing_ok=True)


def create_instruction(name: str, content: str = "") -> InstructionFile:
    safe_name = validate_instruction_name(name)
    path = _root().resolve() / safe_name
    if path.exists():
        raise InstructionError(f"{safe_name} already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, content)
    return _instruction_file(path)


def update_instruction(name: str, content: str) -> InstructionFile:
    path = resolve_instruction(name)
    _atomic_write(path, content)
    return _instruction_file(path)


def delete_instruction(name: str) -> None:
    path = resolve_instruction(name)
    try:
        path.unlink()
    except OSError as exc:
        raise InstructionError(f"Could not delete {name}: {exc}") from exc


def rename_instruction(old_name: str, new_name: str) -> InstructionFile:
    old_path = resolve_instruction(old_name)
    safe_name = validate_instruction_name(new_name)
    new_path = _root().resolve() / safe_name
    if new_path.exists():
        raise InstructionError(f"{safe_name} already exists.")
    new_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        old_path.replace(new_path)
    except OSError as exc:
        raise InstructionError(f"Could not rename {old_name}: {exc}") from exc
    return _instruction_file(new_path)


def _instruction_file(path: Path) -> InstructionFile:
    text = path.read_text(encoding="utf-8")
    stat = path.stat()
    return InstructionFile(
        name=path.relative_to(_root().resolve()).as_posix(),
        size=stat.st_size,
        modified=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        words=word_count(text),
        heading=_first_heading(text),
    )


def _examples_root() -> Path:
    return _root() / "_examples"


def list_examples() -> list[InstructionFile]:
    root = _examples_root()
    if not root.exists():
        return []
    examples = []
    for path in sorted(root.rglob("*.md"), key=lambda item: item.as_posix().lower()):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        stat = path.stat()
        examples.append(InstructionFile(
            name=path.relative_to(root).as_posix(),
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            words=word_count(text),
            heading=_first_heading(text),
        ))
    return examples


def copy_example(example_name: str, destination_name: str) -> InstructionFile:
    root = _examples_root().resolve()
    raw = (example_name or "").strip().replace("\\", "/")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise InstructionError("Invalid example path.")
    source = (root / raw).resolve()
    try:
        source.relative_to(root)
    except ValueError:
        raise InstructionError("Invalid example path.") from None
    if not source.exists() or not source.is_file() or source.suffix.lower() != ".md":
        raise InstructionError(f"Example not found: {example_name}")
    content = source.read_text(encoding="utf-8")
    return create_instruction(destination_name, content)


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [token for token in tokens if len(token) > 2 and token not in STOPWORDS]


def search_instructions(query: str, limit: int = 8) -> list[InstructionMatch]:
    terms = list(dict.fromkeys(_tokenize(query)))
    if not terms:
        return []
    matches = []
    normalized_query = (query or "").strip().lower()
    for item in list_instructions():
        try:
            text = read_instruction(item.name)
        except InstructionError:
            continue
        lowered = text.lower()
        file_terms = _tokenize(item.name.replace("_", " ").replace("-", " "))
        heading_terms = _tokenize(item.heading)
        body_tokens = _tokenize(text)
        body_counts = {}
        for token in body_tokens:
            body_counts[token] = body_counts.get(token, 0) + 1
        file_counts = {}
        for token in file_terms:
            file_counts[token] = file_counts.get(token, 0) + 1
        heading_counts = {}
        for token in heading_terms:
            heading_counts[token] = heading_counts.get(token, 0) + 1

        matched = set()
        score = 0.0
        for term in terms:
            body_hits = body_counts.get(term, 0)
            file_hits = file_counts.get(term, 0)
            heading_hits = heading_counts.get(term, 0)
            if body_hits or file_hits or heading_hits:
                matched.add(term)
                score += body_hits + file_hits * 4 + heading_hits * 3
        if normalized_query and len(normalized_query) > 3 and normalized_query in lowered:
            score += 6
        if score > 0:
            score = score / math.sqrt(max(1, item.words) / 120 + 1)
            matches.append(InstructionMatch(
                name=item.name,
                score=round(score, 3),
                matched_terms=tuple(sorted(matched)),
                heading=item.heading,
            ))
    matches.sort(key=lambda item: (-item.score, item.name.lower()))
    return matches[: max(1, limit)]


def instructions_digest() -> str:
    files = list_instructions()
    if not files:
        return "_No active student instruction files yet._"
    lines = []
    for item in files:
        heading = f" — {item.heading}" if item.heading else ""
        lines.append(f"- **{item.name}** ({item.words:,} words){heading}")
    return "\n".join(lines)


def total_words() -> int:
    return sum(item.words for item in list_instructions())


def upload_instruction(name: str, data: bytes) -> InstructionFile:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise InstructionError(f"{name} is not valid UTF-8 text.") from None
    return create_instruction(name, text)
