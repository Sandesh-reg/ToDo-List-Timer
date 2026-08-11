# Python To-Do List with Timer

A fully functional desktop to-do list built with Python and Tkinter.

## Features

- Add new tasks
- Give every task its own timer
- Start, pause, and reset timers
- Edit task names and timer durations
- Delete tasks
- Mark tasks complete or active again
- Filter tasks by All, Active, or Completed
- See total, active, and completed task counts
- Automatic alert when a timer finishes
- Automatically saves tasks to `tasks.json`
- Running timers are restored correctly after reopening the program
- Uses only Python standard-library modules

## Run the program

Make sure Python 3 is installed, then run:

```bash
python todo_app.py
```

On Windows you can also try:

```bash
py todo_app.py
```

## Requirements

- Python 3
- Tkinter (included with standard Python installations on Windows and macOS)

No `pip install` is required.

## Main file

`todo_app.py` contains the complete application.

The program creates `tasks.json` automatically when you add a task. That file stores your tasks and timer information so your data is available the next time you open the application.
