
from flask import Flask, render_template, request
from datetime import datetime
import psycopg2

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "database": "attendance_db",
    "user": "odoo19",
    "password": "odoo19",
    "port":"5433"
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        roll = request.form["roll"]
        mode = request.form["mode"]
        status = request.form.get("status", "P")

        today = datetime.now().date()
        now = datetime.now().time()

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT name FROM students WHERE roll_no=%s", [roll])
        student = cur.fetchone()
        if not student:
            message = "Invalid roll number"
            conn.close()
            return render_template("index.html", message=message)

        name = student[0]

        if mode == "checkin":
            cur.execute(
                "SELECT id FROM attendance WHERE roll_no=%s AND date=%s",
                (roll, today)
            )
            if cur.fetchone():
                message = "Already checked in"
            else:
                cur.execute(
                    "INSERT INTO attendance (date, roll_no, name, status, check_in) VALUES (%s,%s,%s,%s,%s)",
                    (today, roll, name, status, now)
                )
                conn.commit()
                message = "Check-in successful"

        elif mode == "checkout":
            cur.execute(
                "SELECT id, check_out FROM attendance WHERE roll_no=%s AND date=%s",
                (roll, today)
            )
            row = cur.fetchone()
            if not row:
                message = "No check-in found"
            elif row[1] is not None:
                message = "Already checked out"
            else:
                cur.execute(
                    "UPDATE attendance SET check_out=%s WHERE id=%s",
                    (now, row[0])
                )
                conn.commit()
                message = "Check-out successful"

        conn.close()

    return render_template("index.html", message=message)

@app.route("/students", methods=["GET", "POST"])
def students():
    message = ""
    if request.method == "POST":
        name = request.form["name"]
        roll = request.form["roll"]
        email = request.form["email"]
        phone = request.form["phone"]

        conn = get_conn()
        cur = conn.cursor()
        if len(phone) != 10:
            message = "Phone number must be 10 digits"
            return render_template("students.html", message=message)
        
        cur.execute("SELECT id FROM students WHERE roll_no=%s", (roll,))
        if cur.fetchone():
            message = "Roll number already exists"
        else:
            cur.execute(
                "INSERT INTO students (name, roll_no, email, phone_no) VALUES (%s, %s, %s, %s)",
                (name, roll, email, phone)
            )
            conn.commit()
            message = "Student added successfully"

        conn.close()

    return render_template("students.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)
