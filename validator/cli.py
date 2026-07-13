"""``tbom-validate`` console script.

Validates one or more supplied JSON files against the InvarOS TBoM profile
schema selected by each file's ``profile_id``, reusing the same profile
dispatch and schema loading as ``validate_examples.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import jsonschema
from referencing.exceptions import Unresolvable

from .validate_examples import load_json, validate_payload


def validate_file(path: Path) -> None:
    payload = load_json(path)
    validate_payload(payload)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tbom-validate",
        description=(
            "Validate InvarOS Topology Bill of Materials (TBoM) JSON "
            "artifacts against the schema selected by profile_id and "
            "profile_version."
        ),
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="TBoM JSON artifact file(s) to validate",
    )
    args = parser.parse_args(argv)

    exit_code = 0
    for path in args.files:
        try:
            validate_file(path)
        except FileNotFoundError:
            print(f"ERROR {path}: file not found", file=sys.stderr)
            exit_code = 1
        except json.JSONDecodeError as exc:
            print(f"ERROR {path}: invalid JSON: {exc}", file=sys.stderr)
            exit_code = 1
        except ValueError as exc:
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            exit_code = 1
        except jsonschema.exceptions.ValidationError as exc:
            print(f"FAIL {path}: schema validation error: {exc.message}", file=sys.stderr)
            exit_code = 1
        except (jsonschema.exceptions.SchemaError, Unresolvable) as exc:
            print(f"ERROR {path}: schema resolution error: {exc}", file=sys.stderr)
            exit_code = 1
        else:
            print(f"PASS {path}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
