import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

# 1. Flask колдонмосун туура баштоо
app = Flask(__name__)
app.secret_key = "quran-school-secret-key"
DATABASE = "database.db"

# =========================
# DATABASE
# =========================
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS teacher_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER NOT NULL,
            lesson_number INTEGER NOT NULL,
            topic TEXT NOT NULL,
            lesson_date TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            semester INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            birth_year INTEGER,
            course_id INTEGER NOT NULL,
            parent_name TEXT,
            phone TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS student_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            assignment_id INTEGER NOT NULL,
            lesson_date TEXT NOT NULL,
            attendance TEXT NOT NULL,
            grade TEXT,
            note TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            student_id INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS quran_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juz_number INTEGER NOT NULL UNIQUE,
            section_name TEXT,
            start_reference TEXT,
            end_reference TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS quran_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            juz_number INTEGER NOT NULL,
            surah_name TEXT,
            start_ayah INTEGER,
            end_ayah INTEGER,
            status TEXT NOT NULL,
            progress_date TEXT NOT NULL,
            grade TEXT,
            note TEXT,
            teacher_id INTEGER,
            semester INTEGER DEFAULT 1
        )
    """)

    try:
        conn.execute("ALTER TABLE lessons ADD COLUMN semester INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE quran_progress ADD COLUMN semester INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    courses = ["1-курс", "2-курс", "3-курс", "4-курс", "5-курс", "6-курс"]
    for course in courses:
        existing = conn.execute("SELECT id FROM courses WHERE name = ?", (course,)).fetchone()
        if not existing:
            conn.execute("INSERT INTO courses (name) VALUES (?)", (course,))

    subjects = ["Куран жаттоо", "Фикх", "Акыйда", "Хадис", "Тафсир", "Тажвид", "Сийра", "Араб тили"]
    for subject in subjects:
        existing = conn.execute("SELECT id FROM subjects WHERE name = ?", (subject,)).fetchone()
        if not existing:
            conn.execute("INSERT INTO subjects (name) VALUES (?)", (subject,))

    quran_sections = [
        (1, "الم", "الفاتحة 1", "البقرة 141"),
        (2, "سيقول", "البقرة 142", "البقرة 252"),
        (3, "تلك الرسل", "البقرة 253", "آل عمران 92"),
        (4, "لن تنالوا", "آل عمران 93", "النساء 23"),
        (5, "والمحصنات", "النساء 24", "النساء 147"),
        (6, "لا يحب الله", "النساء 148", "المائدة 81"),
        (7, "وإذا سمعوا", "المائدة 82", "الأنعام 110"),
        (8, "ولو أننا", "الأنعام 111", "الأعراف 87"),
        (9, "قال الملأ", "الأعراف 88", "الأنفال 40"),
        (10, "واعلموا", "الأنفال 41", "التوبة 92"),
        (11, "يعتذرون", "التوبة 93", "هود 5"),
        (12, "وما من دابة", "هود 6", "يوسف 52"),
        (13, "وما أبرئ", "يوسف 53", "إبراهيم 52"),
        (14, "ربما", "الحجر 1", "النحل 128"),
        (15, "سبحان الذي", "الإسراء 1", "الكهف 74"),
        (16, "قال ألم", "الكهف 75", "طه 135"),
        (17, "اقترب للناس", "الأنبياء 1", "الحج 78"),
        (18, "قد أفلح", "المؤمنون 1", "الفرقان 20"),
        (19, "وقال الذين", "الفرقان 21", "النمل 55"),
        (20, "فما كان جواب", "النمل 56", "العنكبوت 45"),
        (21, "اتل ما أوحي", "العنكبوت 46", "الأحزاب 30"),
        (22, "ومن يقنت", "الأحزاب 31", "يس 27"),
        (23, "وما أنزلنا", "يس 28", "الزمر 31"),
        (24, "فمن أظلم", "الزمر 32", "فصلت 46"),
        (25, "إليه يرد", "فصلت 47", "الجاثية 37"),
        (26, "حم", "الأحقاف 1", "الذاريات 30"),
        (27, "قال فما خطبكم", "الذاريات 31", "الحديد 29"),
        (28, "قد سمع الله", "المجادلة 1", "التحريم 12"),
        (29, "تبارك الذي", "الملك 1", "المرسلات 50"),
        (30, "عم يتساءلون", "النبأ 1", "الناس 6")
    ]

    for item in quran_sections:
        existing = conn.execute("SELECT id FROM quran_sections WHERE juz_number = ?", (item[0],)).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO quran_sections
                (juz_number, section_name, start_reference, end_reference)
                VALUES (?, ?, ?, ?)
            """, item)

    admin_teacher = conn.execute("SELECT id FROM teachers WHERE username = ?", ("admin",)).fetchone()
    if not admin_teacher:
        conn.execute("""
            INSERT INTO teachers (name, username, password)
            VALUES (?, ?, ?)
        """, ("Администратор", "admin", "1234"))

    conn.commit()
    conn.close()

