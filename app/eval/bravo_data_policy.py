"""Policy-as-data loader for BRAVO AI runtime data classification."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re

from app.utils.yaml_compat import safe_load_file

DEFAULT_POLICY_PATH = Path("file_system/bravo_data_runtime_policy.yaml")
REQUIRED_CLASSES = {
    "shared_knowledge",
    "domain_rules",
    "eval_fixtures",
    "private_operational_data",
    "runtime_uploads",
    "derived_summary",
}


@dataclass(frozen=True)
class DataClassPolicy:
    name: str
    description: str
    shared_rag_allowed: bool
    versioned: bool
    runtime_scope: str
    ingestion_mode: str


@dataclass(frozen=True)
class PathRule:
    path: Path
    data_class: str
    required: bool = False
    ensure_exists: bool = False
    manifest: Path | None = None
    unmanifested_ingestible_policy: str = "ignore"
    duplicate_policy: str = "warn"
    notes: str = ""


@dataclass(frozen=True)
class DataRuntimePolicy:
    version: int
    policy_name: str
    default_class: str
    classes: dict[str, DataClassPolicy]
    path_rules: tuple[PathRule, ...]
    source_type_classes: dict[str, str]
    required_classes: tuple[str, ...]
    variables: dict[str, str]


def _as_bool(value: object, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def default_policy_variables() -> dict[str, str]:
    app_root = Path(os.getenv("APP_ROOT") or Path.cwd()).resolve()
    data_root = Path(os.getenv("DATA_ROOT") or app_root / "data").resolve()
    corpus_root = Path(os.getenv("CORPUS_ROOT") or app_root / "file_system").resolve()
    return {
        "APP_ROOT": str(app_root),
        "DATA_ROOT": str(data_root),
        "CORPUS_ROOT": str(corpus_root),
        "UPLOAD_ROOT": str(Path(os.getenv("UPLOAD_ROOT") or data_root / "uploads").resolve()),
        "PRIVATE_DATA_ROOT": str(
            Path(os.getenv("PRIVATE_DATA_ROOT") or data_root / "private").resolve()
        ),
    }


_VAR_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def resolve_policy_value(value: str, variables: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, os.getenv(key, match.group(0)))

    return _VAR_RE.sub(repl, value)


def _resolve_path(value: object, variables: dict[str, str]) -> Path:
    raw = resolve_policy_value(str(value), variables)
    path = Path(raw)
    if not path.is_absolute():
        path = Path(variables["APP_ROOT"]) / path
    return path.resolve()


def _load_classes(raw: dict) -> dict[str, DataClassPolicy]:
    classes = raw.get("classes") or {}
    if not isinstance(classes, dict):
        raise ValueError("data policy classes must be a mapping")
    out: dict[str, DataClassPolicy] = {}
    for name, meta in classes.items():
        if not isinstance(meta, dict):
            raise ValueError(f"data policy class {name} must be a mapping")
        out[str(name)] = DataClassPolicy(
            name=str(name),
            description=str(meta.get("description") or ""),
            shared_rag_allowed=_as_bool(meta.get("shared_rag_allowed")),
            versioned=_as_bool(meta.get("versioned")),
            runtime_scope=str(meta.get("runtime_scope") or ""),
            ingestion_mode=str(meta.get("ingestion_mode") or ""),
        )
    return out


def _load_path_rules(raw: dict, variables: dict[str, str]) -> tuple[PathRule, ...]:
    rules = raw.get("path_rules") or []
    if not isinstance(rules, list):
        raise ValueError("data policy path_rules must be a list")
    out: list[PathRule] = []
    for item in rules:
        if not isinstance(item, dict):
            raise ValueError("data policy path rule must be a mapping")
        path = item.get("path")
        data_class = item.get("data_class")
        if not path or not data_class:
            raise ValueError("data policy path rule requires path and data_class")
        manifest = item.get("manifest")
        out.append(
            PathRule(
                path=_resolve_path(path, variables),
                data_class=str(data_class),
                required=_as_bool(item.get("required")),
                ensure_exists=_as_bool(item.get("ensure_exists")),
                manifest=_resolve_path(manifest, variables) if manifest else None,
                unmanifested_ingestible_policy=str(
                    item.get("unmanifested_ingestible_policy") or "ignore"
                ),
                duplicate_policy=str(item.get("duplicate_policy") or "warn"),
                notes=str(item.get("notes") or ""),
            )
        )
    return tuple(out)


def load_data_runtime_policy(
    path: str | Path = DEFAULT_POLICY_PATH,
    *,
    variables: dict[str, str] | None = None,
) -> DataRuntimePolicy:
    variables = {**default_policy_variables(), **(variables or {})}
    raw = safe_load_file(path) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"data policy is not valid YAML mapping: {path}")
    source_type_classes = raw.get("source_type_classes") or {}
    if not isinstance(source_type_classes, dict):
        raise ValueError("data policy source_type_classes must be a mapping")
    required_classes = tuple(str(x) for x in (raw.get("required_classes") or ()))
    return DataRuntimePolicy(
        version=int(raw.get("version") or 1),
        policy_name=str(raw.get("policy_name") or "bravo_ai_runtime_data_classification"),
        default_class=str(raw.get("default_class") or "private_operational_data"),
        classes=_load_classes(raw),
        path_rules=_load_path_rules(raw, variables),
        source_type_classes={str(k): str(v) for k, v in source_type_classes.items()},
        required_classes=required_classes,
        variables=variables,
    )


def validate_data_runtime_policy(policy: DataRuntimePolicy) -> list[str]:
    issues: list[str] = []
    missing_classes = sorted(REQUIRED_CLASSES - set(policy.classes))
    if missing_classes:
        issues.append(f"missing required data class(es): {missing_classes}")
    declared_required = set(policy.required_classes)
    missing_required = sorted(REQUIRED_CLASSES - declared_required)
    if missing_required:
        issues.append(f"required_classes missing: {missing_required}")
    if policy.default_class not in policy.classes:
        issues.append(f"default_class is not declared: {policy.default_class}")
    for rule in policy.path_rules:
        if rule.data_class not in policy.classes:
            issues.append(f"{rule.path}: unknown data_class {rule.data_class}")
        if rule.unmanifested_ingestible_policy not in {"ignore", "warn", "fail"}:
            issues.append(
                f"{rule.path}: invalid unmanifested_ingestible_policy "
                f"{rule.unmanifested_ingestible_policy}"
            )
        if rule.duplicate_policy not in {"ignore", "warn", "active_fail", "fail"}:
            issues.append(f"{rule.path}: invalid duplicate_policy {rule.duplicate_policy}")
        if rule.ensure_exists and policy.classes.get(rule.data_class, None):
            cls = policy.classes[rule.data_class]
            if cls.shared_rag_allowed and cls.runtime_scope == "global":
                issues.append(f"{rule.path}: ensure_exists is not allowed for global shared corpus")
    for source_type, data_class in policy.source_type_classes.items():
        if data_class not in policy.classes:
            issues.append(f"source_type {source_type}: unknown data_class {data_class}")
    return issues


def ensure_runtime_policy_paths(policy: DataRuntimePolicy) -> list[str]:
    """Create runtime directories explicitly marked ensure_exists.

    Shared corpus and rule paths are never created here; missing required paths remain
    boot/readiness failures.
    """
    created: list[str] = []
    for rule in policy.path_rules:
        if not rule.ensure_exists:
            continue
        rule.path.mkdir(parents=True, exist_ok=True)
        created.append(rule.path.as_posix())
    return created
