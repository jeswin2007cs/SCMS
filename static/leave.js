function initLeavePage() {

  const openBtn = document.getElementById("openLeaveBtn");
  const cancelBtn = document.getElementById("cancelLeaveBtn");
  const applyBtn = document.getElementById("applyLeaveBtn");
  const form = document.getElementById("leaveForm");
  const historyDiv = document.getElementById("history");

  if (!openBtn || !applyBtn || !form || !historyDiv) {
    console.error("Leave page DOM missing");
    return;
  }

  openBtn.onclick = () => form.classList.remove("hidden");
  cancelBtn.onclick = closeForm;
  applyBtn.onclick = submitLeave;

  function closeForm() {
    form.classList.add("hidden");
    resetForm();
  }

  function resetForm() {
    document.getElementById("type").value = "";
    document.getElementById("from").value = "";
    document.getElementById("to").value = "";
    document.getElementById("reason").value = "";
  }

  function submitLeave() {
    const type = document.getElementById("type").value;
    const from = document.getElementById("from").value;
    const to = document.getElementById("to").value;
    const reason = document.getElementById("reason").value;

    if (!type || !from || !to || !reason) {
      alert("Fill all fields");
      return;
    }

    fetch("/api/leave", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, from, to, reason })
    })
      .then(res => res.json())
      .then(() => {
        closeForm();
        loadHistory();
      });
  }

  function loadHistory() {
    fetch("/api/leaves")
      .then(res => res.json())
      .then(data => {
        historyDiv.innerHTML = "";

        if (!data.length) {
          historyDiv.innerHTML = "<p>No leave applied</p>";
          return;
        }

        data.forEach(l => {
          historyDiv.innerHTML += `
            <div class="leave-item">
              <div>
                <b>${l.from} to ${l.to}</b>
                <div>${l.reason}</div>
              </div>
              <span class="status ${l.status}">
                ${l.status}
              </span>
            </div>
          `;
        });
      });
  }

  // 🔥 AUTO LOAD HISTORY
  loadHistory();
}
