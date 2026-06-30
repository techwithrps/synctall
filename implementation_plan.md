# Bootstrap Reconciliation Tool — TallyReconcile.exe

## Kya Karna Hai

Ek alag standalone Python tool banana hai jo **nayi company ke liye pehle chalaate hain** — 
yeh Tally aur Oracle DB ka data compare karega, mismatches dikhayega, aur 
`TALLY_SYNC` column ko theek set kar dega taaki main sync agent cleanly shuru ho sake.

---

## Tool ka Flow

```
[Start]
  ↓
Tally se saare students fetch karo (XML via TallyClient)
  ↓
Oracle se saare students fetch karo (STUDENT_MASTER_DATA)
  ↓
Dono ko ENRL_NO se match karo
  ↓
3 categories mein baanto:
  - MATCHED      → Dono mein hai, fields same hain
  - MISMATCH     → Dono mein hai, kuch fields alag hain
  - ONLY_IN_DB   → Oracle mein hai, Tally mein nahi
  - ONLY_IN_TALLY→ Tally mein hai, Oracle mein nahi
  ↓
HTML Report generate karo (browser mein khule)
  ↓
User se poochho: "TALLY_SYNC set karna hai?"
  - MATCHED   → 'S' (already synced, chhod do)
  - MISMATCH  → 'U' (re-sync needed)
  - ONLY_IN_DB→ NULL (naya hai, sync karna hoga)
  ↓
Oracle update karo
  ↓
Done ✅
```

---

## Proposed Changes

### [NEW] `reconcile_tool/` — Standalone Package

#### [NEW] `reconcile_tool/__init__.py`
Empty init file.

#### [NEW] `reconcile_tool/reconcile.py`
Main entry point. Handles:
- Tally fetch (reuses `sync_agent.tally_client.TallyClient`)
- Oracle fetch (reuses `sync_agent.oracle_client.OracleSyncClient`)
- Compare logic — field by field (reuses `sync_agent.sync_service.SyncService._records_differ`)
- Output: Print summary to console
- Generate `reconcile_report.html` in same directory
- Ask user: Apply TALLY_SYNC changes? (Y/N)
- Apply Oracle updates

#### [NEW] `reconcile_tool/report.py`
HTML report generator — beautiful table showing:
- Summary cards (Matched, Mismatch, Only in DB, Only in Tally)
- Per-student diff table with highlighted mismatched fields
- Export to `reconcile_report_YYYYMMDD_HHMMSS.html`

#### [NEW] `reconcile_tool/requirements.txt`
Same as sync_agent requirements (oracledb, requests, python-dotenv, pydantic-settings)

---

## Fields jo Compare Honge

| Field | Tally Source | Oracle Source |
|-------|-------------|---------------|
| student_name | KGSTUDNAME | STUDENT_NAME |
| student_class | KGSTUDCLASS | BRANCH |
| roll_no | KGROLLNO | ROLL_NO |
| registration_no | KGREGTNO | REG_NO |
| course | KGCOURSE | COURSE |
| session | KGSESSION | SESSION_YEAR |
| father_name | KGFATHERNAME | FATHER_NAME |
| mother_name | KGMOTHERNAME | MOTHER_NAME |
| gender | KGSEX | STUDENT_GENDER |
| mobile | KGMOBNO | STUDENT_MOBILE |
| email | KGEMAL | STUDENT_EMAIL_ID |
| is_left | Parent group check | ACTIVE_STATUS_ID / STUDENT_STATUS |

---

## TALLY_SYNC Assignment Logic

| Result | TALLY_SYNC Value | Reason |
|--------|-----------------|--------|
| MATCHED | `'S'` | Already in sync, skip karo |
| MISMATCH | `'U'` | Tally → Oracle update hoga via main agent |
| ONLY_IN_DB | `NULL` (leave) | Main agent Route B se Tally mein create hoga |
| ONLY_IN_TALLY | N/A | Oracle mein nahi hai, Route A se aayega |

---

## Verification Plan

### Manual Testing
1. `.env` properly configured hai (Tally URL + Oracle credentials)
2. Tool chalao: `python -m reconcile_tool.reconcile`
3. Console mein summary dikhe
4. HTML report browser mein khule
5. Oracle mein TALLY_SYNC values verify karo

### EXE Build
```cmd
pyinstaller --onefile --name="TallyReconcile" reconcile_tool/reconcile.py
```

---

## Open Questions

> [!IMPORTANT]
> **HTML Report browser mein auto-open karein ya sirf file save karein?**
> Default: auto-open (webbrowser module se)

> [!IMPORTANT]  
> **Sirf compare + report chahiye, ya TALLY_SYNC apply bhi tool se hi karein?**
> Plan mein dono hai — Y/N prompt se user decide karega
YEH 
> [!IMPORTANT]
> **Company ID hardcode karein (10) ya `.env` se configurable banayein?**
