"""
Synctal Bootstrap Reconciliation Tool
======================================
Nayi company ke liye pehle chalao. Yeh tool:
  1. Tally se saare student records fetch karta hai
  2. Oracle DB se saare student records fetch karta hai
  3. Dono ko compare karta hai
  4. HTML report generate karta hai
  5. Oracle mein TALLY_SYNC set karta hai:
       MATCHED   → 'S'  (skip, already in sync)
       MISMATCH  → 'U'  (sync agent Route B fix karega)
       ONLY_DB   → NULL (sync agent Route B Tally mein create karega)

Usage:
    python -m reconcile_tool.main

EXE build:
    pyinstaller --onefile --name="TallyReconcile" reconcile_tool/main.py
"""

import os
import sys
import re
import webbrowser
from datetime import datetime

# ─── Path setup so imports work both in .py and compiled .exe ─────────────────
# When frozen by PyInstaller, sys._MEIPASS holds the temp extraction dir
if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, _BASE)

# ─── Now safe to import sync_agent modules ────────────────────────────────────
from sync_agent.config import settings
from sync_agent.logger import setup_logger
from sync_agent.tally_client import TallyClient, clean_group_name
from sync_agent.parser import parse_students_xml
from sync_agent.oracle_client import OracleSyncClient
from reconcile_tool.report import generate_report

logger = setup_logger("reconcile_tool", "INFO")

# ─── Fields to compare between Tally and Oracle ──────────────────────────────
COMPARE_FIELDS = [
    "student_name",
    "student_class",
    "roll_no",
    "registration_no",
    "course",
    "session",
    "father_name",
    "mother_name",
    "gender",
    "mobile",
    "email",
    "is_left",
]


# ─── Comparison helpers ───────────────────────────────────────────────────────

def _normalize_str(val) -> str:
    if val is None:
        return ""
    return re.sub(r'\s+', ' ', str(val)).strip().lower()


def _normalize_class(val) -> str:
    if not val:
        return ""
    return clean_group_name(str(val)).strip().lower()


def _normalize_bool(val) -> bool:
    return bool(val) and str(val).lower() not in ("false", "0", "no", "none", "")


def _records_differ(tally_rec: dict, db_rec: dict) -> list:
    """
    Returns list of field names that differ between tally_rec and db_rec.
    Empty list means records match.
    """
    diff_fields = []
    for field in COMPARE_FIELDS:
        t_val = tally_rec.get(field)
        d_val = db_rec.get(field)

        if field == "student_class":
            if _normalize_class(t_val) != _normalize_class(d_val):
                diff_fields.append(field)
        elif field == "is_left":
            if _normalize_bool(t_val) != _normalize_bool(d_val):
                diff_fields.append(field)
        else:
            if _normalize_str(t_val) != _normalize_str(d_val):
                diff_fields.append(field)

    return diff_fields


# ─── Oracle TALLY_SYNC writer ─────────────────────────────────────────────────

