from datetime import datetime, date, time
from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    jsonify
)
from werkzeug.utils import secure_filename
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()   # 🔑 MUST be before os.getenv()


# ================= APP =================

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# ================= DATABASE =================
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
# ================= UPLOAD CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= HELPERS =================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ================= HOME / ATTENDANCE LIST =================
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    date_value = request.args.get("date", "").strip()

    try:
        cur = conn.cursor()

        query = """
            SELECT a.student_id, s.name,
                   a.attendance_date, a.check_in_time, a.check_out_time
            FROM attendance a
            JOIN add_students s ON s.student_id = a.student_id
            WHERE 1=1
        """
        params = []

        if q:
            query += " AND (a.student_id ILIKE %s OR s.name ILIKE %s)"
            params.extend([f"%{q}%", f"%{q}%"])

        if date_value:
            query += " AND a.attendance_date = %s"
            params.append(date_value)

        query += " ORDER BY a.attendance_date DESC"

        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()

        attendance_records = [
            {
                "student_id": r[0],
                "name": r[1],
                "attendance_date": r[2],
                "check_in_time": r[3],
                "check_out_time": r[4],
            }
            for r in rows
        ]

        return render_template("index.html", attendance_records=attendance_records)

    except Exception as e:
        conn.rollback()
        print("Index error:", e)
        return render_template("index.html", attendance_records=[])

@app.route("/attendance_list")
def attendance_list():
    return index()

# ================= ADD STUDENTS =================
 
