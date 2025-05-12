from flask import Flask, request, jsonify
from flask_cors import CORS
from notion_client import Client
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

# --- Config ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PAGE_ID = os.getenv("NOTION_PAGE_ID")  # Your Notion page where databases live
DB_CACHE_FILE = Path("/tmp/database_id.txt")
DB_NAME = "Master Tree"

notion = Client(auth=NOTION_TOKEN)
app = Flask(__name__)
CORS(app)

# --- Retry Notion call if app just woke up ---
def safe_notion_call(func, retries=1, delay=2):
    try:
        return func()
    except Exception as e:
        if retries > 0:
            time.sleep(delay)
            return safe_notion_call(func, retries - 1, delay)
        else:
            raise e

# --- Helpers ---
def get_or_create_database():
    if DB_CACHE_FILE.exists():
        return DB_CACHE_FILE.read_text().strip()

    if not PAGE_ID:
        raise Exception("Missing NOTION_PAGE_ID.")

    def create_db():
        return notion.databases.create(
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

    db = safe_notion_call(create_db)
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

        def add_page():
            return notion.pages.create(
                parent={"database_id": db_id},
                properties={
                    "Tree": {"title": [{"text": {"content": data["Tree"]}}]},
                    "Type": {"rich_text": [{"text": {"content": data["Type"]}}]},
                    "Status": {"select": {"name": data["Status"]}},
                    "Notes": {"rich_text": [{"text": {"content": data["Notes"]}}]},
                }
            )

        safe_notion_call(add_page)
        return jsonify({"message": "Item added successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/create_table", methods=["POST"])
def create_table():
    data = request.get_json()
    table_name = data.get("table")
    fields = data.get("fields")

    if not table_name or not fields:
        return jsonify({"error": "Missing table name or fields"}), 400

    try:
        # Convert fields into Notion property format
        properties = {}
        for name, ftype in fields.items():
            if ftype == "rich_text":
                properties[name] = {"rich_text": {}}
            elif ftype == "title":
                properties[name] = {"title": {}}
            elif ftype == "select":
                properties[name] = {"select": {}}
            else:
                properties[name] = {"rich_text": {}}  # default fallback

        # Ensure at least one title field
        if not any("title" in prop for prop in properties.values()):
            properties["Name"] = {"title": {}}

        def create_db():
            return notion.databases.create(
                parent={"type": "page_id", "page_id": PAGE_ID},
                title=[{"type": "text", "text": {"content": table_name}}],
                properties=properties
            )

        db = safe_notion_call(create_db)
        return jsonify({"message": "Database created", "database_id": db["id"]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/add_column", methods=["POST"])
def add_column():
    data = request.get_json()
    db_id = data.get("database_id")
    column = data.get("column")
    col_type = data.get("type")  # e.g., "rich_text"

    if not db_id or not column or not col_type:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        def update_db():
            return notion.databases.update(
                database_id=db_id,
                properties={column: {"rich_text": {}} if col_type == "rich_text" else {"rich_text": {}}}
            )

        safe_notion_call(update_db)
        return jsonify({"message": f"Column '{column}' added."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/insert", methods=["POST"])
def insert_row():
    data = request.get_json()
    db_id = data.get("database_id")
    values = data.get("values")

    if not db_id or not values:
        return jsonify({"error": "Missing database_id or values"}), 400

    try:
        properties = {
            k: {"rich_text": [{"text": {"content": v}}]} for k, v in values.items()
        }

        def insert_page():
            return notion.pages.create(
                parent={"database_id": db_id},
                properties=properties
            )

        safe_notion_call(insert_page)
        return jsonify({"message": "Row inserted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return "OK", 200

# --- Local Dev Run ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
