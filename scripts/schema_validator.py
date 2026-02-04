#!/usr/bin/env python3
"""
Schema Validator - Database schema validation (Adapted for Zeepub-bot from global skills)
Validates database schemas and checks for common issues.

Usage:
    python scripts/schema_validator.py <project_path>
"""

import re
import sys
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def find_schema_files(project_path: Path) -> list:
    """Find database schema files (SQLAlchemy models and SQL migrations)."""
    schemas = []

    # SQLAlchemy models
    model_files = list(project_path.glob("**/models/*.py"))
    schemas.extend([("sqlalchemy", f) for f in model_files if not f.name.startswith("__")])

    # SQL migrations
    sql_files = list(project_path.glob("alembic/versions/*.py"))  # Alembic migrations
    schemas.extend([("alembic", f) for f in sql_files])

    return schemas[:20]


def validate_sqlalchemy_model(file_path: Path) -> list:
    """Basic validation for SQLAlchemy models."""
    issues = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        # Check for Base inheritance
        if "class" in content and "Base" not in content:
            # Not a strict error but worth checking
            pass

        # Check for __tablename__
        classes = re.findall(r"class\s+(\w+)", content)
        for cls in classes:
            if cls not in [
                "Base",
                "UserRole",
                "BookType",
            ]:  # Skip some common non-table classes
                if "__tablename__" not in content and f"class {cls}" in content:
                    # Very simple check
                    pass

        # Check for indexing on foreign keys (Common optimization)
        fk_fields = re.findall(r'ForeignKey\([\'"](\w+)\.id[\'"]', content)
        for fk in fk_fields:
            if "index=True" not in content:
                issues.append(
                    f"Consider adding index=True to foreign key for '{fk}' in {file_path.name}"
                )

    except Exception as e:
        issues.append(f"Error reading {file_path.name}: {str(e)}")

    return issues


def main():
    project_path = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    print(f"\n{'=' * 60}")
    print("[SCHEMA VALIDATOR] Zeepub-bot Context")
    print(f"{'=' * 60}")
    print(f"Project: {project_path}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    schemas = find_schema_files(project_path)
    print(f"Found {len(schemas)} relevant schema/model files")

    all_issues = []
    for schema_type, file_path in schemas:
        if schema_type == "sqlalchemy":
            issues = validate_sqlalchemy_model(file_path)
            if issues:
                all_issues.append(
                    {"file": str(file_path.relative_to(project_path)), "issues": issues}
                )

    if not all_issues:
        print("\nNo significant schema issues found in models!")
    else:
        print("\nPotential issues found:")
        for item in all_issues:
            print(f"\n{item['file']}:")
            for issue in item["issues"]:
                print(f"  - {issue}")

    print(
        "\n[VALIDATOR] Recommended: Check for missing created_at/updated_at columns in new tables."
    )
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
