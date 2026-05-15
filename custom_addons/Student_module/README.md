# Students Management Module

This Odoo module provides comprehensive tools for managing student information, attendance, departments, and skills within an educational environment.

## Features
- **Student Records:** Manage student details and profiles.
- **Attendance Tracking:** Monitor and record student attendance.
- **Department Management:** Organize students by academic departments.
- **Skills Tracking:** Maintain records of student skills and competencies.
- **Kanban View:** Integrated custom Kanban views for an intuitive user experience.

## Installation
1. Ensure you have an Odoo instance installed.
2. Clone this repository into your Odoo `addons` directory.
3. Restart your Odoo server.
4. Activate Developer Mode in Odoo.
5. Go to **Apps** > **Update Apps List**.
6. Search for "Students Management" and click **Install**.

## Requirements
- Odoo 19.0 (base module)

## Technical Overview
- **Models:**
    - `student.py`: Manages core student data.
    - `attendance.py`: Handles attendance logic and records.
    - `department.py`: Manages departmental structures.
    - `skills.py`: Tracks student skills.
- **Security:** Access control lists defined in `ir.model.access.csv`.
- **Views:** XML-based definitions for forms, trees, and menus.
- **Assets:** Custom CSS styling for the interface (including Kanban view).

## Author
- **THANUSH PRIYAN**

## License
(Add your license information here)
