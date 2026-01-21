function initStudentCourses() {
  fetch("/api/my-courses")
    .then(res => res.json())
    .then(courses => {
      const list = document.getElementById("courseList");
      list.innerHTML = "";

      if (courses.length === 0) {
        list.innerHTML = "<p>No courses assigned</p>";
        return;
      }

      courses.forEach(c => {
        list.innerHTML += `
          <div class="course-card">
            <b>${c.id}</b> - ${c.name}
            <div class="muted">Semester ${c.semester}</div>
          </div>
        `;
      });
    });
}
