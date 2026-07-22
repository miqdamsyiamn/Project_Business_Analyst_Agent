"""
main.py — File utama Business Analyst Agent (#2)
AI Software Development Team

Menjalankan agent interaktif yang berdialog dengan user untuk menganalisis
kebutuhan bisnis menggunakan LLM API (multi-provider).

Provider yang didukung:
  - Groq (llama-3.3-70b-versatile)
  - OpenRouter (berbagai model gratis)
  - Gemini (via OpenAI-compatible endpoint)
  - Qwen (via DashScope)
  - Custom (LLM apapun yang OpenAI-compatible)

Fitur:
  - Percakapan interaktif (agent bertanya balik ke user)
  - Memory: mengingat percakapan sebelumnya dari MongoDB
  - Token limit: max_tokens & temperature terkontrol
  - Retry otomatis saat rate limit

Mode:
  - CLI:    python main.py
  - Gradio: python main.py --serve  (untuk deploy ke Hugging Face Spaces)
"""

import os
import sys
import json
import time
import re
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI

from prompt import CONVERSATION_PROMPT, ANALYSIS_PROMPT, get_analysis_prompt
from database import (
    save_project,
    save_business_analysis,
    save_conversation,
    get_project,
    get_conversations,
    list_projects,
    delete_project,
)

load_dotenv()

# ── Konfigurasi LLM (Multi-Provider) ────────────────────────────────────────

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

if not LLM_API_KEY:
    print("❌ Error: LLM_API_KEY tidak ditemukan di file .env")
    print("   Silakan isi LLM_API_KEY di file .env (lihat .env.example)")
    sys.exit(1)

# Inisialisasi OpenAI client (kompatibel dengan semua provider)
client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)

print(f"🔌 LLM Provider: {LLM_PROVIDER}")
print(f"🤖 Model: {LLM_MODEL}")
print(f"🌐 Base URL: {LLM_BASE_URL}")


# ── Konfigurasi Token Limit ─────────────────────────────────────────────────

CONVERSATION_MAX_TOKENS = 1024    # Batasi output percakapan
CONVERSATION_TEMPERATURE = 0.7   # Cukup kreatif tapi tetap fokus
ANALYSIS_MAX_TOKENS = 4096       # Analisis butuh output lebih panjang
ANALYSIS_TEMPERATURE = 0.3       # Lebih presisi untuk generate JSON


# ── LLM Chat Helper ─────────────────────────────────────────────────────────

def chat_with_llm(messages: list, max_tokens: int = 1024, temperature: float = 0.7) -> str:
    """
    Kirim pesan ke LLM dan dapatkan response.

    Args:
        messages: list of {"role": "system"/"user"/"assistant", "content": "..."}
        max_tokens: batas output token
        temperature: kreativitas (0.0 - 1.0)

    Returns:
        str: response dari LLM
    """
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


# ── Retry Logic untuk Rate Limit ─────────────────────────────────────────────

