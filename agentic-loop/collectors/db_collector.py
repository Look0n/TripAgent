import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def inspect_database(db_path: Path, expected_tables: dict) -> tuple[bool, str]:
    path = Path(db_path).resolve()
    if not path.is_file():
        return False, f"Missing runtime database: {path}"
    if not expected_tables:
        return False, "No expected database tables configured."

    evidence = [f"Runtime SQLite database: {path}", "Access: read-only; minimum rows per table: 10."]
    passed = True
    connection = None
    try:
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")  # Consistent snapshot for counts and validation.
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT GLOB 'sqlite_*' ORDER BY name"
        )]
        for missing in sorted(set(expected_tables) - set(tables)):
            passed = False
            evidence.append(f"FAIL: missing expected table {missing}.")

        for table in tables:
            quoted_table = _quote(table)
            columns = connection.execute(f"PRAGMA table_info({quoted_table})").fetchall()
            names = {column[1] for column in columns}
            required = set(expected_tables.get(table, []))
            missing = required - names
            count = connection.execute(f"SELECT COUNT(*) FROM {quoted_table}").fetchone()[0]
            evidence.append(f"Table {table}: {count} rows; minimum count {'PASS' if count >= 10 else 'FAIL'}.")
            evidence.append("Columns: " + ", ".join(
                f"{column[1]} {column[2]}{' PK' if column[5] else ''}" for column in columns
            ))
            if count < 10 or missing:
                passed = False
            if missing:
                evidence.append("FAIL: missing required columns: " + ", ".join(sorted(missing)))

            # Like the lab's field checks, validate stored values rather than SQL text.
            invalid_conditions = []
            for _, name, declared_type, not_null, _, primary_key in columns:
                quoted_column = _quote(name)
                if name in required or not_null or primary_key:
                    invalid_conditions.append(f"{quoted_column} IS NULL")
                    if "TEXT" in declared_type.upper():
                        invalid_conditions.append(f"trim({quoted_column}) = ''")
                declared_type = declared_type.upper()
                if "INT" in declared_type:
                    invalid_conditions.append(
                        f"({quoted_column} IS NOT NULL AND typeof({quoted_column}) != 'integer')"
                    )
                elif any(kind in declared_type for kind in ("REAL", "FLOAT", "DOUBLE")):
                    invalid_conditions.append(
                        f"({quoted_column} IS NOT NULL AND typeof({quoted_column}) NOT IN ('integer', 'real'))"
                    )
                elif "TEXT" in declared_type:
                    invalid_conditions.append(
                        f"({quoted_column} IS NOT NULL AND typeof({quoted_column}) != 'text')"
                    )
            invalid = 0
            if invalid_conditions:
                invalid = connection.execute(
                    f"SELECT COUNT(*) FROM {quoted_table} WHERE " + " OR ".join(invalid_conditions)
                ).fetchone()[0]
            evidence.append(f"Required-field/type validation: {invalid} invalid rows.")
            if invalid:
                passed = False

        violations = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        evidence.append(f"Foreign-key violations: {violations}.")
        if violations:
            passed = False
        evidence.append(
            "Scope: current rows, required fields, declared INTEGER/REAL/TEXT types and existing foreign keys. "
            "Not a seed-provenance, full business-rule or CRUD test. No data was changed."
        )
        return passed, "\n".join(evidence)
    except sqlite3.Error as error:
        return False, "\n".join(evidence + [f"Database query failed: {error}"])
    finally:
        if connection is not None:
            connection.close()


def collect_db_context(service_config: dict, repo_root: Path) -> tuple[bool, str]:
    root = Path(repo_root).resolve()
    compose_file = root / "docker-compose.yml"
    if not compose_file.is_file():
        return False, f"Missing Compose file: {compose_file}"
    for key in ("database_service", "container_db_path", "db_tables"):
        if not service_config.get(key):
            return False, f"Missing database configuration: {key}"

    command = [
        "docker", "compose", "--project-directory", str(root), "-f", str(compose_file),
        "exec", "-T", service_config["database_service"], "python", "-", "--database-probe",
        service_config["container_db_path"], json.dumps(service_config["db_tables"]),
    ]
    try:
        completed = subprocess.run(
            command, input=Path(__file__).read_text(encoding="utf-8"),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=root, timeout=30, check=False,
        )
        if completed.returncode != 0:
            error = completed.stderr.strip() or completed.stdout.strip()
            return False, f"Live DB query could not run in {service_config['database_service']}: {error}"
        response = json.loads(completed.stdout)
        if not isinstance(response, dict) or type(response.get("ok")) is not bool or not isinstance(response.get("evidence"), str):
            return False, "Invalid database probe response."
        return response["ok"], (
            f"Service: {service_config.get('name', 'Unknown service')}\n"
            f"Compose service: {service_config['database_service']}\n" + response["evidence"]
        )
    except FileNotFoundError:
        return False, "Docker CLI not found. Run from a terminal where docker compose is available."
    except subprocess.TimeoutExpired:
        return False, "Live database query timed out after 30 seconds."
    except (OSError, ValueError) as error:
        return False, f"Database evidence collection failed: {error}"


if __name__ == "__main__" and len(sys.argv) == 4 and sys.argv[1] == "--database-probe":
    ok, evidence = inspect_database(
        Path(os.getenv("DATABASE_PATH", sys.argv[2])), json.loads(sys.argv[3])
    )
    print(json.dumps({"ok": ok, "evidence": evidence}))
