/* ================= SELECT ALL ================= */
const selectAll = document.getElementById("select-all");
const selectedCount = document.getElementById("selected-count");

function updateSelectedCount() {
  const count = document.querySelectorAll(".row-check:checked").length;
  selectedCount.textContent = `${count} selected`;
}

if (selectAll) {
  selectAll.addEventListener("change", function () {
    document.querySelectorAll(".row-check").forEach(cb => {
      cb.checked = selectAll.checked;
    });
    updateSelectedCount();
  });
}

document.addEventListener("change", function (e) {
  if (e.target.classList.contains("row-check")) {
    const all = document.querySelectorAll(".row-check");
    const checked = document.querySelectorAll(".row-check:checked");
    if (selectAll) selectAll.checked = all.length === checked.length;
    updateSelectedCount();
  }
});

/* ================= TOGGLE SINGLE (FIXED) ================= */
function toggleStatus(id, el) {
  el.disabled = true;

  fetch(`/view_students/${id}/toggle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      // 🔑 HARD reload so Flask re-evaluates permissions
      window.location.reload(true);
    } else {
      alert("Toggle failed");
      el.checked = !el.checked;
    }
  })
  .catch(() => {
    alert("Server error");
    el.checked = !el.checked;
  })
  .finally(() => {
    el.disabled = false;
  });
}

/* ================= BULK ENABLE / DISABLE ================= */
function bulkUpdate(status) {
  const ids = Array.from(
    document.querySelectorAll(".row-check:checked")
  ).map(cb => cb.value);

  if (!ids.length) {
    alert("Please select at least one student");
    return;
  }

  fetch("/students/bulk-toggle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids, status })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.location.reload(true);
    } else {
      alert("Bulk update failed");
    }
  });
}

/* ================= BULK DELETE ================= */
function bulkDelete() {
  const ids = Array.from(
    document.querySelectorAll(".row-check:checked")
  ).map(cb => cb.value);

  if (!ids.length) {
    alert("Please select at least one student");
    return;
  }

  if (!confirm("Are you sure you want to delete selected students?")) return;

  fetch("/students/bulk-delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.location.reload(true);
    } else {
      alert("Delete failed (active students cannot be deleted)");
    }
  });
}

/* ================= EDIT MODAL (SINGLE VERSION) ================= */
function openEditModal(btn) {
  document.getElementById("edit-id").value = btn.dataset.id;
  document.getElementById("edit-name").value = btn.dataset.name;
  document.getElementById("edit-student-id").value = btn.dataset.studentId;
  document.getElementById("edit-email").value = btn.dataset.email;
  document.getElementById("edit-phone").value = btn.dataset.phone;
  document.getElementById("edit-address").value = btn.dataset.address;
  document.getElementById("edit-course").value = btn.dataset.course;

  document.getElementById("editModal").style.display = "flex";
}

function closeEditModal() {
  document.getElementById("editModal").style.display = "none";
}

function saveEdit() {
  const id = document.getElementById("edit-id").value;

  fetch(`/students/${id}/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: document.getElementById("edit-name").value,
      email: document.getElementById("edit-email").value,
      phone: document.getElementById("edit-phone").value,
      address: document.getElementById("edit-address").value,
      course: document.getElementById("edit-course").value
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.location.reload(true);
    } else {
      alert("Update failed");
    }
  });
}
