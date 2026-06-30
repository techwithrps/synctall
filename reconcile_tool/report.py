"""
HTML Report Generator for Tally ↔ Oracle Reconciliation Tool.
Generates a beautiful, interactive single-file HTML report.
"""

from datetime import datetime
from typing import Dict, List, Any


def _escape(val) -> str:
    if val is None:
        return "<span class='null'>—</span>"
    s = str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    return s or "<span class='null'>—</span>"


def _field_label(field: str) -> str:
    return field.replace("_", " ").title()


def generate_report(
    matched: List[Dict],
    mismatched: List[Dict],
    only_in_db: List[Dict],
    only_in_tally: List[Dict],
    compared_fields: List[str],
    output_path: str
) -> str:
    """
    Generates a full HTML reconciliation report and saves it to output_path.
    Returns the output_path string.
    """
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    total = len(matched) + len(mismatched) + len(only_in_db) + len(only_in_tally)

    # ─── Build row HTMLs ───────────────────────────────────────────────────────

    def make_matched_rows():
        rows = []
        for s in matched:
            en = _escape(s.get("enrollment_no"))
            name = _escape(s.get("student_name"))
            cls = _escape(s.get("student_class"))
            rows.append(f"""
            <tr class="row-matched">
                <td><span class="badge badge-matched">MATCHED</span></td>
                <td>{en}</td>
                <td>{name}</td>
                <td>{cls}</td>
                <td><span class="tag-s">→ 'S'</span></td>
            </tr>""")
        return "\n".join(rows) if rows else '<tr><td colspan="5" class="empty-row">Koi matched record nahi mila.</td></tr>'

    def make_mismatch_rows():
        rows = []
        for s in mismatched:
            en = _escape(s.get("enrollment_no"))
            name = _escape(s.get("tally", {}).get("student_name") or s.get("db", {}).get("student_name"))
            diff_fields = s.get("diff_fields", [])
            diff_html = "".join(f'<span class="diff-tag">{_field_label(f)}</span>' for f in diff_fields)

            detail_rows = []
            for field in compared_fields:
                t_val = s.get("tally", {}).get(field)
                d_val = s.get("db", {}).get(field)
                is_diff = field in diff_fields
                cls = "diff-row" if is_diff else ""
                detail_rows.append(f"""
                    <tr class="{cls}">
                        <td>{_field_label(field)}</td>
                        <td class="val-tally">{_escape(t_val)}</td>
                        <td class="val-db">{_escape(d_val)}</td>
                    </tr>""")

            row_id = f"mismatch-{en}"
            rows.append(f"""
            <tr class="row-mismatch expandable" onclick="toggleDetail('{row_id}')">
                <td><span class="badge badge-mismatch">MISMATCH</span></td>
                <td>{en}</td>
                <td>{name}</td>
                <td>{diff_html}</td>
                <td><span class="tag-u">→ 'U'</span></td>
            </tr>
            <tr class="detail-row" id="{row_id}">
                <td colspan="5">
                    <table class="diff-detail-table">
                        <thead><tr>
                            <th>Field</th>
                            <th>🔵 Tally Value</th>
                            <th>🟠 Oracle Value</th>
                        </tr></thead>
                        <tbody>{"".join(detail_rows)}</tbody>
                    </table>
                </td>
            </tr>""")
        return "\n".join(rows) if rows else '<tr><td colspan="5" class="empty-row">Koi mismatch nahi mila.</td></tr>'

    def make_only_db_rows():
        rows = []
        for s in only_in_db:
            en = _escape(s.get("enrollment_no"))
            name = _escape(s.get("student_name"))
            cls = _escape(s.get("student_class"))
            rows.append(f"""
            <tr class="row-only-db">
                <td><span class="badge badge-only-db">ONLY IN DB</span></td>
                <td>{en}</td>
                <td>{name}</td>
                <td>{cls}</td>
                <td><span class="tag-null">NULL (Route B banayega)</span></td>
            </tr>""")
        return "\n".join(rows) if rows else '<tr><td colspan="5" class="empty-row">Koi aisa record nahi mila.</td></tr>'

    def make_only_tally_rows():
        rows = []
        for s in only_in_tally:
            en = _escape(s.get("enrollment_no"))
            name = _escape(s.get("student_name"))
            cls = _escape(s.get("student_class"))
            rows.append(f"""
            <tr class="row-only-tally">
                <td><span class="badge badge-only-tally">ONLY IN TALLY</span></td>
                <td>{en}</td>
                <td>{name}</td>
                <td>{cls}</td>
                <td><span class="tag-a">Route A lega Oracle mein</span></td>
            </tr>""")
        return "\n".join(rows) if rows else '<tr><td colspan="5" class="empty-row">Koi aisa record nahi mila.</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Synctal Bootstrap Reconciliation Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #070b13;
            --bg-card: rgba(13, 19, 33, 0.85);
            --border: rgba(255,255,255,0.07);
            --accent: #6366f1;
            --accent2: #a855f7;
            --text: #f1f3f7;
            --text2: #9ca3af;
            --green: #10b981;
            --orange: #f59e0b;
            --blue: #06b6d4;
            --red: #ef4444;
            --purple: #a855f7;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Outfit', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            background-image:
                radial-gradient(circle at 5% 10%, rgba(99,102,241,0.1) 0%, transparent 40%),
                radial-gradient(circle at 95% 90%, rgba(168,85,247,0.1) 0%, transparent 40%);
        }}
        header {{
            padding: 2rem 2.5rem 1rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
        }}
        .logo {{
            font-size: 1.6rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .meta {{ font-size: 0.85rem; color: var(--text2); }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 2rem 2.5rem; }}

        /* Summary Cards */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1.2rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.4rem 1.6rem;
            backdrop-filter: blur(20px);
            position: relative;
            overflow: hidden;
        }}
        .card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0;
            width: 4px; height: 100%;
        }}
        .card.matched::before {{ background: var(--green); }}
        .card.mismatch::before {{ background: var(--orange); }}
        .card.only-db::before {{ background: var(--blue); }}
        .card.only-tally::before {{ background: var(--purple); }}
        .card.total::before {{ background: linear-gradient(var(--accent), var(--accent2)); }}
        .card-label {{
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text2);
            margin-bottom: 0.4rem;
        }}
        .card-val {{
            font-size: 2.4rem;
            font-weight: 800;
        }}
        .card.matched .card-val {{ color: var(--green); }}
        .card.mismatch .card-val {{ color: var(--orange); }}
        .card.only-db .card-val {{ color: var(--blue); }}
        .card.only-tally .card-val {{ color: var(--purple); }}
        .card-sub {{ font-size: 0.78rem; color: var(--text2); margin-top: 0.2rem; }}

        /* Tabs */
        .tabs {{
            display: flex;
            gap: 0.4rem;
            margin-bottom: 1.2rem;
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            padding: 0.3rem;
            border-radius: 12px;
            width: fit-content;
        }}
        .tab {{
            padding: 0.5rem 1.2rem;
            border-radius: 8px;
            border: none;
            background: transparent;
            color: var(--text2);
            font-family: inherit;
            font-size: 0.88rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .tab:hover {{ color: var(--text); }}
        .tab.active {{
            background: rgba(255,255,255,0.09);
            color: var(--text);
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* Search */
        .search-bar {{
            margin-bottom: 1rem;
        }}
        .search-bar input {{
            background: rgba(255,255,255,0.04);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            color: var(--text);
            font-family: inherit;
            font-size: 0.88rem;
            width: 280px;
            outline: none;
            transition: border-color 0.2s;
        }}
        .search-bar input:focus {{ border-color: var(--accent); }}

        /* Table */
        .table-wrap {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            backdrop-filter: blur(20px);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }}
        thead tr {{
            background: rgba(255,255,255,0.04);
            border-bottom: 1px solid var(--border);
        }}
        th {{
            padding: 0.9rem 1.2rem;
            text-align: left;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
            color: var(--text2);
        }}
        td {{
            padding: 0.75rem 1.2rem;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }}
        tr:last-child td {{ border-bottom: none; }}
        .row-matched {{ background: rgba(16,185,129,0.03); }}
        .row-mismatch {{ background: rgba(245,158,11,0.04); cursor: pointer; transition: background 0.2s; }}
        .row-mismatch:hover {{ background: rgba(245,158,11,0.09); }}
        .row-only-db {{ background: rgba(6,182,212,0.03); }}
        .row-only-tally {{ background: rgba(168,85,247,0.04); }}
        .empty-row {{ color: var(--text2); text-align: center; padding: 2rem; }}

        /* Badges */
        .badge {{
            padding: 0.25rem 0.65rem;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}
        .badge-matched {{ background: rgba(16,185,129,0.12); color: var(--green); }}
        .badge-mismatch {{ background: rgba(245,158,11,0.12); color: var(--orange); }}
        .badge-only-db {{ background: rgba(6,182,212,0.12); color: var(--blue); }}
        .badge-only-tally {{ background: rgba(168,85,247,0.12); color: var(--purple); }}

        /* TALLY_SYNC tags */
        .tag-s {{ background: rgba(16,185,129,0.12); color: var(--green); padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }}
        .tag-u {{ background: rgba(245,158,11,0.12); color: var(--orange); padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }}
        .tag-null {{ background: rgba(6,182,212,0.12); color: var(--blue); padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }}
        .tag-a {{ background: rgba(168,85,247,0.12); color: var(--purple); padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }}

        /* Diff tags inline */
        .diff-tag {{
            display: inline-block;
            background: rgba(245,158,11,0.12);
            color: var(--orange);
            padding: 0.15rem 0.5rem;
            border-radius: 5px;
            font-size: 0.72rem;
            font-weight: 600;
            margin: 0.1rem 0.15rem;
        }}
        .null {{ color: rgba(255,255,255,0.2); font-style: italic; }}

        /* Detail row */
        .detail-row {{ display: none; }}
        .detail-row td {{ padding: 0; background: rgba(0,0,0,0.3); }}
        .detail-row.open {{ display: table-row; }}
        .diff-detail-table {{ width: 100%; border-collapse: collapse; font-size: 0.84rem; }}
        .diff-detail-table th {{
            background: rgba(255,255,255,0.05);
            padding: 0.6rem 1.5rem;
            text-align: left;
            font-size: 0.75rem;
            color: var(--text2);
        }}
        .diff-detail-table td {{ padding: 0.55rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.03); }}
        .diff-row td {{ background: rgba(245,158,11,0.06); }}
        .val-tally {{ color: var(--blue); }}
        .val-db {{ color: var(--orange); }}

        /* Info banner */
        .info-banner {{
            background: rgba(99,102,241,0.08);
            border: 1px solid rgba(99,102,241,0.2);
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.5rem;
            font-size: 0.88rem;
            color: var(--text2);
            line-height: 1.6;
        }}
        .info-banner strong {{ color: var(--text); }}
    </style>
</head>
<body>
<header>
    <div class="logo">⚡ Synctal Reconcile</div>
    <div class="meta">Report generated: {now} &nbsp;|&nbsp; Total records compared: <strong style="color:var(--text)">{total}</strong></div>
</header>

<div class="container">

    <!-- Summary -->
    <div class="summary-grid">
        <div class="card total">
            <div class="card-label">Total</div>
            <div class="card-val" style="background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent">{total}</div>
            <div class="card-sub">Records scanned</div>
        </div>
        <div class="card matched">
            <div class="card-label">Matched</div>
            <div class="card-val">{len(matched)}</div>
            <div class="card-sub">TALLY_SYNC → 'S'</div>
        </div>
        <div class="card mismatch">
            <div class="card-label">Mismatch</div>
            <div class="card-val">{len(mismatched)}</div>
            <div class="card-sub">TALLY_SYNC → 'U'</div>
        </div>
        <div class="card only-db">
            <div class="card-label">Only in Oracle</div>
            <div class="card-val">{len(only_in_db)}</div>
            <div class="card-sub">Route B banayega Tally mein</div>
        </div>
        <div class="card only-tally">
            <div class="card-label">Only in Tally</div>
            <div class="card-val">{len(only_in_tally)}</div>
            <div class="card-sub">Route A lega Oracle mein</div>
        </div>
    </div>

    <!-- Info -->
    <div class="info-banner">
        <strong>TALLY_SYNC Plan:</strong> &nbsp;
        <span class="tag-s">'S' = {len(matched)} matched</span> &nbsp;
        <span class="tag-u">'U' = {len(mismatched)} mismatched (sync agent fix karega)</span> &nbsp;
        <span class="tag-null">NULL = {len(only_in_db)} only in DB (Route B create karega Tally mein)</span> &nbsp;
        <span class="tag-a">{len(only_in_tally)} only in Tally (Route A Oracle mein lega)</span>
    </div>

    <!-- Tabs -->
    <div class="tabs">
        <button class="tab active" onclick="showTab('matched', this)">✅ Matched ({len(matched)})</button>
        <button class="tab" onclick="showTab('mismatch', this)">⚠️ Mismatch ({len(mismatched)})</button>
        <button class="tab" onclick="showTab('only-db', this)">🔵 Only in Oracle ({len(only_in_db)})</button>
        <button class="tab" onclick="showTab('only-tally', this)">🟣 Only in Tally ({len(only_in_tally)})</button>
    </div>

    <div class="search-bar">
        <input type="text" id="searchInput" placeholder="Search by Enrollment No or Name..." oninput="filterTable()">
    </div>

    <!-- Tab: Matched -->
    <div class="tab-content active" id="tab-matched">
        <div class="table-wrap">
            <table id="table-matched">
                <thead><tr>
                    <th>Status</th><th>Enrollment No</th><th>Student Name</th><th>Class</th><th>TALLY_SYNC</th>
                </tr></thead>
                <tbody>{make_matched_rows()}</tbody>
            </table>
        </div>
    </div>

    <!-- Tab: Mismatch -->
    <div class="tab-content" id="tab-mismatch">
        <div class="table-wrap">
            <table id="table-mismatch">
                <thead><tr>
                    <th>Status</th><th>Enrollment No</th><th>Student Name</th><th>Mismatched Fields (click to expand)</th><th>TALLY_SYNC</th>
                </tr></thead>
                <tbody>{make_mismatch_rows()}</tbody>
            </table>
        </div>
    </div>

    <!-- Tab: Only in DB -->
    <div class="tab-content" id="tab-only-db">
        <div class="table-wrap">
            <table id="table-only-db">
                <thead><tr>
                    <th>Status</th><th>Enrollment No</th><th>Student Name</th><th>Class</th><th>Action</th>
                </tr></thead>
                <tbody>{make_only_db_rows()}</tbody>
            </table>
        </div>
    </div>

    <!-- Tab: Only in Tally -->
    <div class="tab-content" id="tab-only-tally">
        <div class="table-wrap">
            <table id="table-only-tally">
                <thead><tr>
                    <th>Status</th><th>Enrollment No</th><th>Student Name</th><th>Class</th><th>Action</th>
                </tr></thead>
                <tbody>{make_only_tally_rows()}</tbody>
            </table>
        </div>
    </div>

</div>

<script>
    function showTab(name, btn) {{
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
        document.getElementById('tab-' + name).classList.add('active');
        btn.classList.add('active');
        document.getElementById('searchInput').value = '';
    }}

    function toggleDetail(id) {{
        const el = document.getElementById(id);
        el.classList.toggle('open');
    }}

    function filterTable() {{
        const q = document.getElementById('searchInput').value.toLowerCase();
        const activeTab = document.querySelector('.tab-content.active');
        if (!activeTab) return;
        const rows = activeTab.querySelectorAll('tbody tr:not(.detail-row)');
        rows.forEach(row => {{
            const text = row.innerText.toLowerCase();
            row.style.display = text.includes(q) ? '' : 'none';
        }});
    }}
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
