"""
migrate_full_name.py
====================
Splits the `clients.full_name` column into separate columns:
  - fname      (first name)
  - mi         (middle initial, e.g. "G")  — stored WITHOUT the dot
  - lname      (last name)
  - name_ext   (suffix such as JR, SR, II, III, IV, etc.)

Expected full_name format:  "JERIC G. BOLEZA JR"
                              <fname> <MI.> <lname> <name_ext?>

Run modes
---------
  python migrate_full_name.py            # dry-run: shows what would change
  python migrate_full_name.py --apply    # applies the migration for real

After applying, a rollback SQL file is created in the same directory so you
can undo if needed.
"""

import sys
import os
import re
import datetime

# ── locate project root so we can import db.py ──────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from db import get_db_cursor  # noqa: E402  (project import after sys.path tweak)

# ── name-extension tokens ────────────────────────────────────────────────────
NAME_EXTENSIONS = {"JR", "SR", "II", "III", "IV", "V", "VI", "VII", "VIII"}


def parse_full_name(full_name: str):
    """
    Parse a full_name string into (fname, mi, lname, name_ext).

    Expected format:  FIRST [MI.] LAST [EXT]
    Examples
    --------
    "JERIC G. BOLEZA JR"  → ("JERIC", "G", "BOLEZA", "JR")
    "MARIA SANTOS"        → ("MARIA", "",  "SANTOS", "")
    "JUAN DELA CRUZ III"  → ("JUAN",  "",  "DELA CRUZ", "III")
    "ANA M. REYES"        → ("ANA",   "M", "REYES",  "")
    """
    if not full_name or not full_name.strip():
        return ("", "", "", "")

    # Normalise whitespace
    raw = full_name.strip()
    tokens = raw.split()

    fname = ""
    mi = ""
    lname = ""
    name_ext = ""

    if not tokens:
        return ("", "", "", "")

    # Pull the first token as fname
    fname = tokens[0]
    remaining = tokens[1:]

    # Check if the last token is a name extension
    if remaining and remaining[-1].upper().rstrip(".") in NAME_EXTENSIONS:
        name_ext = remaining[-1].upper().rstrip(".")
        remaining = remaining[:-1]

    # Check if the first remaining token looks like a middle initial (1-2 chars + optional dot)
    mi_pattern = re.compile(r"^([A-Z]{1,2})\.?$", re.IGNORECASE)
    if remaining and mi_pattern.match(remaining[0]):
        mi = remaining[0].upper().rstrip(".")
        remaining = remaining[1:]

    # Everything left is the last name (handles compound surnames like DELA CRUZ)
    lname = " ".join(remaining) if remaining else ""

    return (fname.upper(), mi.upper(), lname.upper(), name_ext.upper())


# ── SQL helpers ───────────────────────────────────────────────────────────────

ADD_COLUMNS_SQL = """
ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS fname    VARCHAR(100) NULL AFTER full_name,
    ADD COLUMN IF NOT EXISTS lname    VARCHAR(100) NULL AFTER fname,
    ADD COLUMN IF NOT EXISTS mi       VARCHAR(10)  NULL AFTER lname,
    ADD COLUMN IF NOT EXISTS name_ext VARCHAR(20)  NULL AFTER mi;
"""

# ── main logic ────────────────────────────────────────────────────────────────

