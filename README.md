# CampusBite

**Skip the Queue, Enjoy Your Food!** A responsive college canteen ordering prototype for students and canteen staff.

## Project overview

CampusBite addresses long queues, wasted break time, manual ordering, and uncertainty about menu availability. Students can browse a live menu, keep a cart, place pickup orders, follow a digital token, and share feedback. Canteen staff can manage menu items, update order stages, and review feedback from a separate dashboard.

This is a functional local prototype built with free tools. Orders and payments are stored in SQLite. The UPI flow is a **simulation only**; it never connects to a payment provider and does not transfer money.

## Problem statement

Students have short breaks and often spend too much of them waiting in a canteen queue. They may not know which dishes are available until they reach the counter, and staff take orders manually during a rush. CampusBite lets students check availability and order before pickup while giving staff a simple way to manage the menu and order queue.

## Objectives

- Reduce time spent waiting in line and checking availability.
- Make canteen ordering easy to use on mobile and desktop.
- Give students an order token and clear pickup progress.
- Give canteen staff direct control of menu availability, prices, and order status.
- Collect food reviews and suggestions for future improvements.

## Features

- Student registration, login, profile, logout, and password hashing.
- Menu with seeded dishes, INR prices, search, category filters, sold-out states, and food photography.
- Persistent SQLite cart that can be built before login and carried into a student account.
- Quantity controls, item removal, clear-cart action, subtotal, and pickup checkout.
- Cash on pickup with pending payment status.
- Simulated UPI page with a decorative demo QR, explicit no-charge messaging, a Pay Now simulation, and a demo transaction reference.
- Unique pickup token, customer name, order items, total, payment details, estimated wait, order history, and four-stage order tracking.
- Rule-based recommendations based on order history, browsing category, and popularity. No paid AI API is used.
- Student ratings, food reviews, and suggestions stored in SQLite.
- Separate admin login and dashboard with order and sales statistics, menu item create/edit/delete, availability toggles, order status updates, and feedback review.
- Responsive layouts, mobile navigation, loading feedback, dismissible notifications, and offline image fallbacks.
- CSRF checks for form submissions in normal app mode.

## Technology stack

- Python 3.10+ and Flask
- SQLite (included with Python)
- Jinja templates, HTML5, CSS3, and JavaScript
- Werkzeug password hashing
- Free Unsplash image URLs with a local visual fallback if the images are unavailable

## Project structure

```text
CampusBite/
├── app.py
├── campusbite/
│   ├── __init__.py       # Flask app factory and shared configuration
│   ├── db.py             # SQLite schema, connection, and starter data
│   └── web.py            # Student, order, feedback, and admin routes
├── database.db           # Created automatically at first run (not committed)
├── requirements.txt
├── templates/            # Jinja pages and reusable food-card partial
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   └── images/
├── tests/test_app.py
├── DESIGN_THINKING_REPORT.md
└── README.md
```

## Install and run on Windows

Open PowerShell in the project folder:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks environment activation, you can skip activation and use the virtual environment's Python directly:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

If `python -m venv .venv` reports that `ensurepip` failed, create the environment without bundled pip and let your installed pip seed it:

```powershell
python -m venv .venv --without-pip
python -m pip --python .venv\Scripts\python.exe install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:5000** in your browser. Press `Ctrl+C` in PowerShell to stop the local server. Python 3.10 or newer is recommended.

The database and starter menu are created automatically on first run. Canteen hours in the prototype are 8:00 AM–5:00 PM using your laptop's local clock. To start over, stop the app and delete `database.db`; the next run will create a fresh database. Keep the database file if you want to retain student accounts, orders, and feedback.

### Demo admin account

- Email: `admin@campusbite.local`
- Password: `CampusBite@2026`
- Admin sign-in page: **http://127.0.0.1:5000/admin/login**

For a fresh database, you can choose initial admin credentials before the first run by setting these PowerShell environment variables:

```powershell
$env:CAMPUSBITE_ADMIN_EMAIL = "canteen@example.edu"
$env:CAMPUSBITE_ADMIN_PASSWORD = "choose-a-strong-local-password"
python app.py
```

The seed admin is created only when no admin account exists yet. The local fallback Flask secret is intended for development; set `CAMPUSBITE_SECRET` to a private random value before exposing the app beyond your laptop. The prototype is not a production deployment configuration.

## Testing

With the virtual environment active:

```powershell
python -m unittest discover -s tests -v
```

The tests use a temporary database and cover registration/login, menu search, cart changes, cash and UPI demo checkout, tokens, tracking, admin menu and order operations, and feedback.

## Screenshots

The application pages are served dynamically from the local app. Capture screenshots after running `python app.py` for your presentation; suggested views are:

1. Home page and category navigation.
2. Menu search and availability indicators.
3. Simulated UPI page and pickup token.
4. Student order tracking.
5. Admin dashboard and menu controls.

## Future scope

- College SSO and role management.
- Live kitchen queue and configurable preparation estimates.
- Canteen-side pickup display and real-time status updates.
- Nutrition and allergen details.
- Better demand and stock forecasting from historical orders.
- A production deployment with managed secrets, backups, monitoring, and accessibility review.

## Team members

Add the project team's names, class/section, and responsibilities here before submission.

