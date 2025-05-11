# Zenplify API

A lightweight Flask API that connects to Notion, powered by ChatGPT and deployed on Render.

## 🌱 What It Does

- Creates a Notion database called **Master Tree** (if it doesn't exist yet)
- Adds new entries to that database via a `/add` POST request
- Keeps the database ID cached for future calls
- Uses environment variables to stay secure
- Deploys using Python 3.11 on Render (with Gunicorn + optional Docker setup)

## 🛠 Tech Stack

- Python 3.11
- Flask 3.1
- Notion Client SDK
- Render (hosted)
- GitHub (versioning)
- Gunicorn (production-ready server)

## 🧠 Environment Variables

Set these in your Render dashboard:

| Variable        | Description                                  |
|----------------|----------------------------------------------|
| `NOTION_TOKEN`  | Your Notion integration secret               |
| `NOTION_PAGE_ID`| ID of the shared parent page for the database|

## 🚀 API Endpoints

### `POST /add`

Add a new item to the Master Tree.

#### Example JSON Body:

```json
{
  "Tree": "Content",
  "Type": "Spark",
  "Status": "Backlog",
  "Notes": "This is a test entry!"
}
