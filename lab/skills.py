"""Optional built-in skills for advanced management work.

Skills are deliberately separate from student_instructions. They are never
auto-selected as student instructions. An AI Manager should read a skill only
when the student explicitly invokes it by name.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from lab import config
from lab.errors import SkillError

SKILLS_SOURCE_URL = "https://www.kimi.ai/resources/project-management-skills-for-agents"
VALID_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class Skill:
    name: str
    title: str
    category: str
    description: str
    triggers: str
    source: str
    path: str
    words: int


@dataclass(frozen=True)
class SkillMatch:
    name: str
    title: str
    category: str
    description: str
    score: float
    matched_terms: tuple[str, ...]


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return {}, text
    metadata = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip().strip('"').strip("'")
        if key:
            metadata[key] = value
    body = "\n".join(lines[end + 1:]).lstrip("\n")
    return metadata, body


def _skill_paths() -> list[Path]:
    root = config.SKILLS_DIR
    if not root.exists():
        return []
    paths = []
    for path in sorted(root.glob("*.md"), key=lambda item: item.name.lower()):
        if path.name.lower() == "readme.md" or path.name.startswith(("_", ".")):
            continue
        paths.append(path)
    return paths


def _build_skill(path: Path) -> Skill:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SkillError(f"Could not read skill {path.name}: {exc}") from exc
    metadata, body = _parse_frontmatter(text)
    name = (metadata.get("name") or path.stem).strip().lower()
    if not VALID_NAME.fullmatch(name):
        raise SkillError(
            f"Skill name '{name}' in {path.name} is invalid. Use lowercase letters, numbers, and hyphens."
        )
    title = metadata.get("title") or name.replace("-", " ").title()
    category = metadata.get("category") or "General"
    description = metadata.get("description") or ""
    triggers = metadata.get("triggers") or ""
    source = metadata.get("source") or "Built-in lab skill"
    return Skill(
        name=name,
        title=title,
        category=category,
        description=description,
        triggers=triggers,
        source=source,
        path=path.name,
        words=len(re.findall(r"\b[\w'-]+\b", body)),
    )


def list_skills() -> list[Skill]:
    skills = []
    for path in _skill_paths():
        try:
            skills.append(_build_skill(path))
        except SkillError:
            continue
    return skills


def validate_all() -> list[str]:
    errors = []
    for path in _skill_paths():
        try:
            _build_skill(path)
        except SkillError as exc:
            errors.append(str(exc))
    return errors


def skill_names() -> list[str]:
    return [skill.name for skill in list_skills()]


def _normalize_requested(name: str) -> str:
    raw = (name or "").strip().lower()
    if raw.startswith("/"):
        raw = raw[1:]
    if raw.endswith(".md"):
        raw = raw[:-3]
    return raw.strip().replace("_", "-").replace(" ", "-")


def resolve_skill(name: str) -> Skill:
    requested = _normalize_requested(name)
    if not requested:
        raise SkillError("An empty skill name was provided.")
    skills = list_skills()
    exact = [skill for skill in skills if skill.name == requested]
    if len(exact) == 1:
        return exact[0]
    title_matches = [
        skill for skill in skills
        if skill.title.lower() == requested.replace("-", " ")
        or skill.title.lower() == requested
    ]
    if len(title_matches) == 1:
        return title_matches[0]
    if not exact and not title_matches:
        raise SkillError(
            f"Built-in skill not found: {name}. Available skills: {', '.join(skill_names()) or 'none'}."
        )
    raise SkillError(f"Skill name '{name}' is ambiguous.")


def read_skill(name: str) -> str:
    skill = resolve_skill(name)
    path = config.SKILLS_DIR / skill.path
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SkillError(f"Could not read skill {name}: {exc}") from exc


def read_skill_body(name: str) -> str:
    text = read_skill(name)
    _, body = _parse_frontmatter(text)
    return body


def normalize_skill_ref(name: str) -> str:
    return resolve_skill(name).name


def _tokens(text: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9]+", (text or "").lower())
        if len(token) > 2
    ]


def search_skills(query: str, limit: int = 10) -> list[SkillMatch]:
    terms = list(dict.fromkeys(_tokens(query)))
    if not terms:
        return []
    matches = []
    for skill in list_skills():
        haystack = " ".join([skill.name, skill.title, skill.category, skill.description, skill.triggers])
        haystack_tokens = _tokens(haystack)
        counts = {}
        for token in haystack_tokens:
            counts[token] = counts.get(token, 0) + 1
        matched = set()
        score = 0.0
        for term in terms:
            hits = counts.get(term, 0)
            if hits:
                matched.add(term)
                score += hits
                if term in _tokens(skill.name):
                    score += 4
                if term in _tokens(skill.title):
                    score += 2
        if score:
            score = score / math.sqrt(max(1, skill.words) / 150 + 1)
            matches.append(SkillMatch(
                name=skill.name,
                title=skill.title,
                category=skill.category,
                description=skill.description,
                score=round(score, 2),
                matched_terms=tuple(sorted(matched)),
            ))
    matches.sort(key=lambda item: (-item.score, item.name))
    return matches[: max(1, limit)]


def skills_digest() -> str:
    skills = list_skills()
    if not skills:
        return "_No built-in skills are installed._"
    grouped: dict[str, list[Skill]] = {}
    for skill in skills:
        grouped.setdefault(skill.category, []).append(skill)
    lines = []
    for category in sorted(grouped):
        lines.append(f"### {category}")
        for skill in grouped[category]:
            description = f" — {skill.description}" if skill.description else ""
            lines.append(f"- **{skill.name}** ({skill.title}){description}")
        lines.append("")
    lines.append(
        "These skills are optional. Read and apply one only when the student explicitly invokes it by name. "
        "They do not replace the student's instruction files or the company data."
    )
    return "\n".join(lines).strip()


def catalog() -> list[dict[str, str]]:
    return [
        {
            "name": skill.name,
            "title": skill.title,
            "category": skill.category,
            "description": skill.description,
            "triggers": skill.triggers,
            "source": skill.source,
            "words": str(skill.words),
        }
        for skill in list_skills()
    ]
