import os
import sqlite3

from flask import Flask, g, jsonify, render_template, request

app = Flask(__name__)
DATABASE = os.environ.get(
    "DATABASE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.db")
)
MAX_TITLE_LENGTH = 200


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def row_to_dict(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/tasks")
def list_tasks():
    rows = get_db().execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify(error="Название задачи не может быть пустым"), 400
    if len(title) > MAX_TITLE_LENGTH:
        return jsonify(error=f"Максимум {MAX_TITLE_LENGTH} символов"), 400
    db = get_db()
    cur = db.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
    db.commit()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(row_to_dict(row)), 201


@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    if "done" not in data:
        return jsonify(error="Поле done обязательно"), 400
    db = get_db()
    cur = db.execute(
        "UPDATE tasks SET done = ? WHERE id = ?", (1 if data["done"] else 0, task_id)
    )
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="Задача не найдена"), 404
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify(row_to_dict(row))


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    db = get_db()
    cur = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="Задача не найдена"), 404
    return "", 204


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT", 5000)))
