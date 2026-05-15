
PostgreSQL Attendance Web App

1. createdb attendance_db
2. psql attendance_db < schema.sql
3. Insert students:
   INSERT INTO students (roll_no,name) VALUES ('101','Anil');

4. python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

5. python app.py