# =========================
# LOGIN & LOGOUT
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == "admin" and password == "1234":
            session.clear()
            session["user_id"] = 0
            session["username"] = "admin"
            session["role"] = "admin"
            return redirect(url_for("admin"))

        conn = get_db()
        parent = conn.execute("SELECT * FROM parents WHERE username = ? AND password = ?", (username, password)).fetchone()
        if parent:
            session.clear()
            session["user_id"] = parent["id"]
            session["student_id"] = parent["student_id"]
            session["username"] = parent["username"]
            session["role"] = "parent"
            conn.close()
            return redirect(url_for("parent"))

        teacher = conn.execute("SELECT * FROM teachers WHERE username = ? AND password = ?", (username, password)).fetchone()
        if teacher:
            session.clear()
            session["user_id"] = teacher["id"]
            session["username"] = teacher["username"]
            session["role"] = "teacher"
            conn.close()
            return redirect(url_for("teacher"))

        conn.close()
        return render_template("login.html", error="Логин же сырсөз туура эмес")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# ADMIN
# =========================
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    total_teachers = conn.execute("SELECT COUNT(*) AS count FROM teachers WHERE username != 'admin'").fetchone()["count"]
    total_students = conn.execute("SELECT COUNT(*) AS count FROM students").fetchone()["count"]
    total_parents = conn.execute("SELECT COUNT(*) AS count FROM parents").fetchone()["count"]
    total_courses = conn.execute("SELECT COUNT(*) AS count FROM courses").fetchone()["count"]
    total_subjects = conn.execute("SELECT COUNT(*) AS count FROM subjects").fetchone()["count"]
    total_assignments = conn.execute("SELECT COUNT(*) AS count FROM teacher_assignments").fetchone()["count"]
    total_attendance = conn.execute("SELECT COUNT(*) AS count FROM student_attendance").fetchone()["count"]
    completed_juz = conn.execute("SELECT COUNT(DISTINCT student_id || '-' || juz_number) AS count FROM quran_progress WHERE status = 'Жаттады'").fetchone()["count"]

    present_count = conn.execute("SELECT COUNT(*) AS count FROM student_attendance WHERE attendance = 'Келди'").fetchone()["count"]
    absent_count = conn.execute("SELECT COUNT(*) AS count FROM student_attendance WHERE attendance = 'Келген жок'").fetchone()["count"]
    total_att_records = present_count + absent_count
    attendance_percent = round(present_count / total_att_records * 100, 1) if total_att_records > 0 else 0

    courses = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()
    teachers = conn.execute("SELECT * FROM teachers WHERE username != 'admin' ORDER BY id DESC").fetchall()
    assignments = conn.execute("""
        SELECT ta.id, t.name AS teacher_name, c.name AS course_name, s.name AS subject_name
        FROM teacher_assignments ta
        JOIN teachers t ON ta.teacher_id = t.id
        JOIN courses c ON ta.course_id = c.id
        JOIN subjects s ON ta.subject_id = s.id
        ORDER BY ta.id DESC
    """).fetchall()

    quran_semester_stats = []
    semester_goals = {1: 3, 2: 8, 3: 13, 4: 21, 5: 30, 6: 30}
    for semester in range(1, 7):
        completed = conn.execute("SELECT COUNT(DISTINCT student_id || '-' || juz_number) AS count FROM quran_progress WHERE semester = ? AND status = 'Жаттады'", (semester,)).fetchone()["count"]
        goal = semester_goals[semester]
        percent = round(completed / goal * 100, 1) if goal > 0 else 0
        quran_semester_stats.append({
            "semester": semester,
            "goal": goal,
            "completed": completed,
            "percent": min(percent, 100)
        })

    conn.close()
    return render_template("admin.html", total_teachers=total_teachers, total_students=total_students, total_parents=total_parents, total_courses=total_courses, total_subjects=total_subjects, total_assignments=total_assignments, total_attendance=total_attendance, completed_juz=completed_juz, present_count=present_count, absent_count=absent_count, attendance_percent=attendance_percent, courses=courses, teachers=teachers, assignments=assignments, quran_semester_stats=quran_semester_stats)

