# Focus Todo

A simple, fully functional browser-based to-do list with a timer for every task.

## Features

- Add tasks
- Edit task names and timer duration
- Delete individual tasks
- Mark tasks complete/incomplete
- Start, pause, and reset a timer for each task
- Timer continues correctly after page refresh
- Optional browser notification when a timer finishes
- Filter by All, Active, and Completed
- Clear all completed tasks
- Saves tasks automatically using `localStorage`
- Responsive design for desktop and mobile
- No frameworks or dependencies required

## Run locally

1. Download or clone the repository.
2. Open `index.html` in a browser.

For the best browser notification support, run it using a local web server such as VS Code Live Server.

## Project files

- `index.html` — page structure
- `style.css` — layout and design
- `script.js` — task management, timers, filtering, editing, and local storage

## How the timer works

Each task stores its original duration, remaining time, running state, and start time. If the page is refreshed while a timer is running, the elapsed time is calculated when the page loads so the countdown stays accurate.
