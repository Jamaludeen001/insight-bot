// static/js/app.js
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const PAGE_META = {
    raise:    { title: "Raise a Damage Report", subtitle: "Report damage detected on arrival" },
    track:    { title: "Track Report",          subtitle: "Look up an existing damage report" },
    warranty: { title: "Claim Warranty",        subtitle: "File a claim for post-purchase damage" },
  };

  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => (p.hidden = true));
      btn.classList.add("active");

      const tab = btn.dataset.tab;
      $("panel-" + tab).hidden = false;
      $("page-title").textContent = PAGE_META[tab].title;
      $("page-subtitle").textContent = PAGE_META[tab].subtitle;
    });
  });

  function wireFileInput(inputId, labelId) {
    $(inputId).addEventListener("change", (e) => {
      const file = e.target.files[0];
      $(labelId).textContent = file ? `📎 ${file.name}` : "";
    });
  }
  wireFileInput("raise-image", "raise-file-name");
  wireFileInput("warranty-image", "warranty-file-name");

  function setLoading(btn, on) {
    btn.disabled = on;
    btn.classList.toggle("loading", on);
  }

  function renderError(el, message) {
    el.className = "result-card err show";
    el.innerHTML = `
      <div class="result-head">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>Request failed</span>
      </div>
      <div class="result-body">
        <div class="result-row"><span class="label">Reason</span><span class="value">${escapeHtml(message)}</span></div>
      </div>`;
  }

  function renderReportSuccess(el, data) {
    el.className = "result-card ok show";

    // Heading changes depending on whether this was an insert or an update
    const heading = data.updated
        ? "Report updated"
        : "Report submitted successfully";

    const img = data.damaged_image_url
        ? `<div class="result-row"><span class="label">Damaged Image</span>
             <span class="value"><a href="${data.damaged_image_url}" target="_blank">view</a></span></div>` : "";

    el.innerHTML = `
      <div class="result-head">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 6 9 17l-5-5"/>
        </svg>
        <span>${heading}</span>
      </div>
      <div class="result-body">
        <div class="result-row"><span class="label">Tracking ID</span><span class="value highlight">${data.tracking_id}</span></div>
        <div class="result-row"><span class="label">Sentiment</span><span class="value">${data.sentiment} (${data.score.toFixed(2)})</span></div>
        <div class="result-row"><span class="label">Damage Severity</span><span class="value">${data.damage_severity}</span></div>
        <div class="result-row"><span class="label">Affected Area</span><span class="value">${data.affected_area_percentage}</span></div>
        <div class="result-row"><span class="label">Recommendation</span><span class="value">${escapeHtml(data.recommendation || '—')}</span></div>
        ${img}
      </div>`;
}
  function renderNotProceed(el, data) {
    el.className = "result-card err show";
    el.innerHTML = `
      <div class="result-head">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        </svg>
        <span>Not eligible for damage report</span>
      </div>
      <div class="result-body">
        <div class="result-row"><span class="label">Reason</span><span class="value">${escapeHtml(data.message)}</span></div>
        <div class="result-row"><span class="label">Sentiment</span><span class="value">${data.sentiment} (${data.score.toFixed(2)})</span></div>
      </div>`;
  }

  function renderReportTrack(el, data) {
    el.className = "result-card ok show";
    const img = data.damaged_image_url
      ? `<div class="result-row"><span class="label">Damaged Image</span>
           <span class="value"><a href="${data.damaged_image_url}" target="_blank">view</a></span></div>` : "";
    el.innerHTML = `
      <div class="result-head">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
        </svg>
        <span>Report Details</span>
      </div>
      <div class="result-body">
        <div class="result-row"><span class="label">Tracking ID</span><span class="value">${data.tracking_id}</span></div>
        <div class="result-row"><span class="label">Order ID</span><span class="value">${data.order_id}</span></div>
        <div class="result-row"><span class="label">Status</span><span class="value"><span class="badge open">${data.status}</span></span></div>
        <div class="result-row"><span class="label">Sentiment</span><span class="value">${data.sentiment} (${data.sentiment_score})</span></div>
        <div class="result-row"><span class="label">Severity</span><span class="value">${data.damage_severity}</span></div>
        <div class="result-row"><span class="label">Created</span><span class="value">${formatDate(data.created_at)}</span></div>
        ${img}
      </div>`;
  }

  function renderClaimSuccess(el, data) {
    el.className = "result-card ok show";
    const img = data.damaged_image_url
      ? `<div class="result-row"><span class="label">Damaged Image</span>
           <span class="value"><a href="${data.damaged_image_url}" target="_blank">view</a></span></div>` : "";
    el.innerHTML = `
      <div class="result-head">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 6 9 17l-5-5"/>
        </svg>
        <span>Warranty claim submitted</span>
      </div>
      <div class="result-body">
        <div class="result-row"><span class="label">Claim ID</span><span class="value highlight">${data.claim_id}</span></div>
        <div class="result-row"><span class="label">Status</span><span class="value"><span class="badge success">${data.status}</span></span></div>
        <div class="result-row"><span class="label">Damage Severity</span><span class="value">${data.damage_severity}</span></div>
        ${img}
      </div>`;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function formatDate(iso) {
    try { return new Date(iso).toLocaleString(); } catch { return iso; }
  }

  async function postForm(url, formData) {
    const res = await fetch(url, { method: "POST", body: formData });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
    return data;
  }

  $("raise-submit").addEventListener("click", async () => {
    const btn = $("raise-submit");
    const out = $("raise-result");
    const order = $("raise-order").value.trim();
    const feedback = $("raise-feedback").value.trim();
    const file = $("raise-image").files[0];

    if (!order || !feedback || !file) {
      return renderError(out, "Order ID, feedback, and image are all required.");
    }

    const fd = new FormData();
    fd.append("order_id", order);
    fd.append("feedback", feedback);
    fd.append("image", file);

    setLoading(btn, true);
    try {
      const data = await postForm("/api/damage-report", fd);
      if (!data.proceed) renderNotProceed(out, data);
      else renderReportSuccess(out, data);
    } catch (e) {
      renderError(out, e.message);
    } finally {
      setLoading(btn, false);
    }
  });

  $("track-submit").addEventListener("click", async () => {
    const btn = $("track-submit");
    const out = $("track-result");
    const id = $("track-id").value.trim();

    if (!id) return renderError(out, "Tracking ID is required.");

    setLoading(btn, true);
    try {
      const res = await fetch("/api/reports/" + encodeURIComponent(id));
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Not found");
      renderReportTrack(out, data);
    } catch (e) {
      renderError(out, e.message);
    } finally {
      setLoading(btn, false);
    }
  });

  $("warranty-submit").addEventListener("click", async () => {
    const btn = $("warranty-submit");
    const out = $("warranty-result");
    const order = $("warranty-order").value.trim();
    const reason = $("warranty-reason").value.trim();
    const file = $("warranty-image").files[0];

    if (!order || !reason || !file) {
      return renderError(out, "Order ID, image, and description are all required.");
    }

    const fd = new FormData();
    fd.append("order_id", order);
    fd.append("reason", reason);
    fd.append("image", file);

    setLoading(btn, true);
    try {
      const data = await postForm("/api/warranty-claim", fd);
      renderClaimSuccess(out, data);
    } catch (e) {
      renderError(out, e.message);
    } finally {
      setLoading(btn, false);
    }
  });
})();