def apply_tally_sync_statuses(
    oracle: OracleSyncClient,
    matched_enrollments: list,
    mismatch_enrollments: list
) -> None:
    """
    Writes TALLY_SYNC values to Oracle:
      - Matched   → 'S'
      - Mismatch  → 'U'
      - Only in DB → leave NULL (no touch needed)
    """
    conn = None
    cur = None
    try:
        conn = oracle._get_connection()
        cur = conn.cursor()

        # Batch update matched → 'S'
        if matched_enrollments:
            print(f"\n  Updating {len(matched_enrollments)} matched records → TALLY_SYNC = 'S' ...")
            for enrl_no in matched_enrollments:
                cur.execute(
                    f"UPDATE {settings.DB_SCHEMA}.STUDENT_MASTER_DATA SET TALLY_SYNC = 'S' WHERE ENRL_NO = :e",
                    {"e": enrl_no}
                )
            print(f"  ✅ {len(matched_enrollments)} records marked 'S'")

        # Batch update mismatch → 'U'
        if mismatch_enrollments:
            print(f"  Updating {len(mismatch_enrollments)} mismatched records → TALLY_SYNC = 'U' ...")
            for enrl_no in mismatch_enrollments:
                cur.execute(
                    f"UPDATE {settings.DB_SCHEMA}.STUDENT_MASTER_DATA SET TALLY_SYNC = 'U' WHERE ENRL_NO = :e",
                    {"e": enrl_no}
                )
            print(f"  ✅ {len(mismatch_enrollments)} records marked 'U'")

        conn.commit()
        print(f"\n  Oracle TALLY_SYNC column updated successfully! ✅")

    except Exception as e:
        print(f"\n  ❌ Oracle update failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("  ⚡ Synctal Bootstrap Reconciliation Tool")
    print("=" * 62)
    print(f"  Tally URL  : {settings.TALLY_URL}")
    print(f"  Oracle DSN : {settings.DB_CONNECT_STRING}")
    print(f"  Schema     : {settings.DB_SCHEMA}")
    print("=" * 62)
    print()

    tally_client = TallyClient()
    oracle = OracleSyncClient()

    # ── Step 1: Fetch from Tally ──────────────────────────────────────────────
    print("📡 Step 1: Tally se students fetch kar rahe hain...")
    try:
        xml_data = tally_client.fetch_student_details()
        tally_students = parse_students_xml(xml_data)
        print(f"  ✅ Tally se {len(tally_students)} records mile")
    except Exception as e:
        print(f"  ❌ Tally connection failed: {e}")
        print("  Tally Prime open hai? Port sahi hai?")
        input("\nPress Enter to exit...")
        return

    # ── Step 2: Fetch ledger parent map (for is_left detection) ──────────────
    print("\n🗺️  Step 2: Tally ledger parent map fetch kar rahe hain...")
    try:
        ledger_parents = tally_client.fetch_all_ledgers_with_parent()
        print(f"  ✅ {len(ledger_parents)} ledger parent mappings mile")
    except Exception as e:
        print(f"  ⚠️  Ledger parent map nahi mila (is_left check affected): {e}")
        ledger_parents = {}

    # Resolve is_left for each tally student from ledger parent
    for s in tally_students:
        en = str(s.get("enrollment_no", "")).strip().lower()
        name = str(s.get("student_name", "")).strip()
        expected = f"{name} -{s.get('enrollment_no', '')}".lower() if name else en
        parent = ledger_parents.get(en) or ledger_parents.get(expected)
        tally_is_left = bool(parent and (parent.startswith("Left") or parent.startswith("Passout")))
        s["is_left"] = tally_is_left

    # Index tally records by enrollment_no
    tally_map = {str(s["enrollment_no"]).strip(): s for s in tally_students if s.get("enrollment_no")}

    # ── Step 3: Fetch from Oracle ─────────────────────────────────────────────
    print("\n🗄️  Step 3: Oracle DB se students fetch kar rahe hain...")
    try:
        db_students = oracle.get_all_students()
        print(f"  ✅ Oracle se {len(db_students)} records mile")
    except Exception as e:
        print(f"  ❌ Oracle connection failed: {e}")
        input("\nPress Enter to exit...")
        return

    db_map = {str(s["enrollment_no"]).strip(): s for s in db_students if s.get("enrollment_no")}

    # ── Step 4: Compare ───────────────────────────────────────────────────────
    print("\n🔍 Step 4: Compare kar rahe hain...")

    matched = []
    mismatched = []
    only_in_db = []
    only_in_tally = []

    all_enrollments = set(tally_map.keys()) | set(db_map.keys())

    for en in all_enrollments:
        t_rec = tally_map.get(en)
        d_rec = db_map.get(en)

        if t_rec and d_rec:
            diff_fields = _records_differ(t_rec, d_rec)
            if diff_fields:
                mismatched.append({
                    "enrollment_no": en,
                    "tally": t_rec,
                    "db": d_rec,
                    "diff_fields": diff_fields
                })
            else:
                matched.append(d_rec)

        elif d_rec and not t_rec:
            only_in_db.append(d_rec)

        elif t_rec and not d_rec:
            only_in_tally.append(t_rec)

    print(f"  ✅ Matched       : {len(matched)}")
    print(f"  ⚠️  Mismatch      : {len(mismatched)}")
    print(f"  🔵 Only in Oracle: {len(only_in_db)}")
    print(f"  🟣 Only in Tally : {len(only_in_tally)}")

    # ── Step 5: Generate HTML Report ─────────────────────────────────────────
    print("\n📊 Step 5: HTML Report generate kar rahe hain...")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"reconcile_report_{ts}.html"
    report_path = os.path.join(_BASE, report_name)

    generate_report(
        matched=matched,
        mismatched=mismatched,
        only_in_db=only_in_db,
        only_in_tally=only_in_tally,
        compared_fields=COMPARE_FIELDS,
        output_path=report_path
    )
    print(f"  ✅ Report saved: {report_path}")

    try:
        webbrowser.open(f"file:///{report_path.replace(os.sep, '/')}")
        print("  🌐 Browser mein report khul gayi!")
    except Exception:
        print("  (Browser auto-open nahi hua, manually kholein)")

    # ── Step 6: Apply TALLY_SYNC ──────────────────────────────────────────────
    print()
    print("─" * 62)
    print("  TALLY_SYNC Plan:")
    print(f"    Matched ({len(matched)})    → 'S' (sync agent skip karega)")
    print(f"    Mismatch ({len(mismatched)})   → 'U' (Route B Tally mein fix karega)")
    print(f"    Only in DB ({len(only_in_db)}) → NULL (Route B Tally mein create karega)")
    print(f"    Only in Tally ({len(only_in_tally)}) → Route A Oracle mein lega")
    print("─" * 62)
    print()

    answer = input("  Oracle mein TALLY_SYNC apply karein? (Y/N): ").strip().upper()

    if answer == "Y":
        matched_enrollments = [str(s.get("enrollment_no", "")).strip() for s in matched if s.get("enrollment_no")]
        mismatch_enrollments = [str(r.get("enrollment_no", "")).strip() for r in mismatched if r.get("enrollment_no")]

        apply_tally_sync_statuses(oracle, matched_enrollments, mismatch_enrollments)

        print()
        print("=" * 62)
        print("  ✅ Bootstrap complete!")
        print()
        print("  Ab sync agent chalao:")
        print("    python -m sync_agent.main")
        print()
        print("  Sync agent ab:")
        print(f"    - {len(mismatch_enrollments)} mismatched students Tally mein fix karega")
        print(f"    - {len(only_in_db)} new students Tally mein create karega")
        print(f"    - {len(matched_enrollments)} matched students skip karega")
        print("=" * 62)
    else:
        print("\n  ❌ Apply nahi kiya. Koi changes nahi hue Oracle mein.")
        print("  Report browser mein dekh sakte ho for reference.")

    print()
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
