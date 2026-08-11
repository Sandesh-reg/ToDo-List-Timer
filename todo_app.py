import json
import os
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

DATA_FILE = "tasks.json"
TICK_MS = 250


def format_seconds(seconds: int) -> str:
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class TodoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Python To-Do List with Timer")
        self.root.geometry("920x620")
        self.root.minsize(780, 520)

        self.tasks = []
        self.selected_task_id = None

        self._build_ui()
        self._load_tasks()
        self._refresh_tree()
        self._tick()

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(outer, text="Python To-Do List", font=("Segoe UI", 22, "bold"))
        title.pack(anchor="w")
        subtitle = ttk.Label(
            outer,
            text="Add tasks, edit them, delete them, mark them complete, and run a separate timer for each task.",
        )
        subtitle.pack(anchor="w", pady=(2, 14))

        entry_frame = ttk.LabelFrame(outer, text="Add a task", padding=12)
        entry_frame.pack(fill="x")

        ttk.Label(entry_frame, text="Task:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.task_entry = ttk.Entry(entry_frame)
        self.task_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        self.task_entry.bind("<Return>", lambda _event: self.add_task())

        ttk.Label(entry_frame, text="Timer (minutes):").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.minutes_var = tk.StringVar(value="25")
        self.minutes_spin = ttk.Spinbox(entry_frame, from_=1, to=1440, textvariable=self.minutes_var, width=8)
        self.minutes_spin.grid(row=0, column=3, sticky="w", padx=(0, 12))

        ttk.Button(entry_frame, text="Add Task", command=self.add_task).grid(row=0, column=4, sticky="e")
        entry_frame.columnconfigure(1, weight=1)

        filter_frame = ttk.Frame(outer)
        filter_frame.pack(fill="x", pady=(12, 8))

        ttk.Label(filter_frame, text="Show:").pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        filter_box = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=["All", "Active", "Completed"],
            state="readonly",
            width=12,
        )
        filter_box.pack(side="left", padx=(8, 0))
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh_tree())

        self.summary_label = ttk.Label(filter_frame, text="0 tasks")
        self.summary_label.pack(side="right")

        tree_frame = ttk.Frame(outer)
        tree_frame.pack(fill="both", expand=True)

        columns = ("status", "task", "timer", "timer_state")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("status", text="Status")
        self.tree.heading("task", text="Task")
        self.tree.heading("timer", text="Timer")
        self.tree.heading("timer_state", text="Timer State")
        self.tree.column("status", width=95, anchor="center", stretch=False)
        self.tree.column("task", width=430, anchor="w")
        self.tree.column("timer", width=110, anchor="center", stretch=False)
        self.tree.column("timer_state", width=110, anchor="center", stretch=False)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda _event: self.edit_task())

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(outer)
        button_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(button_frame, text="Mark Complete / Active", command=self.toggle_complete).pack(side="left")
        ttk.Button(button_frame, text="Edit Task", command=self.edit_task).pack(side="left", padx=6)
        ttk.Button(button_frame, text="Delete Task", command=self.delete_task).pack(side="left")

        timer_controls = ttk.Frame(button_frame)
        timer_controls.pack(side="right")
        ttk.Button(timer_controls, text="Start Timer", command=self.start_timer).pack(side="left")
        ttk.Button(timer_controls, text="Pause", command=self.pause_timer).pack(side="left", padx=6)
        ttk.Button(timer_controls, text="Reset", command=self.reset_timer).pack(side="left")

        footer = ttk.Label(
            outer,
            text="Tip: Double-click a task to edit it. Tasks are saved automatically in tasks.json.",
        )
        footer.pack(anchor="w", pady=(10, 0))

    def _new_id(self):
        return str(time.time_ns())

    def _validate_minutes(self, value=None):
        raw = self.minutes_var.get() if value is None else str(value)
        try:
            minutes = int(raw)
        except ValueError:
            raise ValueError("Timer must be a whole number of minutes.")
        if not 1 <= minutes <= 1440:
            raise ValueError("Timer must be between 1 and 1440 minutes.")
        return minutes

    def add_task(self):
        title = self.task_entry.get().strip()
        if not title:
            messagebox.showwarning("Missing task", "Please enter a task name.")
            return

        try:
            minutes = self._validate_minutes()
        except ValueError as exc:
            messagebox.showwarning("Invalid timer", str(exc))
            return

        seconds = minutes * 60
        self.tasks.append(
            {
                "id": self._new_id(),
                "title": title,
                "completed": False,
                "duration_seconds": seconds,
                "remaining_seconds": seconds,
                "running": False,
                "end_time": None,
                "notified": False,
            }
        )
        self.task_entry.delete(0, tk.END)
        self.task_entry.focus_set()
        self._save_tasks()
        self._refresh_tree()

    def _selected_task(self):
        if not self.selected_task_id:
            return None
        return next((task for task in self.tasks if task["id"] == self.selected_task_id), None)

    def _require_selection(self):
        task = self._selected_task()
        if task is None:
            messagebox.showinfo("Select a task", "Please select a task first.")
        return task

    def _on_select(self, _event=None):
        selection = self.tree.selection()
        self.selected_task_id = selection[0] if selection else None

    def toggle_complete(self):
        task = self._require_selection()
        if not task:
            return
        task["completed"] = not task["completed"]
        if task["completed"]:
            self._pause_task(task)
        self._save_tasks()
        self._refresh_tree(keep_selection=True)

    def edit_task(self):
        task = self._require_selection()
        if not task:
            return

        new_title = simpledialog.askstring("Edit task", "Task name:", initialvalue=task["title"], parent=self.root)
        if new_title is None:
            return
        new_title = new_title.strip()
        if not new_title:
            messagebox.showwarning("Invalid task", "Task name cannot be empty.")
            return

        current_minutes = max(1, round(task["duration_seconds"] / 60))
        new_minutes = simpledialog.askinteger(
            "Edit timer",
            "Timer length in minutes:",
            initialvalue=current_minutes,
            minvalue=1,
            maxvalue=1440,
            parent=self.root,
        )
        if new_minutes is None:
            return

        was_running = task["running"]
        task["title"] = new_title
        task["duration_seconds"] = new_minutes * 60
        task["remaining_seconds"] = new_minutes * 60
        task["running"] = False
        task["end_time"] = None
        task["notified"] = False

        self._save_tasks()
        self._refresh_tree(keep_selection=True)

        if was_running:
            messagebox.showinfo("Timer reset", "Editing the timer reset and paused it.")

    def delete_task(self):
        task = self._require_selection()
        if not task:
            return
        if not messagebox.askyesno("Delete task", f"Delete '{task['title']}'?"):
            return
        self.tasks = [item for item in self.tasks if item["id"] != task["id"]]
        self.selected_task_id = None
        self._save_tasks()
        self._refresh_tree()

    def start_timer(self):
        task = self._require_selection()
        if not task:
            return
        if task["completed"]:
            messagebox.showinfo("Completed task", "Mark the task active before starting its timer.")
            return
        if task["remaining_seconds"] <= 0:
            task["remaining_seconds"] = task["duration_seconds"]
        task["running"] = True
        task["end_time"] = time.time() + task["remaining_seconds"]
        task["notified"] = False
        self._save_tasks()
        self._refresh_tree(keep_selection=True)

    def _pause_task(self, task):
        if task["running"] and task.get("end_time"):
            task["remaining_seconds"] = max(0, int(round(task["end_time"] - time.time())))
        task["running"] = False
        task["end_time"] = None

    def pause_timer(self):
        task = self._require_selection()
        if not task:
            return
        self._pause_task(task)
        self._save_tasks()
        self._refresh_tree(keep_selection=True)

    def reset_timer(self):
        task = self._require_selection()
        if not task:
            return
        task["remaining_seconds"] = task["duration_seconds"]
        task["running"] = False
        task["end_time"] = None
        task["notified"] = False
        self._save_tasks()
        self._refresh_tree(keep_selection=True)

    def _tick(self):
        changed = False
        finished = []
        now = time.time()

        for task in self.tasks:
            if not task.get("running"):
                continue
            end_time = task.get("end_time")
            if not end_time:
                task["end_time"] = now + task["remaining_seconds"]
                end_time = task["end_time"]
                changed = True

            remaining = max(0, int(round(end_time - now)))
            if remaining != task["remaining_seconds"]:
                task["remaining_seconds"] = remaining
                changed = True

            if remaining <= 0:
                task["running"] = False
                task["end_time"] = None
                if not task.get("notified"):
                    task["notified"] = True
                    finished.append(task["title"])
                changed = True

        if changed:
            self._save_tasks()
            self._refresh_tree(keep_selection=True)

        for title in finished:
            self.root.bell()
            messagebox.showinfo("Timer finished", f"Time is up for:\n{title}")

        self.root.after(TICK_MS, self._tick)

    def _filtered_tasks(self):
        current_filter = self.filter_var.get()
        if current_filter == "Active":
            return [task for task in self.tasks if not task["completed"]]
        if current_filter == "Completed":
            return [task for task in self.tasks if task["completed"]]
        return self.tasks

    def _refresh_tree(self, keep_selection=False):
        selected_id = self.selected_task_id if keep_selection else None

        for item in self.tree.get_children():
            self.tree.delete(item)

        for task in self._filtered_tasks():
            status = "Completed" if task["completed"] else "Active"
            if task["remaining_seconds"] <= 0:
                timer_state = "Finished"
            elif task["running"]:
                timer_state = "Running"
            else:
                timer_state = "Paused" if task["remaining_seconds"] < task["duration_seconds"] else "Ready"

            self.tree.insert(
                "",
                "end",
                iid=task["id"],
                values=(status, task["title"], format_seconds(task["remaining_seconds"]), timer_state),
            )

        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)
            self.tree.focus(selected_id)
            self.selected_task_id = selected_id
        elif not keep_selection:
            self.selected_task_id = None

        total = len(self.tasks)
        completed = sum(task["completed"] for task in self.tasks)
        active = total - completed
        self.summary_label.config(text=f"{total} total • {active} active • {completed} completed")

    def _save_tasks(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(self.tasks, file, indent=2)
        except OSError as exc:
            messagebox.showerror("Save error", f"Could not save tasks:\n{exc}")

    def _load_tasks(self):
        if not os.path.exists(DATA_FILE):
            self.tasks = []
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.tasks = data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            self.tasks = []
            messagebox.showwarning("Load warning", "tasks.json could not be read. Starting with an empty task list.")
            return

        now = time.time()
        for task in self.tasks:
            task.setdefault("id", self._new_id())
            task.setdefault("title", "Untitled task")
            task.setdefault("completed", False)
            task.setdefault("duration_seconds", 25 * 60)
            task.setdefault("remaining_seconds", task["duration_seconds"])
            task.setdefault("running", False)
            task.setdefault("end_time", None)
            task.setdefault("notified", False)

            if task["running"] and task.get("end_time"):
                remaining = max(0, int(round(task["end_time"] - now)))
                task["remaining_seconds"] = remaining
                if remaining == 0:
                    task["running"] = False
                    task["end_time"] = None


if __name__ == "__main__":
    root = tk.Tk()
    TodoApp(root)
    root.mainloop()