def retry_llm_call(func, max_retries=3, base_delay=10):
    """
    Wrapper untuk retry otomatis saat kena rate limit (429).

    Args:
        func: callable yang memanggil LLM API
        max_retries: jumlah percobaan ulang (default: 3)
        base_delay: delay awal dalam detik (default: 10s)

    Returns:
        response dari LLM

    Raises:
        Exception: jika tetap gagal setelah semua retry
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower() or "quota" in error_str.lower():
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)  # 10s, 20s, 40s
                    print(f"⏳ Rate limit tercapai. Menunggu {delay} detik... (percobaan {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    print(f"❌ Rate limit masih tercapai setelah {max_retries} percobaan.")
                    raise
            else:
                raise


# ── Helper Functions ─────────────────────────────────────────────────────────

def clean_for_terminal(text: str) -> str:
    """
    Bersihkan output LLM dari format markdown agar rapi di terminal.
    Menghapus: **bold**, *italic*, ### heading, ```code block```, dll.
    """
    # Hapus code block ```...```
    text = re.sub(r'```[\s\S]*?```', '', text)

    # Hapus heading (### heading -> heading)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    # Hapus bold **text** -> text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)

    # Hapus italic *text* -> text (tapi jangan hapus * di awal baris untuk bullet)
    text = re.sub(r'(?<!\n)\*(.+?)\*', r'\1', text)

    # Ganti * bullet di awal baris dengan -
    text = re.sub(r'^\s*\*\s+', '  - ', text, flags=re.MULTILINE)

    # Hapus backtick inline `code` -> code
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Bersihkan multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def generate_project_id() -> str:
    """Generate project_id unik berdasarkan timestamp."""
    now = datetime.now(timezone.utc)
    return f"proj_{now.strftime('%Y%m%d%H%M%S')}"


def parse_json_response(response_text: str) -> dict:
    """
    Parse response dari LLM menjadi dictionary.
    Menangani kemungkinan response yang dibungkus markdown code block.
    """
    text = response_text.strip()

    # Hapus markdown code block jika ada
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"⚠️ Gagal parse JSON: {e}")
        print(f"Response mentah:\n{response_text}")
        return None


def save_local_backup(analysis_data: dict) -> str:
    """
    Simpan hasil analisis ke file lokal:
    1. output/business_analysis_{project_id}.json  — file per proyek
    2. output/business_analysis.json               — kumpulan SEMUA proyek
    """
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    clean_data = {k: v for k, v in analysis_data.items() if k != "_id"}
    project_id = clean_data.get("project_id", "unknown")

    # 1. Simpan file per proyek (tidak akan tertimpa proyek lain)
    per_project_path = os.path.join(output_dir, f"business_analysis_{project_id}.json")
    with open(per_project_path, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)

    # 2. Simpan/update ke file master (kumpulan semua proyek)
    master_path = os.path.join(output_dir, "business_analysis.json")

    # Load data master yang sudah ada
    all_analyses = {}
    if os.path.exists(master_path):
        try:
            with open(master_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
                # Jika format lama (bukan dict of projects), konversi
                if isinstance(existing, dict) and "projects" in existing:
                    for proj in existing["projects"]:
                        all_analyses[proj.get("project_id", "")] = proj
                elif isinstance(existing, dict) and "project_id" in existing:
                    # Format lama: single project
                    all_analyses[existing["project_id"]] = existing
                elif isinstance(existing, list):
                    for proj in existing:
                        all_analyses[proj.get("project_id", "")] = proj
        except (json.JSONDecodeError, KeyError):
            pass

    # Update/tambah proyek ke master
    all_analyses[project_id] = clean_data

    # Tulis master file
    master_data = {
        "total_projects": len(all_analyses),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "projects": list(all_analyses.values())
    }

    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(master_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Backup lokal disimpan ke:")
    print(f"   - {per_project_path}")
    print(f"   - {master_path} ({len(all_analyses)} proyek)")
    return per_project_path


def load_chat_history_from_db(project_id: str) -> list:
    """
    Load histori percakapan sebelumnya dari MongoDB.
    Mengembalikan list of (role, message) tuples.
    """
    conversations = get_conversations(project_id)
    return [(conv["role"], conv["message"]) for conv in conversations]


def build_openai_messages(system_prompt: str, chat_history: list) -> list:
    """
    Konversi chat_history [(role, message), ...] menjadi format
    OpenAI messages agar LLM mengingat seluruh konteks percakapan.

    Format output:
    [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "pesan user"},
        {"role": "assistant", "content": "pesan agent"},
        ...
    ]
    """
    messages = [{"role": "system", "content": system_prompt}]

    for role, message in chat_history:
        if role == "user":
            messages.append({"role": "user", "content": message})
        else:
            messages.append({"role": "assistant", "content": message})

    return messages


# ── Analisis Final ───────────────────────────────────────────────────────────

def generate_final_analysis(project_id: str, project_name: str, description: str, chat_history: list) -> dict:
    """
    Generate analisis final berdasarkan seluruh histori percakapan.
    """
    # Susun histori percakapan menjadi teks untuk prompt analisis
    history_text = f"Nama Proyek: {project_name}\nDeskripsi Awal: {description}\n\n"
    history_text += "=== Histori Percakapan ===\n"
    for role, message in chat_history:
        label = "User" if role == "user" else "Business Analyst"
        history_text += f"\n{label}: {message}\n"

    # Buat messages untuk analisis
    analysis_prompt = get_analysis_prompt(history_text)
    messages = [
        {"role": "system", "content": ANALYSIS_PROMPT},
        {"role": "user", "content": analysis_prompt},
    ]

    print("\n🤖 Menghasilkan dokumen analisis bisnis final...")

    try:
        response_text = retry_llm_call(
            lambda: chat_with_llm(messages, max_tokens=ANALYSIS_MAX_TOKENS, temperature=ANALYSIS_TEMPERATURE)
        )
    except Exception as e:
        print(f"❌ Error saat memanggil LLM: {e}")
        return None

    # Parse response JSON
    analysis = parse_json_response(response_text)
    if analysis is None:
        return None

    # Tambahkan metadata
    analysis["project_id"] = project_id
    analysis["created_at"] = datetime.now(timezone.utc).isoformat()
    analysis["agent"] = "business_analyst_agent_v1"

    # Simpan ke MongoDB
    save_business_analysis(analysis)

    # Simpan response agent ke conversations
    save_conversation(project_id, "agent", json.dumps(analysis, ensure_ascii=False))

    # Simpan backup lokal
    save_local_backup(analysis)

    # Update status project (analyzed, bukan completed — masih bisa dilanjutkan)
    save_project({
        "project_id": project_id,
        "project_name": project_name,
        "description": description,
        "status": "analyzed"
    })

    return analysis


def display_analysis(result: dict, project_name: str, project_id: str):
    """Tampilkan hasil analisis ke terminal."""
    print("\n" + "=" * 60)
    print("✅ ANALISIS SELESAI!")
    print("=" * 60)

    print(f"\n📌 Project: {project_name} ({project_id})")

    print(f"\n👥 Stakeholders ({len(result.get('stakeholders', []))}):")
    for s in result.get("stakeholders", []):
        print(f"   • {s}")

    print(f"\n📖 User Stories ({len(result.get('user_stories', []))}):")
    for us in result.get("user_stories", []):
        print(f"   [{us['id']}] As a {us['as_a']}, I want {us['i_want']}, so that {us['so_that']}")

    print(f"\n✅ Functional Requirements ({len(result.get('functional_requirements', []))}):")
    for fr in result.get("functional_requirements", []):
        print(f"   • {fr}")

    print(f"\n⚡ Non-Functional Requirements ({len(result.get('non_functional_requirements', []))}):")
    for nfr in result.get("non_functional_requirements", []):
        print(f"   • {nfr}")

    print(f"\n🚧 Constraints ({len(result.get('constraints', []))}):")
    for c in result.get("constraints", []):
        print(f"   • {c}")

    print(f"\n💾 Data disimpan ke:")
    print(f"   • MongoDB Atlas → DB: BaAgent")
    print(f"   • Lokal → output/business_analysis.json")


# ── Mode CLI (Interaktif dengan Memory) ──────────────────────────────────────

def show_banner():
    """Tampilkan banner utama agent."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + "  🤖 Business Analyst Agent (#2)".center(58) + "║")
    print("║" + "     AI Software Development Team".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()


def show_main_menu():
    """Tampilkan menu utama dan return pilihan proyek."""
    print("─" * 60)
    print("  📋 MENU UTAMA")
    print("─" * 60)
    print()

    project_id = None
    project_name = None
    description = None
    chat_history = []

    try:
        existing_projects = list_projects()
        resumable = [p for p in existing_projects if p.get("status") in ("in_progress", "analyzed")]

        if resumable:
            print("  📂 Proyek yang tersedia:")
            print()
            for i, proj in enumerate(resumable, 1):
                if proj.get("status") == "in_progress":
                    status_icon = "🔄"
                    status_text = "sedang berjalan"
                else:
                    status_icon = "✅"
                    status_text = "sudah dianalisis"
                print(f"    {i}. {status_icon} {proj['project_name']}")
                print(f"       ID: {proj['project_id']}  |  Status: {status_text}")
            print()
            print(f"    {len(resumable) + 1}. ➕ Buat proyek baru")
            print(f"    d. 🗑️  Hapus proyek")
            print(f"    0. 🚪 Keluar")
            print()
            print("─" * 60)

            choice = input("  Pilih nomor (Enter = buat baru): ").strip()

            # Handle /keluar atau 0
            if choice.lower() in ("/keluar", "0"):
                print("\n  👋 Sampai jumpa!")
                return "keluar"

            # Handle hapus proyek
            if choice.lower() in ("d", "/hapus"):
                print()
                print("  🗑️  HAPUS PROYEK")
                print("  " + "─" * 40)
                for i, proj in enumerate(resumable, 1):
                    print(f"    {i}. {proj['project_name']} ({proj['project_id']})")
                print(f"    0. Batal")
                print()

                del_choice = input("  Pilih nomor proyek yang ingin dihapus: ").strip()

                if del_choice.isdigit() and 1 <= int(del_choice) <= len(resumable):
                    target = resumable[int(del_choice) - 1]
                    target_name = target["project_name"]
                    target_id = target["project_id"]

                    confirm = input(f"\n  ⚠️  Yakin hapus '{target_name}'? (y/n): ").strip().lower()
                    if confirm == "y":
                        # Hapus dari MongoDB
                        delete_project(target_id)

                        # Hapus file lokal jika ada
                        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
                        local_file = os.path.join(output_dir, f"business_analysis_{target_id}.json")
                        if os.path.exists(local_file):
                            os.remove(local_file)
                            print(f"  🗑️  File lokal dihapus: {local_file}")

                        # Update master file
                        master_path = os.path.join(output_dir, "business_analysis.json")
                        if os.path.exists(master_path):
                            try:
                                with open(master_path, "r", encoding="utf-8") as f:
                                    master = json.load(f)
                                if "projects" in master:
                                    master["projects"] = [p for p in master["projects"] if p.get("project_id") != target_id]
                                    master["total_projects"] = len(master["projects"])
                                    with open(master_path, "w", encoding="utf-8") as f:
                                        json.dump(master, f, indent=2, ensure_ascii=False)
                            except (json.JSONDecodeError, KeyError):
                                pass

                        print(f"\n  ✅ Proyek '{target_name}' berhasil dihapus!")
                    else:
                        print("\n  ↩️  Batal hapus.")
                else:
                    print("\n  ↩️  Batal hapus.")

                print()
                return "menu"  # Kembali ke menu utama

            if choice.isdigit() and 1 <= int(choice) <= len(resumable):
                selected = resumable[int(choice) - 1]
                project_id = selected["project_id"]
                project_name = selected["project_name"]

                proj_data = get_project(project_id)
                description = proj_data.get("description", "") if proj_data else ""
                chat_history = load_chat_history_from_db(project_id)

                status_label = "sudah dianalisis" if selected.get("status") == "analyzed" else "sedang berjalan"
                print()
                print(f"  🔄 Melanjutkan proyek ({status_label}):")
                print(f"     Nama      : {project_name}")
                print(f"     ID        : {project_id}")
                print(f"     Deskripsi : {description}")
                print(f"     Memori    : {len(chat_history)} pesan dimuat")
                print()
        else:
            print("  Belum ada proyek. Mari buat yang baru!")
            print()
    except Exception as e:
        print(f"  ⚠️ Tidak bisa memuat proyek lama: {e}")
        print()

    # Buat proyek baru jika belum dipilih
    if project_id is None:
        print("─" * 60)
        print("  📝 BUAT PROYEK BARU")
        print("─" * 60)
        print()
        project_name = input("  Nama proyek: ").strip()
        if not project_name:
            print("  ❌ Nama proyek tidak boleh kosong.")
            return None

        print()
        description = input("  Deskripsi proyek:\n  > ").strip()
        if not description:
            print("  ❌ Deskripsi proyek tidak boleh kosong.")
            return None

        project_id = generate_project_id()
        print(f"\n  🆔 Project ID: {project_id}")

        save_project({
            "project_id": project_id,
            "project_name": project_name,
            "description": description,
            "status": "in_progress"
        })

        save_conversation(project_id, "user", description)
        chat_history = [("user", description)]

    return {
        "project_id": project_id,
        "project_name": project_name,
        "description": description,
        "chat_history": chat_history
    }


def run_project_chat(project_id, project_name, description, chat_history):
    """
    Menjalankan sesi percakapan untuk satu proyek.
    Returns: 'beranda' untuk kembali ke menu, 'keluar' untuk exit.
    """
    print()
    print("╔" + "═" * 58 + "╗")
    print(f"║  Proyek: {project_name[:46]}".ljust(59) + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("  Perintah:")
    print("    /selesai  - Generate/update analisis")
    print("    /beranda  - Kembali ke menu utama")
    print("    /keluar   - Keluar dari program")
    print()

    # Jika ada histori, langsung siap chat
    if len(chat_history) > 1:
        print("  🤖 Agent sudah mengingat percakapan sebelumnya.")
        print("     Silakan lanjutkan diskusi!\n")
    else:
        # Proyek baru — kirim deskripsi awal ke LLM
        print("  🤖 Agent sedang memproses...\n")
        try:
            initial_user_msg = (
                f"User ingin membuat proyek bernama '{project_name}'. "
                f"Berikut deskripsi awalnya:\n\n{description}\n\n"
                f"Ajukan pertanyaan untuk menggali kebutuhan lebih detail."
            )
            messages = build_openai_messages(CONVERSATION_PROMPT, [("user", initial_user_msg)])

            agent_reply = retry_llm_call(
                lambda: chat_with_llm(messages, max_tokens=CONVERSATION_MAX_TOKENS, temperature=CONVERSATION_TEMPERATURE)
            )
            # Bersihkan output dari markdown
            clean_reply = clean_for_terminal(agent_reply)
            print(f"  🤖 BA Agent:\n  {clean_reply.replace(chr(10), chr(10) + '  ')}\n")

            save_conversation(project_id, "agent", agent_reply)
            chat_history.append(("agent", agent_reply))
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return "beranda"

    # ── Loop percakapan interaktif ──
    while True:
        print("  " + "─" * 40)
        user_input = input("  👤 Anda:\n  > ").strip()

        if not user_input:
            continue

        # Perintah /keluar
        if user_input.lower() == "/keluar":
            print("\n  👋 Percakapan tersimpan. Sampai jumpa!")
            return "keluar"

        # Perintah /beranda
        if user_input.lower() == "/beranda":
            print("\n  🏠 Kembali ke menu utama...")
            return "beranda"

        # Perintah /selesai — generate/update analisis
        if user_input.lower() == "/selesai":
            result = generate_final_analysis(project_id, project_name, description, chat_history)

            if result:
                display_analysis(result, project_name, project_id)

                print()
                print("  ╔" + "═" * 54 + "╗")
                print("  ║  Apa yang ingin Anda lakukan selanjutnya?".ljust(55) + " ║")
                print("  ╠" + "═" * 54 + "╣")
                print("  ║  1. Lanjutkan diskusi proyek ini".ljust(55) + " ║")
                print("  ║  2. Kembali ke menu utama (pilih proyek lain)".ljust(55) + " ║")
                print("  ║  3. Keluar dari program".ljust(55) + " ║")
                print("  ╚" + "═" * 54 + "╝")
                print()

                post_choice = input("  Pilih (1/2/3): ").strip()

                if post_choice == "2":
                    print("\n  🏠 Kembali ke menu utama...")
                    return "beranda"
                elif post_choice == "3":
                    print("\n  👋 Percakapan tersimpan. Sampai jumpa!")
                    return "keluar"
                else:
                    print("\n  💬 Melanjutkan diskusi proyek ini...\n")
                    continue
            else:
                print("\n  ❌ Analisis gagal. Silakan coba lagi.")
            continue

        # Simpan pesan user ke MongoDB
        save_conversation(project_id, "user", user_input)
        chat_history.append(("user", user_input))

        # Bangun SELURUH histori percakapan sebagai context
        messages = build_openai_messages(CONVERSATION_PROMPT, chat_history)

        print("\n  🤖 Agent sedang memproses...\n")
        try:
            agent_reply = retry_llm_call(
                lambda: chat_with_llm(messages, max_tokens=CONVERSATION_MAX_TOKENS, temperature=CONVERSATION_TEMPERATURE)
            )
            # Bersihkan output dari markdown
            clean_reply = clean_for_terminal(agent_reply)
            print(f"  🤖 BA Agent:\n  {clean_reply.replace(chr(10), chr(10) + '  ')}\n")

            save_conversation(project_id, "agent", agent_reply)
            chat_history.append(("agent", agent_reply))
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue


def run_cli():
    """Menjalankan agent dalam mode CLI interaktif dengan menu beranda."""
    show_banner()
    print("  Saya akan membantu menganalisis kebutuhan bisnis proyek Anda.")
    print("  Mari berdiskusi terlebih dahulu sebelum saya buat analisisnya.")
    print()

    # ── Main Menu Loop ──
    while True:
        project_data = show_main_menu()

        # User minta keluar dari menu utama
        if project_data == "keluar":
            return

        # Kembali ke menu (setelah hapus proyek)
        if project_data == "menu":
            continue

        if project_data is None:
            # User tidak isi nama/deskripsi, tanya mau coba lagi?
            retry = input("\n  Coba lagi? (y/n): ").strip().lower()
            if retry != "y":
                print("\n  👋 Sampai jumpa!")
                return
            continue

        # Jalankan sesi chat untuk proyek terpilih
        action = run_project_chat(
            project_data["project_id"],
            project_data["project_name"],
            project_data["description"],
            project_data["chat_history"]
        )

        if action == "keluar":
            return
        # action == "beranda" → loop kembali ke menu utama


# ── Mode Gradio (Chat Interface untuk Hugging Face Spaces) ───────────────────

def run_gradio():
    """Menjalankan agent dengan Gradio ChatInterface + API endpoint."""
    import gradio as gr

    # State per session
    session_data = {}

    def chat_respond(message: str, history: list, project_name: str, project_id_input: str):
        """Handler untuk Gradio chat interface dengan memory."""
        # Inisialisasi session jika baru
        if "project_id" not in session_data or not history:
            # Cek apakah user ingin melanjutkan proyek lama
            if project_id_input and project_id_input.strip():
                project_id = project_id_input.strip()
                proj_data = get_project(project_id)

                if proj_data:
                    p_name = proj_data.get("project_name", project_name or f"Project {project_id}")
                    desc = proj_data.get("description", message)
                    prev_history = load_chat_history_from_db(project_id)

                    session_data["project_id"] = project_id
                    session_data["project_name"] = p_name
                    session_data["description"] = desc
                    session_data["chat_history"] = prev_history.copy()

                    # Tambahkan pesan baru
                    save_conversation(project_id, "user", message)
                    session_data["chat_history"].append(("user", message))

                    try:
                        messages = build_openai_messages(CONVERSATION_PROMPT, session_data["chat_history"])
                        agent_reply = retry_llm_call(
                            lambda: chat_with_llm(messages, max_tokens=CONVERSATION_MAX_TOKENS, temperature=CONVERSATION_TEMPERATURE)
                        )
                        save_conversation(project_id, "agent", agent_reply)
                        session_data["chat_history"].append(("agent", agent_reply))
                        return f"🔄 *Melanjutkan proyek: {p_name}* ({len(prev_history)} pesan sebelumnya dimuat)\n\n{agent_reply}"
                    except Exception as e:
                        return f"❌ Error: {e}"

            # Proyek baru
            project_id = generate_project_id()
            p_name = project_name if project_name else f"Project {project_id}"

            session_data["project_id"] = project_id
            session_data["project_name"] = p_name
            session_data["description"] = message
            session_data["chat_history"] = []

            save_project({
                "project_id": project_id,
                "project_name": p_name,
                "description": message,
                "status": "in_progress"
            })

            save_conversation(project_id, "user", message)
            session_data["chat_history"].append(("user", message))

            try:
                initial_user_msg = (
                    f"User ingin membuat proyek bernama '{p_name}'. "
                    f"Berikut deskripsi awalnya:\n\n{message}\n\n"
                    f"Ajukan pertanyaan untuk menggali kebutuhan lebih detail."
                )
                messages = build_openai_messages(CONVERSATION_PROMPT, [("user", initial_user_msg)])
                agent_reply = retry_llm_call(
                    lambda: chat_with_llm(messages, max_tokens=CONVERSATION_MAX_TOKENS, temperature=CONVERSATION_TEMPERATURE)
                )
                save_conversation(project_id, "agent", agent_reply)
                session_data["chat_history"].append(("agent", agent_reply))
                return f"🆔 Project ID: **{project_id}**\n\n{agent_reply}"
            except Exception as e:
                return f"❌ Error: {e}"

        # Cek perintah /selesai — generate/update analisis, session tetap aktif
        if message.strip().lower() == "/selesai":
            result = generate_final_analysis(
                session_data["project_id"],
                session_data["project_name"],
                session_data["description"],
                session_data["chat_history"]
            )
            if result:
                result.pop("_id", None)
                output = {
                    "status": "success",
                    "project_id": session_data["project_id"],
                    "result": result
                }
                # JANGAN clear session — percakapan tetap lanjut
                return (
                    f"✅ **Analisis selesai/diperbarui!**\n\n"
                    f"```json\n{json.dumps(output, indent=2, ensure_ascii=False)}\n```\n\n"
                    f"💬 *Percakapan masih aktif. Lanjutkan diskusi atau ketik /selesai lagi untuk update analisis.*"
                )
            else:
                return "❌ Gagal menghasilkan analisis. Silakan coba lagi."

        # Percakapan biasa — kirim seluruh histori sebagai konteks
        project_id = session_data["project_id"]
        save_conversation(project_id, "user", message)
        session_data["chat_history"].append(("user", message))

        try:
            messages = build_openai_messages(CONVERSATION_PROMPT, session_data["chat_history"])
            agent_reply = retry_llm_call(
                lambda: chat_with_llm(messages, max_tokens=CONVERSATION_MAX_TOKENS, temperature=CONVERSATION_TEMPERATURE)
            )
            save_conversation(project_id, "agent", agent_reply)
            session_data["chat_history"].append(("agent", agent_reply))
            return agent_reply
        except Exception as e:
            return f"❌ Error: {e}"

    # API endpoint untuk Orchestrator (non-interaktif, langsung analisis)
    def analyze_api(project_id: str, description: str):
        """
        Endpoint POST /analyze untuk dipanggil Orchestrator.
        Langsung generate analisis tanpa percakapan.
        """
        if not description:
            return {"status": "error", "message": "Deskripsi proyek tidak boleh kosong"}

        if not project_id:
            project_id = generate_project_id()

        project_name = f"Project {project_id}"

        save_project({
            "project_id": project_id,
            "project_name": project_name,
            "description": description,
            "status": "in_progress"
        })
        save_conversation(project_id, "user", description)

        chat_history = [("user", description)]
        result = generate_final_analysis(project_id, project_name, description, chat_history)

        if result:
            result.pop("_id", None)
            return {"status": "success", "project_id": project_id, "result": result}
        else:
            return {"status": "error", "project_id": project_id, "message": "Gagal menganalisis proyek"}

    # Buat Gradio Blocks dengan Chat + API
    with gr.Blocks(title="🤖 Business Analyst Agent (#2)") as demo:
        gr.Markdown("# 🤖 Business Analyst Agent (#2)")
        gr.Markdown(
            "Agent AI untuk analisis kebutuhan bisnis. "
            "Ceritakan proyek Anda, saya akan bertanya untuk menggali kebutuhan. "
            "Ketik **`/selesai`** jika sudah siap untuk generate analisis.\n\n"
            "💡 *Untuk melanjutkan proyek lama, isi Project ID di bawah sebelum mengirim pesan.*"
        )

        with gr.Row():
            project_name_input = gr.Textbox(
                label="Nama Proyek",
                placeholder="Contoh: App Toko Online",
                scale=2
            )
            project_id_input = gr.Textbox(
                label="Project ID (opsional, untuk lanjutkan proyek lama)",
                placeholder="Contoh: proj_20260708120000",
                scale=2
            )

        chat = gr.ChatInterface(
            fn=chat_respond,
            additional_inputs=[project_name_input, project_id_input],
            chatbot=gr.Chatbot(height=500, placeholder="💬 Ceritakan proyek Anda..."),
            textbox=gr.Textbox(placeholder="Ketik pesan Anda di sini...", container=False),
            retry_btn=None,
            undo_btn=None,
            clear_btn="🗑️ Mulai Ulang",
        )

        # API endpoint terpisah untuk Orchestrator
        api_interface = gr.Interface(
            fn=analyze_api,
            inputs=[
                gr.Textbox(label="project_id"),
                gr.Textbox(label="description"),
            ],
            outputs=gr.JSON(),
            api_name="analyze",
        )

    demo.launch(server_name="0.0.0.0", server_port=7860)


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--serve" in sys.argv:
        run_gradio()
    else:
        run_cli()