def run(apply: bool):
    dry = not apply
    mode_label = "DRY-RUN" if dry else "APPLY"
    print(f"\n{'='*60}")
    print(f"  migrate_full_name.py  [{mode_label}]")
    print(f"{'='*60}\n")

    # ── Step 1: Add new columns (skip in dry-run) ─────────────────────────
    if not dry:
        print("[1/4] Adding new columns (fname, lname, mi, name_ext)…")
        try:
            with get_db_cursor(commit=True) as cur:
                for stmt in ADD_COLUMNS_SQL.strip().split(";"):
                    stmt = stmt.strip()
                    if stmt:
                        cur.execute(stmt)
            print("      Columns added (or already existed).\n")
        except Exception as exc:
            print(f"      ERROR adding columns: {exc}\n")
            sys.exit(1)
    else:
        print("[1/4] [DRY-RUN] Would add columns: fname, lname, mi, name_ext\n")

    # ── Step 2: Fetch all clients ─────────────────────────────────────────
    print("[2/4] Fetching all clients…")
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT id, client_id, full_name FROM clients")
            clients = cur.fetchall()
    except Exception as exc:
        print(f"      ERROR fetching clients: {exc}\n")
        sys.exit(1)

    print(f"      Found {len(clients)} client(s).\n")

    # ── Step 3: Parse & preview / update ─────────────────────────────────
    print("[3/4] Parsing full_name values…\n")
    header = f"{'ID':>6}  {'CLIENT_ID':<15}  {'FULL_NAME':<30}  {'FNAME':<12}  {'MI':<4}  {'LNAME':<20}  {'EXT'}"
    print(header)
    print("-" * len(header))

    parsed_rows = []
    for row in clients:
        rid        = row["id"]
        client_id  = row["client_id"]
        full_name  = row["full_name"] or ""
        fname, mi, lname, name_ext = parse_full_name(full_name)
        parsed_rows.append((rid, client_id, full_name, fname, mi, lname, name_ext))
        print(f"{rid:>6}  {client_id:<15}  {full_name:<30}  {fname:<12}  {mi:<4}  {lname:<20}  {name_ext}")

    print()

    if dry:
        print("[4/4] [DRY-RUN] No changes written. Re-run with --apply to commit.\n")
        return

    # ── Step 4: Write parsed data back to DB ──────────────────────────────
    print("[4/4] Updating rows in clients table…")
    update_sql = """
        UPDATE clients
        SET fname = %s, mi = %s, lname = %s, name_ext = %s
        WHERE id = %s
    """
    undo_lines = []  # for rollback script

    try:
        with get_db_cursor(commit=True) as cur:
            for rid, client_id, full_name, fname, mi, lname, name_ext in parsed_rows:
                cur.execute(update_sql, (fname, mi, lname, name_ext, rid))
                # Build undo SQL line (restore original full_name, clear new cols)
                safe_fn = full_name.replace("'", "''")
                undo_lines.append(
                    f"UPDATE clients SET fname=NULL, mi=NULL, lname=NULL, name_ext=NULL, "
                    f"full_name='{safe_fn}' WHERE id={rid};"
                )
        print(f"      {len(parsed_rows)} row(s) updated successfully.\n")
    except Exception as exc:
        print(f"      ERROR during update: {exc}\n")
        sys.exit(1)

    # ── Write rollback script ─────────────────────────────────────────────
    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    undo_file = os.path.join(SCRIPT_DIR, f"undo_migrate_full_name_{ts}.sql")
    with open(undo_file, "w", encoding="utf-8") as f:
        f.write("-- Rollback: restore full_name and clear split columns\n")
        f.write("-- Generated by migrate_full_name.py\n\n")
        f.write("USE hrmo_elog_db;\n\n")
        for line in undo_lines:
            f.write(line + "\n")
        # Optionally drop the added columns
        f.write(
            "\n-- Uncomment the lines below to also DROP the new columns:\n"
            "-- ALTER TABLE clients\n"
            "--     DROP COLUMN fname,\n"
            "--     DROP COLUMN lname,\n"
            "--     DROP COLUMN mi,\n"
            "--     DROP COLUMN name_ext;\n"
        )
    print(f"      Rollback SQL written to:\n      {undo_file}\n")

    print("Migration complete!\n")
    print("NOTE: The original `full_name` column is still present.")
    print("      After verifying the new columns, you may drop it with:")
    print("        ALTER TABLE clients DROP COLUMN full_name;\n")


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    apply_mode = "--apply" in sys.argv
    run(apply=apply_mode)
