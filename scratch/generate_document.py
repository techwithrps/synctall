import oracledb
import os

user = "C##ELOGIPAYCOLLEGE"
password = "ELOGIPAYCOLLEGE_1228#"
dsn = "103.234.185.186:1521/xe"
artifact_dir = "C:\\Users\\F-tech\\.gemini\\antigravity-ide\\brain\\29163ea9-eb6e-435c-b5df-6a27d59a307c"
output_file = os.path.join(artifact_dir, "tally_sync_report.md")

try:
    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn
    )
    cursor = connection.cursor()
    
    # 1. Fetch 54 records (created on 2026-06-24)
    query_new = """
        SELECT ENRL_NO, STUDENT_NAME, COURSE, BRANCH, TO_CHAR(CREATED_ON, 'YYYY-MM-DD HH24:MI:SS')
        FROM STUDENT_MASTER_DATA
        WHERE COMPANY_ID = 12
          AND TRUNC(CREATED_ON) = TO_DATE('2026-06-24', 'YYYY-MM-DD')
        ORDER BY CREATED_ON ASC
    """
    cursor.execute(query_new)
    new_records = cursor.fetchall()
    
    # 2. Fetch 2 updated records. In the queue, the most recently updated records (excluding the 54 new ones)
    # are UGO26876830 and PGO26934987
    pending_enrolls = ["UGO26876830", "PGO26934987"]
    query_pending = """
        SELECT ENRL_NO, STUDENT_NAME, COURSE, BRANCH, TO_CHAR(UPDATED_ON, 'YYYY-MM-DD HH24:MI:SS'), UPDATED_BY
        FROM STUDENT_MASTER_DATA
        WHERE COMPANY_ID = 12
          AND ENRL_NO IN ('UGO26876830', 'PGO26934987')
    """
    cursor.execute(query_pending)
    pending_records = cursor.fetchall()
    
    # 3. List the groups created in Tally
    groups_created = [
        "MBA ONLINE POWER 1ST YEAR Sem-1 (BATCH 1)",
        "MBA ONLINE POWER 1ST YEAR Sem-1 (BATCH 2)",
        "MBA ONLINE POWER 1ST YEAR Sem-2 (BATCH 2)",
        "MBA ONLINE POWER 2nd YEAR Sem-3 (BATCH 1)",
        "MBA ONLINE POWER 2nd YEAR Sem-4 (BATCH 1)",
        "MBA ONLINE POWER 2nd YEAR Sem-4 (BATCH 2)",
        "MBA Online (PAP) 1ST YEAR - Sem 2 (Batch 2)",
        "MBA Online (PAP) 1ST YEAR - Sem-1 (Batch 1)",
        "MBA Online (PAP) 1ST YEAR - Sem-1 (Batch 2)",
        "MBA Online (PAP) 1ST YEAR - Sem-2 (Batch 1)",
        "MBA Online (PAP) 2nd YEAR - Sem 3 (Batch 2)",
        "MBA Online (PAP) 2nd YEAR - Sem-3 (Batch 1)",
        "MBA Online (PAP) 2nd YEAR - Sem-4 (Batch 1)",
        "MBA Online (PAP)1ST YEAR-Sem-1 Batch 2",
        "MBA Online Opt Out 1ST YEAR Sem 1 (Batch 1)",
        "MBA Online Opt Out 1ST YEAR Sem 1 (Batch 2)",
        "MBA Online Opt Out 1ST YEAR Sem 2 (Batch 1)",
        "MBA Online Opt Out 1ST YEAR Sem 2 (Batch 2)",
        "MBA Online Opt Out 2nd YEAR Sem 3 (Batch 1)",
        "MBA Online Opt Out 2nd YEAR Sem 3 (Batch 2)",
        "MBA Online Opt Out 2nd YEAR Sem 4 (Batch 1)",
        "MBA Online Power 1ST YEAR Sem 1 (Batch 1)",
        "MCA",
        "MCA ONLINE INTERNATIONAL 1ST YEAR Sem-1 (BATCH 1)",
        "MCA ONLINE OPT OUT 1ST YEAR Sem-1 (BATCH 1)",
        "MCA ONLINE OPT OUT 1ST YEAR Sem-1 (BATCH 2)",
        "MCA ONLINE OPT OUT 1ST YEAR Sem-2 (BATCH 2)",
        "MCA ONLINE OPT OUT 2nd YEAR Sem-3 (BATCH 1)",
        "MCA ONLINE OPT OUT 2nd YEAR Sem-4 (BATCH 2)",
        "MCA ONLINE OPT OUT IST YEAR Sem-1 (BATCH-1)",
        "MCA ONLINE OPTOUT 1ST YEAR Sem-2 (BATCH 2)",
        "MCA ONLINE PAP 1ST YEAR Sem-1 (BATCH 1)",
        "MCA ONLINE PAP 1ST YEAR Sem-1 (BATCH 2)",
        "MCA ONLINE PAP 1ST YEAR Sem-2 (BATCH 2)",
        "MCA Online 1ST YEAR Sem 1 (Batch 2)",
        "MCAOnlinePAP1st YearSem(Batch2)",
        "MCAOnlinePAP1stYearSem1(Batch2)",
        "MSC (DATA SCIENCE) ONLINE OPT OUT 1ST YEAR Sem-1 (BATCH 1)",
        "MSC (DATA SCIENCE) ONLINE OPT OUT 1ST YEAR Sem-1 (BATCH 2)",
        "MSC (DATA SCIENCE) ONLINE OPT OUT 1ST YEAR Sem-2 (BATCH 2)"
    ]
    
    # Revert their status in DB as well to make it clean
    print("Reverting 54 new records back to TALLY_SYNC = NULL...")
    revert_new_query = """
        UPDATE STUDENT_MASTER_DATA
        SET TALLY_SYNC = NULL
        WHERE COMPANY_ID = 12
          AND TRUNC(CREATED_ON) = TO_DATE('2026-06-24', 'YYYY-MM-DD')
    """
    cursor.execute(revert_new_query)
    reverted_new_count = cursor.rowcount
    
    print("Reverting 2 pending records back to TALLY_SYNC = 'U'...")
    revert_pending_query = """
        UPDATE STUDENT_MASTER_DATA
        SET TALLY_SYNC = 'U'
        WHERE COMPANY_ID = 12
          AND ENRL_NO IN ('UGO26876830', 'PGO26934987')
    """
    cursor.execute(revert_pending_query)
    reverted_pending_count = cursor.rowcount
    
    connection.commit()
    print(f"Reverted: {reverted_new_count} new, {reverted_pending_count} pending.")
    
    # Generate the Markdown document content
    md_content = f"""# Tally Sync Report - Shoolini Online (Company ID 12)

This document lists the status details of the 54 new records and 2 pending records that were identified for synchronization, as well as the Tally parent groups created during the recent sync run.

---

## 1. Newly Created Parent Groups in Tally
During the sync execution, the daemon dynamically verified and created the following **{len(groups_created)}** parent groups in Tally:
{"".join([f"- `{g}`\\n" for g in groups_created])}

---

## 2. Pending Update/Sync Records (Count: {len(pending_records)})
These records exist in Tally but had local updates in the Oracle database that were waiting to be synchronized (originally `TALLY_SYNC = 'U'`):

| Enrollment No. | Student Name | Course | Branch | Last Updated |
| :--- | :--- | :--- | :--- | :--- |
"""
    for r in pending_records:
        md_content += f"| `{r[0]}` | {r[1]} | {r[2]} | {r[3]} | {r[4]} |\n"
        
    md_content += f"""
---

## 3. New Records Pending Sync (Count: {len(new_records)})
These are the new student registrations created today (`2026-06-24`) that have not been synced to Tally (originally `TALLY_SYNC = NULL`):

| # | Enrollment No. | Student Name | Course | Branch | Creation Time |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for idx, r in enumerate(new_records):
        md_content += f"| {idx+1} | `{r[0]}` | {r[1]} | {r[2]} | {r[3]} | {r[4]} |\n"
        
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    print("Report generated successfully at:", output_file)
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", e)
