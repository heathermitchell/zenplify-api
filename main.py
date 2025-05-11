from flask import Flask, request, jsonify
from notion_client import Client
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Loads .env if running locally

# --- Config ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PAGE_ID = os.getenv("NOTION_PAGE_ID")  # Your Notion page where the database lives
DB_CACHE_FILE = Path("/tmp/database_id.txt")
DB_NAME = "Master Tree"

notion = Client(auth=NOTION_TOKEN)
app = Flask(__name__)

# --- Helpers ---
def get_or_create_database():
    if DB_CACHE_FILE.exists():
        return DB_CACHE_FILE.read_text().strip()

    if not PAGE_ID:
        raise Exception("Missing NOTION_PAGE_ID.")

    db = notion.databases.create(
        parent={"type": "page_id", "page_id": PAGE_ID},
        title=[{"type": "text", "text": {"content": DB_NAME}}],
        properties={
            "Tree": {"title": {}},
            "Type": {"rich_text": {}},
            "Status": {"select": {"options": [
                {"name": "Backlog", "color": "gray"},
                {"name": "In Progress", "color": "blue"},
                {"name": "Complete", "color": "green"},
            ]}},
            "Notes": {"rich_text": {}}
        }
    )

    database_id = db["id"]
    DB_CACHE_FILE.write_text(database_id)
    return database_id

def validate_input(data):
    required = ["Tree", "Type", "Status", "Notes"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"
    return True, None

# --- Routes ---
@app.route("/add", methods=["POST"])
def add_item():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    valid, msg = validate_input(data)
    if not valid:
        return jsonify({"error": msg}), 400

    try:
        db_id = get_or_create_database()
        notion.pages.create(
            parent={"database_id": db_id},
            properties={
                "Tree": {"title": [{"text": {"content": data["Tree"]}}]},
                "Type": {"rich_text": [{"text": {"content": data["Type"]}}]},
                "Status": {"select": {"name": data["Status"]}},
                "Notes": {"rich_text": [{"text": {"content": data["Notes"]}}]},
            }
        )
        return jsonify({"message": "Item added successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return "OK", 200

# --- Local Dev Run ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
