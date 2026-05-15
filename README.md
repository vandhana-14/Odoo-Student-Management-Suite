# Smart Attendance Management System

This repository contains both the Odoo-based management system and the Python-Flask web-based Attendance Management System.

## Odoo Modules

| Module Name | Description |
| :--- | :--- |
| **`students_app`** | Core management for students, attendance, exams, and marks. |
| **`students_dashboard`** | Spreadsheet dashboards for student analytics. |
| **`ask_ai`** | AI assistant integration for Discuss channels. |

## Web-Based Attendance Management System

A web-based application built with Python, Flask, and PostgreSQL.

### Features
- **Student Management:** Add new students to the system.
- **Attendance Tracking:** Simple check-in and check-out functionality.

### Installation
1. Clone this repository.
2. For the web-based system:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
3. For Odoo modules: Ensure your Odoo instance is configured with the `custom_addons` path.