# =========================
# ADD STUDENT
# =========================
@app.route("/add-student", methods=["GET", "POST"])
def add_student():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    courses = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        birth_year = request.form.get("birth_year", type=int)
        course_id = request.form.get("course_id", type=int)
        parent_name = request.form.get("parent_name", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not course_id:
            conn.close()
            return render_template("add_student.html", courses=courses, error="Аты жана курсу толтурулушу керек")

        conn.execute("""
            INSERT INTO students (name, birth_year, course_id, parent_name, phone)
            VALUES (?, ?, ?, ?, ?)
        """, (name, birth_year, course_id, parent_name, phone))
        conn.commit()
        conn.close()
        return redirect(url_for("students"))

    conn.close()
    return render_template("add_student.html", courses=courses)

# =========================
# STUDENTS
# =========================
@app.route("/students")
def students():
    if session.get("role") not in ["admin", "teacher"]:
        return redirect(url_for("login"))

    conn = get_db()
    students_list = conn.execute("""
        SELECT st.*, c.name AS course_name
        FROM students st
        JOIN courses c ON st.course_id = c.id
        ORDER BY st.id DESC
    """).fetchall()
    courses = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()
    conn.close()

    return render_template("students.html", students=students_list, courses=courses)

# =========================
# TEACHER
# =========================
@app.route("/teacher")
def teacher():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    teacher_id = session.get("user_id")
    conn = get_db()
    teacher_info = conn.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,)).fetchone()
    assignments = conn.execute("""
        SELECT ta.id, c.name AS course_name, s.name AS subject_name
        FROM teacher_assignments ta
        JOIN courses c ON ta.course_id = c.id
        JOIN subjects s ON ta.subject_id = s.id
        WHERE ta.teacher_id = ?
        ORDER BY ta.id
    """, (teacher_id,)).fetchall()
    conn.close()

    return render_template("teacher.html", teacher=teacher_info, assignments=assignments)



@app.route("/teacher-students/<int:assignment_id>")
def teacher_students(assignment_id):
    if session.get("role") not in ["admin", "teacher"]:
        return redirect(url_for("login"))

    conn = get_db()

    assignment = conn.execute("""
        SELECT
            ta.id,
            ta.teacher_id,
            ta.course_id,
            ta.subject_id,
            t.name AS teacher_name,
            c.name AS course_name,
            s.name AS subject_name
        FROM teacher_assignments ta
        JOIN teachers t ON ta.teacher_id = t.id
        JOIN courses c ON ta.course_id = c.id
        JOIN subjects s ON ta.subject_id = s.id
        WHERE ta.id = ?
    """, (assignment_id,)).fetchone()

    if not assignment:
        conn.close()
        return redirect(url_for("teacher"))

    if session.get("role") == "teacher":
        if assignment["teacher_id"] != session.get("user_id"):
            conn.close()
            return redirect(url_for("teacher"))

    students = conn.execute("""
        SELECT
            st.*,
            c.name AS course_name
        FROM students st
        JOIN courses c ON st.course_id = c.id
        WHERE st.course_id = ?
        ORDER BY st.name
    """, (assignment["course_id"],)).fetchall()

    conn.close()

    return render_template(
        "teacher_students.html",
        assignment=assignment,
        students=students
    )

