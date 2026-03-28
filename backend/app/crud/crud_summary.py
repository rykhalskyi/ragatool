from sqlite3 import Connection
from typing import List, Optional
from uuid import uuid4
from app.schemas.summary import Summary, SummaryType

def get_summaries(db: Connection, collection_id: str) -> List[Summary]:
    cursor = db.cursor()
    cursor.execute("SELECT id, collection_id, type, summary, metadata FROM summary WHERE collection_id = ?", (collection_id,))
    summaries = cursor.fetchall()
    return [Summary(**dict(summary)) for summary in summaries]

def get_summary_by_type(db: Connection, collection_id: str, summary_type: SummaryType) -> List[Summary]:
    cursor = db.cursor()
    cursor.execute("SELECT id, collection_id, type, summary, metadata FROM summary WHERE collection_id = ? AND type = ?", (collection_id, summary_type.value))
    summaries = cursor.fetchall()
    return [Summary(**dict(summary)) for summary in summaries]

def create_summary(db: Connection, summary: Summary):
    cursor = db.cursor()
    summary_id = str(uuid4())
    cursor.execute(
        "INSERT INTO summary (id, collection_id, type, summary, metadata) VALUES (?, ?, ?, ?, ?)",
        (summary_id, summary.collection_id, summary.type.value, summary.summary, summary.metadata)
    )
    db.commit()
    return summary_id

def edit_summary(db: Connection, summary_id: str, summary: Summary):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE summary SET type = ?, summary = ?, metadata = ? WHERE id = ?",
        (summary.type.value, summary.summary, summary.metadata, summary_id)
    )
    db.commit()

def delete_summary_by_id(db: Connection, summary_id: str):
    cursor = db.cursor()
    cursor.execute("DELETE FROM summary WHERE id = ?", (summary_id,))
    db.commit()

def delete_all_summaries_for_collection(db: Connection, collection_id: str):
    cursor = db.cursor()
    cursor.execute("DELETE FROM summary WHERE collection_id = ?", (collection_id,))
    db.commit()