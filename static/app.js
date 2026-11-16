const form = document.getElementById("add-form");
const input = document.getElementById("title");
const list = document.getElementById("list");
const empty = document.getElementById("empty");
const counter = document.getElementById("counter");
const errorBox = document.getElementById("error");
const progress = document.getElementById("progress");

let tasks = [];

function showError(message) {
  errorBox.textContent = message || "";
  errorBox.hidden = !message;
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let message = "Ошибка запроса";
    try {
      message = (await response.json()).error || message;
    } catch (_) {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function render() {
  list.innerHTML = "";
  for (const task of tasks) {
    const li = document.createElement("li");
    if (task.done) li.classList.add("done");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = task.done;
    checkbox.setAttribute("aria-label", "Выполнено");
    checkbox.addEventListener("change", () => toggleTask(task.id, checkbox.checked));

    const text = document.createElement("span");
    text.className = "text";
    text.textContent = task.title; // textContent защищает от XSS

    const del = document.createElement("button");
    del.className = "delete";
    del.type = "button";
    del.textContent = "×";
    del.setAttribute("aria-label", "Удалить задачу");
    del.addEventListener("click", () => deleteTask(task.id));

    li.append(checkbox, text, del);
    list.append(li);
  }

  const left = tasks.filter((t) => !t.done).length;
  counter.textContent = tasks.length ? `Осталось: ${left} из ${tasks.length}` : "";
  empty.hidden = tasks.length > 0;
  progress.style.width = tasks.length ? `${((tasks.length - left) / tasks.length) * 100}%` : "0%";
}

async function loadTasks() {
  try {
    tasks = await api("/api/tasks");
    showError("");
    render();
  } catch (e) {
    showError(e.message);
  }
}

async function toggleTask(id, done) {
  try {
    const updated = await api(`/api/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ done }),
    });
    tasks = tasks.map((t) => (t.id === id ? updated : t));
    showError("");
  } catch (e) {
    showError(e.message);
  }
  render();
}

async function deleteTask(id) {
  try {
    await api(`/api/tasks/${id}`, { method: "DELETE" });
    tasks = tasks.filter((t) => t.id !== id);
    showError("");
    render();
  } catch (e) {
    showError(e.message);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = input.value.trim();
  if (!title) {
    showError("Название задачи не может быть пустым");
    return;
  }
  try {
    const created = await api("/api/tasks", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
    tasks.unshift(created);
    input.value = "";
    showError("");
    render();
  } catch (e) {
    showError(e.message);
  }
  input.focus();
});

loadTasks();
