import json
from importlib.metadata import version


def write_report_to_db(report_file: str):
    import psycopg2

    try:
        codegen_version = version("codegen")
    except Exception:
        codegen_version = "dev"

    with open(report_file) as f:
        report = json.load(f)

    # Establish connection
    conn = psycopg2.connect(
        host="localhost", database="swebench", user="swebench", password="swebench"
    )

    # Create a cursor
    cur = conn.cursor()

    try:
        # Single row insert
        cur.execute(
            "INSERT INTO table_name (codegen_version, submitted, completed_instances, resolved_instances, unresolved_instances, empty_patches, error_instances) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                codegen_version,
                report["submitted_instances"],
                report["completed_instances"],
                report["resolved_instances"],
                report["unresolved_instances"],
                report["empty_patch_instances"],
                report["error_instances"],
            ),
        )

        # Commit the transaction
        conn.commit()

    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Error: {e}")

    finally:
        # Close cursor and connection
        cur.close()
        conn.close()