@app.route("/add_students", methods=["GET", "POST"])
def add_students():
    cur = conn.cursor()
    cur.execute("SELECT dept_code FROM departments ORDER BY dept_code")
    departments = cur.fetchall()
    cur.close()
    if request.method == "POST":
        try:
            name = request.form.get("name")
            student_id = request.form.get("student_id")
            email = request.form.get("email")
            phone = request.form.get("phone")
            address = request.form.get("address")
            course = request.form.get("course")

            day = request.form.get("day")
            month = request.form.get("month")
            year = request.form.get("year")

            birth = date(int(year), int(month), int(day)) if day and month and year else None

            file = request.files.get("document")
            resume_path = None

            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Invalid file type", "error")
                    return redirect(url_for("add_students"))

                filename = secure_filename(file.filename)
                resume_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(resume_path)

            cur = conn.cursor()
            cur.execute("""
                INSERT INTO add_students
                (name, birth, student_id, department, email, phone, address, resume_path)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (name, birth, student_id, course, email, phone, address, resume_path))

            conn.commit()
            cur.close()

            flash("Student added successfully!", "success")
            return redirect(url_for("view_students"))
        
        except psycopg2.errors.UniqueViolation as e:
            conn.rollback()

            error_msg = str(e)

            if "add_students_email_key" in error_msg:
                flash("❌ Email already exists. Please use a different email.", "error")

            elif "add_students_student_id_key" in error_msg:
                flash("❌ Student ID already exists. Please use a unique ID.", "error")

            else:
                flash("❌ Duplicate data detected.", "error")

            return redirect(url_for("add_students"))

        except Exception as e:
            conn.rollback()
            print("Add student error:", e)
            flash("Failed to add student", "error")
            return redirect(url_for("add_students"))

    return render_template("add_students.html",departments=departments)


# ================= ATTENDANCE =================
@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if request.method == "POST":
        try:
            student_id = request.form.get("student_id")

            # 📅 DATE: auto today, allow manual override
            date_value = request.form.get("date")
            attendance_date = (
                datetime.strptime(date_value, "%Y-%m-%d").date()
                if date_value else date.today()
            )

            # ⏱ TIME: manual or auto current time
            check_in_input = request.form.get("check_in_time")
            check_out_input = request.form.get("check_out_time")
            now_time = datetime.now().time().replace(microsecond=0)

            cur = conn.cursor()

            # ✅ ACTIVE STUDENT CHECK
            cur.execute("""
                SELECT name FROM add_students
                WHERE student_id = %s AND active = TRUE
            """, (student_id,))
            student = cur.fetchone()

            if not student:
                cur.close()
                flash("Inactive or invalid student ID", "error")
                return redirect(url_for("attendance"))

            student_name = student[0]

            # 🔍 CHECK TODAY'S ATTENDANCE
            cur.execute("""
                SELECT id, check_in_time, check_out_time
                FROM attendance
                WHERE student_id = %s AND attendance_date = %s
            """, (student_id, attendance_date))
            row = cur.fetchone()

            # ================= CHECK-IN =================
            if not row:
                check_in_time = (
                    datetime.strptime(check_in_input, "%H:%M").time()
                    if check_in_input else now_time
                )

                cur.execute("""
                    INSERT INTO attendance
                    (student_id, attendance_date, check_in_time)
                    VALUES (%s, %s, %s)
                """, (student_id, attendance_date, check_in_time))

                conn.commit()
                message = "Check-in successful"

            # ================= CHECK-OUT =================
            else:
                if row[2] is not None:
                    flash("Already checked out for today", "error")
                    cur.close()
                    return redirect(url_for("attendance"))

                check_out_time = (
                    datetime.strptime(check_out_input, "%H:%M").time()
                    if check_out_input else now_time
                )

                cur.execute("""
                    UPDATE attendance
                    SET check_out_time = %s
                    WHERE id = %s
                """, (check_out_time, row[0]))

                conn.commit()
                message = "Check-out successful"

            cur.close()

            return render_template(
                "attendance.html",
                success=True,
                message=message,
                student_name=student_name,
                student_id=student_id,
                attendance_date=attendance_date
            )

        except Exception as e:
            conn.rollback()
            print("Attendance error:", e)
            flash("Attendance failed", "error")
            return redirect(url_for("attendance"))

    return render_template("attendance.html")

# ================= VIEW STUDENTS =================
@app.route("/view_students")
def view_students():
    search = request.args.get("search", "")
    course = request.args.get("course", "")
    status = request.args.get("status", "")

    try:
        cur = conn.cursor()

        cur.execute("SELECT dept_code, dept_name FROM departments ORDER BY dept_name")
        departments = cur.fetchall()

        query = """
            SELECT id, name, student_id, department, email, active
            FROM add_students WHERE 1=1
        """
        params = []

        if search:
            query += " AND (name ILIKE %s OR student_id ILIKE %s OR email ILIKE %s)"
            params.extend([f"%{search}%"] * 3)

        if course:
            query += " AND department = %s"
            params.append(course)

        if status == "active":
            query += " AND active = TRUE"
        elif status == "inactive":
            query += " AND active = FALSE"

        query += " ORDER BY id DESC"

        cur.execute(query, params)
        students = cur.fetchall()
        cur.close()

        return render_template(
            "view_students.html",
            students=students,
            departments=departments
        )

    except Exception as e:
        conn.rollback()
        print("View students error:", e)
        return render_template("view_students.html", students=[], departments=[])


# ================= TOGGLE SINGLE =================
@app.route("/view_students/<int:id>/toggle", methods=["POST"])
def toggle_student(id):
    try:
        cur = conn.cursor()

        cur.execute("""
            UPDATE add_students
            SET active = NOT active
            WHERE id = %s
            RETURNING active
        """, (id,))

        new_status = cur.fetchone()[0]

        conn.commit()
        cur.close()

        return jsonify({
            "success": True,
            "active": new_status
        })

    except Exception as e:
        conn.rollback()
        print("Toggle error:", e)
        return jsonify({"success": False}), 500



# ================= UPDATE STUDENT =================
@app.route("/students/<int:id>/update", methods=["POST"])
def update_student(id):
    try:
        data = request.get_json()

        cur = conn.cursor()
        cur.execute("""
            UPDATE add_students
            SET
              name=%s,
              department=%s,
              email=%s,
              phone=%s,
              address=%s
            WHERE id=%s
        """, (
            data["name"],
            data["course"],
            data["email"],
            data["phone"],
            data["address"],
            id
        ))

        conn.commit()
        cur.close()
        return jsonify(success=True)

    except Exception as e:
        conn.rollback()
        print("Update error:", e)
        return jsonify(success=False), 500



# ================= DELETE SINGLE =================
@app.route("/students/<int:id>/delete", methods=["POST"])
def delete_student(id):
    try:
        cur = conn.cursor()

        # ❗ Prevent delete if active
        cur.execute("SELECT active FROM add_students WHERE id=%s", (id,))
        row = cur.fetchone()

        if not row or row[0]:
            cur.close()
            return jsonify({"success": False, "error": "Active student"}), 403

        cur.execute("DELETE FROM add_students WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        print("Delete error:", e)
        return jsonify({"success": False}), 500



# ================= BULK ENABLE / DISABLE =================
@app.route("/students/bulk-toggle", methods=["POST"])
def bulk_toggle():
    try:
        data = request.get_json()
        ids = list(map(int, data.get("ids", [])))  # 🔑 FIX
        status = data.get("status")

        if not ids:
            return jsonify({"error": "No IDs"}), 400

        cur = conn.cursor()
        cur.execute(
            """
            UPDATE add_students
            SET active = %s
            WHERE id = ANY(%s)
            """,
            (status, ids)
        )
        conn.commit()
        cur.close()

        return jsonify(success=True)

    except Exception as e:
        conn.rollback()
        print("Bulk toggle error:", e)
        return jsonify(success=False), 500

        return jsonify(success=False), 500


# ================= BULK DELETE =================
@app.route("/students/bulk-delete", methods=["POST"])
def bulk_delete_students():
    try:
        data = request.get_json(force=True)

        # force integer conversion
        ids = [int(i) for i in data.get("ids", [])]

        if not ids:
            return jsonify({"error": "No IDs provided"}), 400

        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM add_students
            WHERE id = ANY(%s::INTEGER[])
              AND active = FALSE
            """,
            (ids,)
        )

        conn.commit()
        cur.close()

        return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        print("Bulk delete error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
