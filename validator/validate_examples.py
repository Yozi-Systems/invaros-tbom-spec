from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]


def _schema_root() -> Path:
    """Locate authoritative schemas in a checkout or an installed wheel."""
    checkout = ROOT / "schemas"
    if checkout.is_dir():
        return checkout
    installed = Path(sys.prefix) / "share" / "invaros-tbom-spec" / "schemas"
    if installed.is_dir():
        return installed
    raise RuntimeError("InvarOS TBoM schema bundle is unavailable")


SCHEMA_ROOT = _schema_root()

PROFILE_SCHEMAS = {
    ("invaros.tbom.profile.agentic_topology", "3.0.0"): (
        SCHEMA_ROOT
        / "agentic/"
        "invaros-agentic-topology-tbom-profile.schema.json"
    ),
    ("invaros.tbom.profile.edge_network_topology", "3.0.0"): (
        SCHEMA_ROOT
        / "edge-network/"
        "invaros-edge-network-topology-tbom-profile.schema.json"
    ),
    ("invaros.tbom.profile.edge_network_topology", "4.0.0"): (
        SCHEMA_ROOT / "edge-network-topology/4.0.0/schema.json"
    ),
}

LEGACY_PROFILE_DEFAULTS = {
    "invaros.tbom.profile.agentic_topology": "3.0.0",
    "invaros.tbom.profile.edge_network_topology": "3.0.0",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def schema_store() -> dict[str, dict]:
    """Load all locally bundled schemas for offline reference resolution."""
    store: dict[str, dict] = {}
    for path in sorted(SCHEMA_ROOT.rglob("*.json")):
        schema = load_json(path)
        schema_id = schema.get("$id")
        if schema_id:
            store[schema_id] = schema
    return store


def schema_registry() -> Registry:
    """Build an offline modern referencing registry for all bundled schemas."""
    resources = []
    for schema_id, schema in schema_store().items():
        resources.append((schema_id, Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def profile_key(payload: dict) -> tuple[str, str]:
    profile_id = payload.get("profile_id")
    if profile_id not in LEGACY_PROFILE_DEFAULTS:
        raise ValueError(f"unsupported or missing profile_id: {profile_id!r}")
    profile_version = payload.get("profile_version")
    if profile_version is None:
        profile_version = LEGACY_PROFILE_DEFAULTS[profile_id]
    key = (profile_id, profile_version)
    if key not in PROFILE_SCHEMAS:
        raise ValueError(
            "unsupported profile_id/profile_version: "
            f"{profile_id!r}/{profile_version!r}"
        )
    return key


def validate_payload(payload: dict) -> None:
    schema = load_json(PROFILE_SCHEMAS[profile_key(payload)])
    validator_class = jsonschema.validators.validator_for(schema)
    validator_class.check_schema(schema)
    validator_class(
        schema,
        registry=schema_registry(),
        format_checker=jsonschema.FormatChecker(),
    ).validate(payload)

    if profile_key(payload) == (
        "invaros.tbom.profile.edge_network_topology",
        "4.0.0",
    ):
        try:
            from .profile4_semantics import validate_profile4_semantics
        except ImportError:  # direct script execution
            from validator.profile4_semantics import validate_profile4_semantics

        validate_profile4_semantics(payload)


def validate_example(path: Path) -> None:
    payload = load_json(path)
    try:
        validate_payload(payload)
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc


def main() -> None:
    examples = sorted((ROOT / "examples").glob("*/*.json"))

    if not examples:
        raise SystemExit("No example artifacts found.")

    for example in examples:
        validate_example(example)
        print(f"PASS {example.relative_to(ROOT)}")

    print(f"\nValidated {len(examples)} TBoM example artifacts.")


if __name__ == "__main__":
    main()
