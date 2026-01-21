from flask import Flask, render_template, request, redirect, session, jsonify, send_from_directory
import json, os, time

# ==================================================
# JSON STORAGE (SINGLETON)
# ==================================================
class JSONStorage:
    _instance = None

    def __new__(cls, base_dir):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.base_dir = base_dir
        return cls._instance

    def load(self, filename, default):
        path = os.path.join(self.base_dir, filename)
        if not os.path.exists(path):
            return default
        with open(path, "r") as f:
            return json.load(f)

    def save(self, filename, data):
        with open(os.path.join(self.base_dir, filename), "w") as f:
            json.dump(data, f, indent=2)


# ==================================================
# AUTH SERVICE (SINGLETON)
# ==================================================
class AuthService:
    _instance = None

    def __new__(cls, storage):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.storage = storage
        return cls._instance

    def authenticate_student(self, email, password):
        students = self.storage.load("students.json", {"students": []})["students"]
        return next(
            (s for s in students if s["gmail"] == email and s["password"] == password),
            None
        )

    def authenticate_admin(self, email, password):
        admins = self.storage.load("admins.json", {"admins": []})["admins"]
        return next(
            (a for a in admins if a["email"] == email and a["password"] == password),
            None
        )


# ==================================================
# MAIN APPLICATION (SINGLETON)
# ==================================================
class SCMSApp:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.app = Flask(__name__)
        self.app.secret_key = "secret123"

        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.storage = JSONStorage(self.BASE_DIR)
        self.auth = AuthService(self.storage)

        self.register_routes()

    # ------------------------------------------------
    # ROUTES
    # ------------------------------------------------
    def register_routes(self):

        # ---------- INDEX ----------
        @self.app.route("/")
        def index():
            if "admin" in session:
                return redirect("/admin/dashboard")
            if "student" in session:
                return redirect("/dashboard")
            return redirect("/login")

        # ---------- STUDENT LOGIN ----------
        @self.app.route("/login", methods=["GET", "POST"])
        def login():
            if request.method == "GET":
                return render_template("login.html")

            user = self.auth.authenticate_student(
                request.form.get("email"),
                request.form.get("password")
            )

            if not user:
                return render_template("login.html", error="Invalid Gmail or Password")

            session.clear()
            session["student"] = user
            return redirect("/dashboard")

        # ---------- ADMIN LOGIN ----------
        @self.app.route("/admin/login", methods=["GET", "POST"])
        def admin_login():
            if request.method == "GET":
                return render_template("admin_login.html")

            admin = self.auth.authenticate_admin(
                request.form.get("email"),
                request.form.get("password")
            )

            if not admin:
                return render_template("admin_login.html", error="Invalid Admin Credentials")

            session.clear()
            session["admin"] = admin
            return redirect("/admin/dashboard")

        # ---------- STUDENT DASHBOARD ----------
        @self.app.route("/dashboard")
        def dashboard():
            if "student" not in session:
                return redirect("/login")
            return render_template("dashboard.html", student=session["student"])

        # ---------- ADMIN DASHBOARD ----------
                # ---------- ADMIN DASHBOARD ----------
        @self.app.route("/admin/dashboard")
        def admin_dashboard():
            admin = session.get("admin")
            if not admin:
                return redirect("/admin/login")

            students_data = self.storage.load("students.json", {"students": []})
            courses_data = self.storage.load("courses.json", {"courses": []})
            leaves_data = self.storage.load("leaves.json", [])
            attendance_data = self.storage.load("attendance.json", {"records": []})

            students = students_data["students"]
            courses = courses_data["courses"]
            leaves = leaves_data
            attendance = attendance_data["records"]

            return render_template(
                "admin_dashboard.html",
                admin=admin,

                # COUNTS (for cards)
                stats={
                    "students": len(students),
                    "courses": len(courses),
                    "leaves": len(leaves),
                },

                # FULL DATA (for tables)
                students=students,
                courses=courses,
                leaves=leaves,
                attendance=attendance
            )

        # ---------- STATIC PHOTOS ----------
        @self.app.route("/photos/<path:filename>")
        def photos(filename):
            return send_from_directory(os.path.join(self.BASE_DIR, "photos"), filename)

        # ---------- STUDENT PAGES ----------
        @self.app.route("/attendance")
        def attendance_page():
            if "student" not in session:
                return redirect("/login")
            return render_template("attendance.html")

        @self.app.route("/leave")
        def leave_page():
            if "student" not in session:
                return redirect("/login")
            return render_template("leave.html")

        @self.app.route("/my-courses")
        def my_courses():
            if "student" not in session:
                return redirect("/login")
            return render_template("my_courses.html")

        # ---------- ADMIN PAGES ----------
        @self.app.route("/admin/courses")
        def admin_courses():
            if "admin" not in session:
                return redirect("/admin/login")
            return render_template("course_admin.html")

        # ---------- ATTENDANCE API ----------
        @self.app.route("/api/attendance")
        def attendance_api():
            student = session.get("student")
            if not student:
                return jsonify({"error": "Unauthorized"}), 401

            courses = self.storage.load("courses.json", {"courses": []})["courses"]
            records = self.storage.load("attendance.json", {"records": []})["records"]

            subjects = []

            for c in courses:
                if c["department"] == student["department"] and str(c["semester"]) == str(student["semester"]):
                    r = next(
                        (x for x in records
                         if x["studentEmail"] == student["gmail"]
                         and x["courseId"] == c["id"]),
                        None
                    )

                    present = r["present"] if r else 0
                    total = r["total"] if r else 0
                    percentage = round((present / total) * 100) if total else 0

                    subjects.append({
                        "code": c["id"],
                        "name": c["name"],
                        "present": present,
                        "total": total,
                        "percentage": percentage
                    })

            return jsonify({
                "student": {
                    "name": student["name"],
                    "department": student["department"],
                    "semester": student["semester"]
                },
                "subjects": subjects
            })

        # ---------- STUDENT COURSES API ----------
        @self.app.route("/api/my-courses")
        def api_my_courses():
            student = session.get("student")
            if not student:
                return jsonify([])

            courses = self.storage.load("courses.json", {"courses": []})["courses"]
            return jsonify([
                c for c in courses
                if c["department"] == student["department"]
                and str(c["semester"]) == str(student["semester"])
            ])

        # ---------- LEAVE ----------
        @self.app.route("/api/leave", methods=["POST"])
        def apply_leave():
            student = session.get("student")
            if not student:
                return jsonify({"error": "Unauthorized"}), 401

            leaves = self.storage.load("leaves.json", [])
            data = request.json

            data.update({
                "id": int(time.time() * 1000),
                "studentEmail": student["gmail"],
                "status": "Pending"
            })

            leaves.insert(0, data)
            self.storage.save("leaves.json", leaves)
            return jsonify({"success": True})

        @self.app.route("/api/leaves")
        def leave_history():
            student = session.get("student")
            if not student:
                return jsonify([])

            leaves = self.storage.load("leaves.json", [])
            return jsonify([l for l in leaves if l["studentEmail"] == student["gmail"]])

        # ---------- LOGOUT ----------
        @self.app.route("/logout")
        def logout():
            session.clear()
            return redirect("/login")

    # ---------- RUN ----------
    def run(self):
        self.app.run(debug=True)


# ==================================================
# APPLICATION ENTRY POINT
# ==================================================
if __name__ == "__main__":
    SCMSApp().run()