# =========================
# ADD TEACHER
# =========================
@app.route("/add-teacher", methods=["GET", "POST"])
def add_teacher():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not name or not username or not password:
            return render_template("add_teacher.html", error="Бардык талааларды толтуруңуз")

        conn = get_db()
        try:
            conn.execute("INSERT INTO teachers (name, username, password) VALUES (?, ?, ?)", (name, username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("add_teacher.html", error="Бул логин мурда катталган")

        conn.close()
        return redirect(url_for("admin"))

    return render_template("add_teacher.html")

# =========================
# ASSIGN TEACHER
# =========================
@app.route("/assign-teacher", methods=["GET", "POST"])
def assign_teacher():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    teachers = conn.execute("SELECT * FROM teachers WHERE username != 'admin' ORDER BY name").fetchall()
    courses = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY id").fetchall()

    if request.method == "POST":
        teacher_id = request.form.get("teacher_id", type=int)
        course_id = request.form.get("course_id", type=int)
        subject_id = request.form.get("subject_id", type=int)

        existing = conn.execute("""
            SELECT id FROM teacher_assignments
            WHERE teacher_id = ? AND course_id = ? AND subject_id = ?
        """, (teacher_id, course_id, subject_id)).fetchone()

        if existing:
            conn.close()
            return render_template("assign_teacher.html", teachers=teachers, courses=courses, subjects=subjects, error="Бул сабак мурда бекитилген")

        conn.execute("INSERT INTO teacher_assignments (teacher_id, course_id, subject_id) VALUES (?, ?, ?)", (teacher_id, course_id, subject_id))
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))

    conn.close()
    return render_template("assign_teacher.html", teachers=teachers, courses=courses, subjects=subjects)

# =========================
# EDIT ASSIGNMENT (Өзгөртүлгөн жери: <int:assignment_id>)
# =========================
@app.route("/edit-assignment/<int:assignment_id>", methods=["GET", "POST"])
def edit_assignment(assignment_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    assignment = conn.execute("SELECT * FROM teacher_assignments WHERE id = ?", (assignment_id,)).fetchone()

    if not assignment:
        conn.close()
        return redirect(url_for("admin"))

    teachers = conn.execute("SELECT * FROM teachers WHERE username != 'admin' ORDER BY name").fetchall()
    courses = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY id").fetchall()

    if request.method == "POST":
        teacher_id = request.form.get("teacher_id", type=int)
        course_id = request.form.get("course_id", type=int)
        subject_id = request.form.get("subject_id", type=int)

        conn.execute("""
            UPDATE teacher_assignments
            SET teacher_id = ?, course_id = ?, subject_id = ?
            WHERE id = ?
        """, (teacher_id, course_id, subject_id, assignment_id))
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))

    conn.close()
    return render_template("edit_assignment.html", assignment=assignment, teachers=teachers, courses=courses, subjects=subjects)

