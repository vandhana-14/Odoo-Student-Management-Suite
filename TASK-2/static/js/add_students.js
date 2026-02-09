document.addEventListener("DOMContentLoaded", function () {

  const daySelect = document.getElementById("day");
  const monthSelect = document.getElementById("month");
  const yearSelect = document.getElementById("year");

  // Safety check
  if (!daySelect || !monthSelect || !yearSelect) {
    console.error("DOB select elements not found");
    return;
  }

  // ===== Months =====
  const months = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
  ];

  months.forEach((month, index) => {
    const option = document.createElement("option");
    option.value = index + 1;      // 1–12
    option.textContent = month;
    monthSelect.appendChild(option);
  });

  // ===== Years (1950 → current year) =====
  const currentYear = new Date().getFullYear();
  for (let y = currentYear; y >= 1950; y--) {
    const option = document.createElement("option");
    option.value = y;
    option.textContent = y;
    yearSelect.appendChild(option);
  }

  // ===== Update days based on month & year =====
  function updateDays() {
    daySelect.innerHTML = '<option value="">Day</option>';

    const month = parseInt(monthSelect.value);
    const year = parseInt(yearSelect.value);

    if (!month || !year) return;

    // Correct days in month
    const daysInMonth = new Date(year, month, 0).getDate();

    for (let d = 1; d <= daysInMonth; d++) {
      const option = document.createElement("option");
      option.value = d;
      option.textContent = d;
      daySelect.appendChild(option);
    }
  }

  monthSelect.addEventListener("change", updateDays);
  yearSelect.addEventListener("change", updateDays);

});

document.addEventListener("DOMContentLoaded", () => {
  const popup = document.getElementById("flash-popup");
  if (popup) {
    setTimeout(() => {
      popup.style.opacity = "0";
      setTimeout(() => popup.remove(), 500);
    }, 3000);
  }
});

document.getElementById("addStudentForm").addEventListener("submit", function (e) {
  let valid = true;

  // Clear old errors
  document.querySelectorAll(".error").forEach(el => el.textContent = "");

  const name = document.getElementById("name").value.trim();
  const studentId = document.getElementById("student_id").value.trim();
  const email = document.getElementById("email").value.trim();
  const phone = document.getElementById("phone").value.trim();
  const course = document.getElementById("course").value;
  const file = document.getElementById("document").files[0];

  const year = document.getElementById("year").value;
  const month = document.getElementById("month").value;
  const day = document.getElementById("day").value;

  // ---- NAME ----
  if (!/^[A-Za-z ]{3,}$/.test(name)) {
    showError("name", "Enter a valid full name (min 3 letters)");
    valid = false;
  }

  // ---- DOB ----
  if (!year || !month || !day) {
    showError("day", "Please select complete Date of Birth");
    valid = false;
  }

  // ---- STUDENT ID ----
  if (!/^[A-Za-z0-9_-]{4,}$/.test(studentId)) {
    showError("student_id", "Invalid Student ID format");
    valid = false;
  }

  // ---- EMAIL ----
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    showError("email", "Invalid email address");
    valid = false;
  }

  // ---- PHONE (optional but validated) ----
  if (phone && !/^[0-9]{10}$/.test(phone)) {
    showError("phone", "Phone must be 10 digits");
    valid = false;
  }

  // ---- COURSE ----
  if (!course) {
    showError("course", "Please select a course");
    valid = false;
  }

  // ---- RESUME FILE ----
  if (file) {
    const allowed = ["pdf", "doc", "docx"];
    const ext = file.name.split(".").pop().toLowerCase();
    if (!allowed.includes(ext)) {
      showError("document", "Resume must be PDF/DOC/DOCX");
      valid = false;
    }
  }

  if (!valid) e.preventDefault();
});

// Helper
function showError(inputId, message) {
  const input = document.getElementById(inputId);
  input.closest(".form-row").querySelector(".error").textContent = message;
}
