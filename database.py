"""
database.py — Koneksi dan operasi MongoDB Atlas
Business Analyst Agent (#2)

Database: BaAgent
Collections: projects, business_analysis, conversations
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# ── Koneksi MongoDB ──────────────────────────────────────────────────────────

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "BaAgent"

_client = None
_db = None


def get_database():
    """
    Mengembalikan koneksi ke database BaAgent.
    Menggunakan singleton pattern agar koneksi hanya dibuat sekali.
    """
    global _client, _db
    if _db is None:
        if not MONGODB_URI:
            raise ValueError("MONGODB_URI tidak ditemukan di file .env")
        _client = MongoClient(MONGODB_URI)
        _db = _client[DB_NAME]
        # Test koneksi
        _client.admin.command("ping")
        print("✅ Berhasil terhubung ke MongoDB Atlas!")
    return _db


# ── Operasi Collection: projects ─────────────────────────────────────────────

def save_project(project_data: dict) -> dict:
    """
    Menyimpan informasi proyek ke collection 'projects'.
    Jika project_id sudah ada, data akan di-update.

    Args:
        project_data: dict dengan field project_id, project_name, description, status

    Returns:
        dict: data proyek yang disimpan
    """
    db = get_database()
    collection = db["projects"]

    project_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    project_data.setdefault("status", "in_progress")

    collection.update_one(
        {"project_id": project_data["project_id"]},
        {"$set": project_data},
        upsert=True
    )
    print(f"📁 Project '{project_data.get('project_name', '')}' disimpan ke MongoDB.")
    return project_data


def get_project(project_id: str) -> dict | None:
    """
    Mengambil data proyek berdasarkan project_id.
    """
    db = get_database()
    return db["projects"].find_one({"project_id": project_id}, {"_id": 0})


# ── Operasi Collection: business_analysis ────────────────────────────────────

def save_business_analysis(analysis_data: dict) -> dict:
    """
    Menyimpan hasil analisis bisnis ke collection 'business_analysis'.
    Jika project_id sudah ada, data akan di-update.

    Args:
        analysis_data: dict dengan field project_id, user_stories,
                       functional_requirements, non_functional_requirements,
                       constraints, stakeholders

    Returns:
        dict: data analisis yang disimpan
    """
    db = get_database()
    collection = db["business_analysis"]

    analysis_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    analysis_data.setdefault("agent", "business_analyst_agent_v1")

    collection.update_one(
        {"project_id": analysis_data["project_id"]},
        {"$set": analysis_data},
        upsert=True
    )
    print(f"📊 Hasil analisis bisnis disimpan ke MongoDB (project: {analysis_data['project_id']}).")
    return analysis_data


def get_business_analysis(project_id: str) -> dict | None:
    """
    Mengambil hasil analisis bisnis berdasarkan project_id.
    """
    db = get_database()
    return db["business_analysis"].find_one({"project_id": project_id}, {"_id": 0})


# ── Operasi Collection: conversations ────────────────────────────────────────

def save_conversation(project_id: str, role: str, message: str) -> dict:
    """
    Menyimpan satu pesan percakapan ke collection 'conversations'.

    Args:
        project_id: ID proyek terkait
        role: "user" atau "agent"
        message: isi pesan

    Returns:
        dict: data percakapan yang disimpan
    """
    db = get_database()
    collection = db["conversations"]

    conversation = {
        "project_id": project_id,
        "role": role,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    collection.insert_one(conversation)
    return conversation


def get_conversations(project_id: str) -> list:
    """
    Mengambil seluruh histori percakapan berdasarkan project_id,
    diurutkan berdasarkan timestamp.
    """
    db = get_database()
    conversations = db["conversations"].find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("timestamp", 1)
    return list(conversations)


def list_projects() -> list:
    """
    Mengambil daftar semua proyek yang ada di database,
    diurutkan berdasarkan created_at (terbaru duluan).
    """
    db = get_database()
    projects = db["projects"].find(
        {},
        {"_id": 0, "project_id": 1, "project_name": 1, "status": 1, "created_at": 1}
    ).sort("created_at", -1)
    return list(projects)


def delete_project(project_id: str) -> dict:
    """
    Menghapus proyek beserta semua data terkait dari MongoDB.
    Menghapus dari: projects, business_analysis, conversations.

    Args:
        project_id: ID proyek yang akan dihapus

    Returns:
        dict: jumlah dokumen yang dihapus per collection
    """
    db = get_database()

    result = {
        "projects": db["projects"].delete_many({"project_id": project_id}).deleted_count,
        "business_analysis": db["business_analysis"].delete_many({"project_id": project_id}).deleted_count,
        "conversations": db["conversations"].delete_many({"project_id": project_id}).deleted_count,
    }

    total = sum(result.values())
    print(f"🗑️  Proyek {project_id} dihapus dari MongoDB ({total} dokumen).")
    return result
