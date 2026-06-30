# Tally EDU college management integration platform

A modular, production-ready Python synchronization agent designed to sync custom Tally ERP 9 / TallyPrime student reports (e.g. `StudentDetail`) with a remote cloud-hosted Supabase PostgreSQL store.

---

## Project Structure

```text
sync_agent/
  __init__.py
  config.py
  logger.py
  tally_client.py
  parser.py
  supabase_client.py
  sync_service.py
  main.py

reconcile_tool/         ← Bootstrap tool (pehli baar chalao)
  __init__.py
  main.py
  report.py

requirements.txt
.env.example
schema.sql
README.md
```

---

## Installation & Setup

### 1. Database Schema
Run the contents of [schema.sql](schema.sql) in your Supabase project's SQL Editor to initialize all tables:
* `sync_jobs`
* `students`
* `student_sync_logs`

### 2. Install Dependencies
Install the required packages in your Python environment:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your Supabase connection parameters:
```bash
cp .env.example .env
```
Ensure `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are configured.

---

## Usage Guide

### 1. Running a Single Manual Sync Pass
Run a single synchronized upsert operation and immediately exit:
```bash
python -m sync_agent.main --once
```

### 2. Running in Background Daemon Loop
Runs as a persistent background loop polling every 60 seconds (or immediately on manual database triggers):
```bash
python -m sync_agent.main
```

---

## New Company Bootstrap — Reconciliation Tool

Jab kisi **nayi company mein system lagana ho jahan Tally mein data already hai**, pehle
yeh tool chalao. Yeh Tally aur Oracle ka data compare karega aur `TALLY_SYNC` column set
karega taaki main sync agent cleanly shuru ho sake.

### Kaise Chalayein

```bash
python -m reconcile_tool.main
```

**Tool kya karta hai:**
1. Tally se sab students XML se fetch karta hai
2. Oracle se sab students fetch karta hai
3. Dono compare karta hai — field by field
4. Browser mein interactive HTML report kholta hai
5. Poochta hai: "TALLY_SYNC apply karein? (Y/N)"
6. Oracle update karta hai:
   - `MATCHED` → `TALLY_SYNC = 'S'` (sync agent skip karega)
   - `MISMATCH` → `TALLY_SYNC = 'U'` (Route B Tally mein fix karega)
   - `ONLY IN DB` → NULL rakha (Route B Tally mein create karega)
   - `ONLY IN TALLY` → Route A Oracle mein lega next cycle mein

**Uske baad main sync agent chalao:**
```bash
python -m sync_agent.main
```

### EXE Build (Reconcile Tool)
```cmd
pyinstaller --onefile --name="TallyReconcile" reconcile_tool/main.py
```
`.env` file ko `TallyReconcile.exe` ke saath same folder mein rakhein.

---

## Windows Deployment Options

### 1. Run as a Windows Background Task (Task Scheduler)
To run the sync agent silently in the background on startup:
1. Open **Task Scheduler** in Windows.
2. Click **Create Basic Task**.
3. Set Trigger to **When the computer starts**.
4. Set Action to **Start a Program**.
5. Set Program/script to your Python executable path:
   `C:\Users\<user>\AppData\Local\Programs\Python\Python312\python.exe`
6. Set Arguments to:
   `-m sync_agent.main`
7. Set "Start in" to the directory where your project folder resides (e.g. `C:\Users\<user>\desktop`).
8. Under **Conditions**, uncheck "Start the task only if the computer is on AC power".
9. Under **Settings**, check "Run task as soon as possible after a scheduled start is missed" and set "If the task fails, restart every: 1 minute".

### 2. Creating a Compiled Windows Executable (.exe)
You can compile the sync agent into a standalone portable `.exe` that runs without requiring a Python installation using `pyinstaller`:

1. Install PyInstaller:
   ```cmd
   pip install pyinstaller
   ```
2. Compile into a single file with Console output:
   ```cmd
   pyinstaller --onefile --name="TallySyncAgent" --copy-metadata="supabase" --copy-metadata="postgrest" sync_agent/main.py
   ```
3. The standalone executable `TallySyncAgent.exe` will be generated inside the `dist/` directory. Copy your `.env` file alongside the `.exe` to run it on any Windows Tally PC.

