# SWE7301-API

**Flask API for Geospatial Observation Data - Group 4 Project**

This repository contains the backend infrastructure and functional modules for managing satellite observation data. It uses a modular architecture where specific User Stories are registered into a universal application factory.

---

## 👥 Team Contributions & Status

### 🛠 Syed Fraz Ali Naqvi (Infrastructure & DevOps)

- **US-22: ORM for API** — ✅ Done (Implemented via SQLAlchemy)
- **US-23: GitHub Source Control** — ✅ Done
- **US-19: SQLite for Development** — ✅ Done (Universal compatibility)
- **US-25: CI/CD Pipeline** — ⏳ In Progress (GitHub Actions)

### 🛰 Attiq-ur-Rehman (Functional Features)

- **US-10: Store Geospatial Data** — ✅ Done
- **US-09: Filter & Retrieve Data** — ✅ Done
- **US-11: Update Observation Data** — ✅ Done

### 🧪 Amir Tavass
* **US-05: Flask API Framework** — ✅ Done
* **US-06: API Documentation** — ✅ Done
* **US-13: JWT Authentication** — ✅ Done
* **US-24: Test-Driven Development** — 📅 Sprint Backlog

### 📝 Toluwalope Otegbeye
* **US-07: HTTP Methods** — ✅ Done
* **US-08: JSON Data Format** — ✅ Done
* **US-12: Bulk Operations** — ✅ Done
---

## 🏗 Universal Application Architecture

The project uses a central `app.py` that serves as the entry point, dynamically importing and registering feature modules (User Stories). This allows multiple developers to work on separate files without causing merge conflicts in the main application logic.
