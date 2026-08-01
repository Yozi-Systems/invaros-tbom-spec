# Trust Bill of Materials Standard Specification (`invaros-tbom-spec`)

## 1. What is this repository?
**Component Name:** Trust Bill of Materials (TBOM) Standard Specification Repository (`invaros-tbom-spec`)  
**Owner:** Yozi Systems Standards & Specification Governance Board  
**Scope:** Canonical JSON-LD schemas, profile specifications, algorithm definitions, and conformance suites for the TBOM open standard.

## 2. What problem does it solve?
Defines an open, vendor-neutral standard for declaring, verifying, and auditing software trust metadata, cryptographic provenance, and runtime governance policies.

## 3. How is it built and tested?
- **Prerequisites:** Python 3.10+, `pytest`, `jsonschema`
- **Validation & Test Commands:**
  ```bash
  python3 scripts/validate_schemas.py
  pytest conformance/
  ```

## 4. Where is the canonical institutional documentation?
Canonical platform standards, corporate strategy, and governance rules reside in central `yozi-docs`:
- 📍 **Canonical Platform Specs:** [`yozi-docs/canonical-specs/`](file:///home/yozi/yozi-docs/canonical-specs/)
- 📍 **TBOM Explorer Products:** [`yozi-docs/products/tbom-explorer/`](file:///home/yozi/yozi-docs/products/tbom-explorer/)

## 5. Which repositories does it depend on?
- **Upstream Dependencies:** None (Authoritative Standard Repository)
- **Downstream Consumers:** [`invaros-runtime`](file:///home/yozi/invaros-runtime), [`invaros-authority`](file:///home/yozi/invaros-authority), [`invaros-development-tbom-explorer`](file:///home/yozi/invaros-development-tbom-explorer), [`invaros-enterprise-tbom-explorer`](file:///home/yozi/invaros-enterprise-tbom-explorer)

## 6. Where should new documentation for this repository be placed?
- **Repository-Local Technical Documentation (`docs/` & `SPECIFICATION.md`):** Normative specifications (`SPECIFICATION.md`), algorithm definitions (`docs/algorithms/`), registry parameter rules (`docs/registries/`), and conformance guides.
- **Central Institutional Documentation (`yozi-docs/`):** TBOM commercial strategy, adoption proposals, and cross-repo governance roadmaps (`yozi-docs/`).