# =========================
# DELETE ASSIGNMENT (Өзгөртүлгөн жери: <int:assignment_id>)
# =========================
@app.route("/delete-assignment/<int:assignment_id>")
def delete_assignment(assignment_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM student_attendance WHERE assignment_id = ?", (assignment_id,))
    conn.execute("DELETE FROM lessons WHERE assignment_id = ?", (assignment_id,))
    conn.execute("DELETE FROM teacher_assignments WHERE id = ?", (assignment_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin"))

# =========================
# QURAN SECTIONS
# =========================
@app.route("/quran-sections")
def quran_sections():
    if session.get("role") not in ["admin", "teacher"]:
        return redirect(url_for("login"))

    conn = get_db()
    sections = conn.execute("SELECT * FROM quran_sections ORDER BY juz_number").fetchall()
    conn.close()

    return render_template("quran_sections.html", sections=sections)

# =========================
# LESSON PAGE (Өзгөртүлгөн жери: <int:assignment_id>)
# =========================
@app.route("/lesson/<int:assignment_id>")
def lesson_page(assignment_id):
    if session.get("role") not in ["admin", "teacher"]:
        return redirect(url_for("login"))

    selected_semester = request.args.get("semester", 1, type=int)
    if selected_semester < 1 or selected_semester > 6:
        selected_semester = 1

    conn = get_db()
    assignment = conn.execute("""
        SELECT ta.*, t.name AS teacher_name, c.name AS course_name, s.name AS subject_name
        FROM teacher_assignments ta
        JOIN teachers t ON ta.teacher_id = t.id
        JOIN courses c ON ta.course_id = c.id
        JOIN subjects s ON ta.subject_id = s.id
        WHERE ta.id = ?
    """, (assignment_id,)).fetchone()

    if not assignment:
        conn.close()
        return redirect(url_for("admin"))

    lessons = conn.execute("""
        SELECT * FROM lessons
        WHERE assignment_id = ? AND semester = ?
        ORDER BY lesson_number
    """, (assignment_id, selected_semester)).fetchall()

    conn.close()
    return render_template("lesson.html", assignment=assignment, lessons=lessons, selected_semester=selected_semester)

# =========================
# PARENT CABINET
# =========================
@app.route("/parent")
def parent():
    if session.get("role") != "parent":
        return redirect(url_for("login"))

    student_id = session.get("student_id")
    conn = get_db()
    student = conn.execute("""
        SELECT st.*, c.name AS course_name
        FROM students st
        JOIN courses c ON st.course_id = c.id
        WHERE st.id = ?
    """, (student_id,)).fetchone()

    quran_progress = conn.execute("""
        SELECT qp.*, t.name AS teacher_name
        FROM quran_progress qp
        LEFT JOIN teachers t ON qp.teacher_id = t.id
        WHERE qp.student_id = ?
        ORDER BY qp.semester, qp.juz_number
    """, (student_id,)).fetchall()

    conn.close()
    return render_template("parent.html", student=student, quran_progress=quran_progress)

# =========================
# PARENTS LIST
# =========================
@app.route("/parents")
def parents():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    parents_list = conn.execute("""
        SELECT p.*, st.name AS student_name
        FROM parents p
        LEFT JOIN students st ON p.student_id = st.id
        ORDER BY p.id DESC
    """).fetchall()
    conn.close()

    return render_template("parents.html", parents=parents_list)

# =========================
# LAUNCH
# =========================

# =========================
# EDIT STUDENT (Студентти оңдоо)
# =========================
@app.route("/edit-student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if session.get("role") not in ["admin", "teacher"]:
        return redirect(url_for("login"))

    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()

    if not student:
        conn.close()
        return redirect(url_for("students"))

    courses = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        birth_year = request.form.get("birth_year", type=int)
        course_id = request.form.get("course_id", type=int)
        parent_name = request.form.get("parent_name", "").strip()
        phone = request.form.get("phone", "").strip()

        conn.execute("""
            UPDATE students
            SET name = ?, birth_year = ?, course_id = ?, parent_name = ?, phone = ?
            WHERE id = ?
        """, (name, birth_year, course_id, parent_name, phone, student_id))

        conn.commit()
        conn.close()
        return redirect(url_for("students"))

    conn.close()
    return render_template("edit_student.html", student=student, courses=courses)

# =========================
# EDIT STUDENT
# =========================


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
