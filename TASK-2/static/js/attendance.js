document.addEventListener("DOMContentLoaded", () => {
  const dateInput = document.getElementById("attendance-date");
  if (!dateInput.value) {
    dateInput.value = new Date().toISOString().split("T")[0];
  }
});