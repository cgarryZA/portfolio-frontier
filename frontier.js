// frontier.js — Portfolio Efficient Frontier Dashboard

document.addEventListener("DOMContentLoaded", async () => {
  const data = await fetch("./data/precomputed/frontier.json")
    .then(r => r.ok ? r.json() : null)
    .catch(() => null);

  if (!data) {
    document.querySelector(".container").innerHTML =
      `<div class="card"><p style="opacity:.7;">No precomputed data found. Run: python src/precompute_frontier.py</p></div>`;
    return;
  }

  const TYPE_COLORS = {
    rifle: "#ef4444",
    pistol: "#f59e0b",
    smg: "#22c55e",
    shotgun: "#a78bfa",
    mg: "#ec4899",
    knife: "#38bdf8",
    glove: "#f97316",
    other: "#6b7280",
  };

  // ─── Helpers ───
  function sizeCanvas(canvas) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const w = Math.round(rect.width);
    const h = Math.round(rect.height);
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, W: w, H: h };
  }

  function num(v) {
    if (!Number.isFinite(v)) return String(v);
    if (Math.abs(v) >= 100) return v.toFixed(0);
    if (Math.abs(v) >= 1) return v.toFixed(2);
    return v.toFixed(4);
  }

  function pct(v) { return (v * 100).toFixed(1) + "%"; }

  // ─── Frontier Chart ───
  const frontierCanvas = document.getElementById("frontier-canvas");
  if (frontierCanvas && data.frontier) {
    requestAnimationFrame(() => {
      const { ctx, W, H } = sizeCanvas(frontierCanvas);
      const points = data.frontier.long_only || [];
      const special = data.special_portfolios || {};

      if (!points.length) {
        ctx.fillStyle = "rgba(255,255,255,.5)";
        ctx.font = "14px system-ui";
        ctx.fillText("No frontier data", 20, 30);
        return;
      }

      const PAD = { top: 20, right: 20, bottom: 40, left: 70 };
      const pw = W - PAD.left - PAD.right;
      const ph = H - PAD.top - PAD.bottom;

      // Gather all points for scale
      const allPts = [...points.map(p => [p.risk, p.ret])];
      Object.values(special).forEach(p => allPts.push([p.risk, p.ret]));

      let xmin = Math.min(...allPts.map(p => p[0]));
      let xmax = Math.max(...allPts.map(p => p[0]));
      let ymin = Math.min(...allPts.map(p => p[1]));
      let ymax = Math.max(...allPts.map(p => p[1]));
      const xpad = (xmax - xmin) * 0.1 || 0.01;
      const ypad = (ymax - ymin) * 0.1 || 0.001;
      xmin -= xpad; xmax += xpad; ymin -= ypad; ymax += ypad;

      function tx(x) { return PAD.left + ((x - xmin) / (xmax - xmin)) * pw; }
      function ty(y) { return PAD.top + (1 - (y - ymin) / (ymax - ymin)) * ph; }

      // Background
      ctx.fillStyle = "#0b0f14";
      ctx.fillRect(0, 0, W, H);

      // Grid
      ctx.strokeStyle = "rgba(255,255,255,.07)";
      ctx.fillStyle = "rgba(255,255,255,.6)";
      ctx.font = "11px system-ui";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      for (let i = 0; i <= 5; i++) {
        const yv = ymin + (i * (ymax - ymin)) / 5;
        const py = ty(yv);
        ctx.beginPath(); ctx.moveTo(PAD.left, py); ctx.lineTo(W - PAD.right, py); ctx.stroke();
        ctx.fillText(pct(yv), PAD.left - 6, py);
      }
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      for (let i = 0; i <= 5; i++) {
        const xv = xmin + (i * (xmax - xmin)) / 5;
        const px = tx(xv);
        ctx.beginPath(); ctx.moveTo(px, PAD.top); ctx.lineTo(px, H - PAD.bottom); ctx.stroke();
        ctx.fillText(pct(xv), px, H - PAD.bottom + 6);
      }

      // Axes labels
      ctx.fillStyle = "rgba(255,255,255,.5)";
      ctx.font = "12px system-ui";
      ctx.textAlign = "center";
      ctx.fillText("Annualized Volatility", W / 2, H - 6);
      ctx.save();
      ctx.translate(14, H / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText("Annualized Return", 0, 0);
      ctx.restore();

      // Frontier curve
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      points.forEach((p, i) => {
        const px = tx(p.risk);
        const py = ty(p.ret);
        if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.stroke();

      // Special portfolio markers
      const markerColors = {
        equal_weight: "#6b7280",
        min_variance: "#22c55e",
        max_sharpe: "#f59e0b",
        risk_parity: "#a78bfa",
      };
      const markerLabels = {
        equal_weight: "EW",
        min_variance: "MinVar",
        max_sharpe: "MaxSR",
        risk_parity: "RiskPar",
      };
      Object.entries(special).forEach(([key, port]) => {
        const px = tx(port.risk);
        const py = ty(port.ret);
        const color = markerColors[key] || "#fff";
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(px, py, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.fillStyle = "#fff";
        ctx.font = "bold 11px system-ui";
        ctx.textAlign = "left";
        ctx.textBaseline = "bottom";
        ctx.fillText(markerLabels[key] || key, px + 10, py - 4);
      });
    });
  }

  // ─── Scatter Chart ───
  const scatterCanvas = document.getElementById("scatter-canvas");
  if (scatterCanvas && data.items) {
    // Build legend
    const legendDiv = document.getElementById("scatter-legend");
    if (legendDiv) {
      Object.entries(TYPE_COLORS).forEach(([type, color]) => {
        const count = Object.values(data.items).filter(i => i.type === type).length;
        if (count === 0) return;
        const span = document.createElement("span");
        span.style.cssText = `display:inline-flex;align-items:center;gap:4px;margin-right:12px;font-size:12px;`;
        span.innerHTML = `<span style="width:10px;height:10px;border-radius:50%;background:${color};display:inline-block;"></span>${type} (${count})`;
        legendDiv.appendChild(span);
      });
    }

    requestAnimationFrame(() => {
      const { ctx, W, H } = sizeCanvas(scatterCanvas);
      const items = Object.entries(data.items);

      const PAD = { top: 20, right: 20, bottom: 40, left: 70 };
      const pw = W - PAD.left - PAD.right;
      const ph = H - PAD.top - PAD.bottom;

      // Filter out extreme outliers for better visualization
      const vols = items.map(([, d]) => d.vol).filter(v => v > 0);
      const rets = items.map(([, d]) => d.mean_ret);
      const volP95 = vols.sort((a, b) => a - b)[Math.floor(vols.length * 0.95)] || 2;
      const retP95 = rets.sort((a, b) => a - b)[Math.floor(rets.length * 0.95)] || 1;
      const retP05 = rets[Math.floor(rets.length * 0.05)] || -1;

      const xmax = volP95 * 1.1;
      const xmin = 0;
      const ymax = retP95 * 1.1;
      const ymin = Math.min(retP05 * 1.1, -0.1);

      function tx(x) { return PAD.left + (x / xmax) * pw; }
      function ty(y) { return PAD.top + (1 - (y - ymin) / (ymax - ymin)) * ph; }

      // Background
      ctx.fillStyle = "#0b0f14";
      ctx.fillRect(0, 0, W, H);

      // Grid
      ctx.strokeStyle = "rgba(255,255,255,.07)";
      ctx.fillStyle = "rgba(255,255,255,.6)";
      ctx.font = "11px system-ui";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      for (let i = 0; i <= 5; i++) {
        const yv = ymin + (i * (ymax - ymin)) / 5;
        const py = ty(yv);
        ctx.beginPath(); ctx.moveTo(PAD.left, py); ctx.lineTo(W - PAD.right, py); ctx.stroke();
        ctx.fillText(pct(yv), PAD.left - 6, py);
      }
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      for (let i = 0; i <= 5; i++) {
        const xv = (i * xmax) / 5;
        const px = tx(xv);
        ctx.beginPath(); ctx.moveTo(px, PAD.top); ctx.lineTo(px, H - PAD.bottom); ctx.stroke();
        ctx.fillText(pct(xv), px, H - PAD.bottom + 6);
      }

      // Zero line
      if (ymin < 0 && ymax > 0) {
        ctx.strokeStyle = "rgba(255,255,255,.2)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(PAD.left, ty(0));
        ctx.lineTo(W - PAD.right, ty(0));
        ctx.stroke();
      }

      // Plot items
      ctx.globalAlpha = 0.6;
      items.forEach(([name, d]) => {
        if (d.vol > xmax || d.mean_ret > ymax || d.mean_ret < ymin) return;
        const px = tx(d.vol);
        const py = ty(d.mean_ret);
        ctx.fillStyle = TYPE_COLORS[d.type] || TYPE_COLORS.other;
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.globalAlpha = 1.0;

      // Axes labels
      ctx.fillStyle = "rgba(255,255,255,.5)";
      ctx.font = "12px system-ui";
      ctx.textAlign = "center";
      ctx.fillText("Annualized Volatility", W / 2, H - 6);
      ctx.save();
      ctx.translate(14, H / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText("Annualized Return", 0, 0);
      ctx.restore();
    });
  }

  // ─── Special Portfolios ───
  const specialDiv = document.getElementById("special-portfolios");
  if (specialDiv && data.special_portfolios) {
    const labels = {
      equal_weight: "Equal Weight",
      min_variance: "Minimum Variance",
      max_sharpe: "Maximum Sharpe",
      risk_parity: "Risk Parity",
    };

    let html = `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;">`;
    Object.entries(data.special_portfolios).forEach(([key, port]) => {
      html += `<div style="padding:12px;border:1px solid var(--grid);border-radius:8px;background:rgba(255,255,255,.02);">
        <div style="font-weight:600;margin-bottom:6px;">${labels[key] || key}</div>
        <div style="font-size:13px;color:var(--muted);">
          Return: ${pct(port.ret)} &nbsp; Risk: ${pct(port.risk)}
          ${port.sharpe ? ` &nbsp; Sharpe: ${port.sharpe}` : ""}
        </div>
        ${port.top_holdings ? `<div style="margin-top:6px;font-size:12px;">
          <div style="opacity:.7;margin-bottom:3px;">Top Holdings:</div>
          ${Object.entries(port.top_holdings).slice(0, 5).map(([name, w]) =>
            `<div style="display:flex;justify-content:space-between;"><span>${name}</span><span>${pct(w)}</span></div>`
          ).join("")}
        </div>` : ""}
      </div>`;
    });
    html += `</div>`;
    specialDiv.innerHTML = html;
  }

  // ─── Sector Correlation ───
  const corrDiv = document.getElementById("sector-corr");
  if (corrDiv && data.correlation) {
    const sa = data.correlation.sector_avg || {};
    let html = `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;">`;
    Object.entries(sa).sort((a, b) => b[1] - a[1]).forEach(([pair, corr]) => {
      const color = corr > 0.3 ? "rgba(239,68,68,.3)" : corr > 0.1 ? "rgba(245,158,11,.2)" : "rgba(34,197,94,.2)";
      html += `<div style="padding:8px;border-radius:6px;background:${color};font-size:13px;">
        <div style="font-weight:600;">${pair}</div>
        <div>${corr.toFixed(3)}</div>
      </div>`;
    });
    html += `</div>`;

    // Top/bottom correlated pairs
    if (data.correlation.top_correlated) {
      html += `<h3 style="margin-top:16px;">Most Correlated Pairs</h3>`;
      html += `<div style="font-size:12px;display:grid;grid-template-columns:1fr 1fr auto;gap:2px 12px;">`;
      data.correlation.top_correlated.slice(0, 10).forEach(p => {
        html += `<div>${p.a}</div><div>${p.b}</div><div>${p.corr.toFixed(3)}</div>`;
      });
      html += `</div>`;
    }
    if (data.correlation.least_correlated) {
      html += `<h3 style="margin-top:16px;">Least Correlated Pairs</h3>`;
      html += `<div style="font-size:12px;display:grid;grid-template-columns:1fr 1fr auto;gap:2px 12px;">`;
      data.correlation.least_correlated.slice(0, 10).forEach(p => {
        html += `<div>${p.a}</div><div>${p.b}</div><div>${p.corr.toFixed(3)}</div>`;
      });
      html += `</div>`;
    }
    corrDiv.innerHTML = html;
  }

  // ─── Item Table ───
  const tableDiv = document.getElementById("item-table");
  const searchInput = document.getElementById("search");
  const typeFilter = document.getElementById("type-filter");
  const sortBy = document.getElementById("sort-by");

  if (tableDiv && data.items) {
    // Populate type filter
    const types = [...new Set(Object.values(data.items).map(d => d.type))].sort();
    types.forEach(t => {
      const opt = document.createElement("option");
      opt.value = t; opt.textContent = t;
      typeFilter.appendChild(opt);
    });

    function renderTable() {
      let entries = Object.entries(data.items);
      const query = (searchInput.value || "").toLowerCase();
      const typeVal = typeFilter.value;
      const sortVal = sortBy.value;

      if (query) entries = entries.filter(([name]) => name.toLowerCase().includes(query));
      if (typeVal !== "all") entries = entries.filter(([, d]) => d.type === typeVal);

      entries.sort((a, b) => {
        if (sortVal === "sharpe") return (b[1].sharpe || 0) - (a[1].sharpe || 0);
        if (sortVal === "vol") return (a[1].vol || 0) - (b[1].vol || 0);
        if (sortVal === "mean_ret") return (b[1].mean_ret || 0) - (a[1].mean_ret || 0);
        if (sortVal === "max_dd") return (b[1].max_dd || 0) - (a[1].max_dd || 0);
        if (sortVal === "last_price") return (b[1].last_price || 0) - (a[1].last_price || 0);
        return 0;
      });

      const shown = entries.slice(0, 100);
      let html = `<div style="font-size:12px;color:var(--muted);margin-bottom:4px;">
        Showing ${shown.length} of ${entries.length} items</div>`;
      html += `<table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead><tr style="border-bottom:1px solid var(--grid);text-align:left;">
          <th style="padding:6px;">Item</th>
          <th style="padding:6px;">Type</th>
          <th style="padding:6px;text-align:right;">Price</th>
          <th style="padding:6px;text-align:right;">Ann. Return</th>
          <th style="padding:6px;text-align:right;">Ann. Vol</th>
          <th style="padding:6px;text-align:right;">Sharpe</th>
          <th style="padding:6px;text-align:right;">Max DD</th>
          <th style="padding:6px;text-align:right;">Skew</th>
          <th style="padding:6px;text-align:right;">Days</th>
        </tr></thead><tbody>`;

      shown.forEach(([name, d]) => {
        const retColor = d.mean_ret > 0 ? "#22c55e" : "#ef4444";
        html += `<tr style="border-bottom:1px solid rgba(255,255,255,.05);">
          <td style="padding:4px 6px;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${name}</td>
          <td style="padding:4px 6px;"><span style="color:${TYPE_COLORS[d.type] || '#6b7280'}">${d.type}</span></td>
          <td style="padding:4px 6px;text-align:right;">$${d.last_price?.toFixed(2) || "?"}</td>
          <td style="padding:4px 6px;text-align:right;color:${retColor};">${pct(d.mean_ret)}</td>
          <td style="padding:4px 6px;text-align:right;">${pct(d.vol)}</td>
          <td style="padding:4px 6px;text-align:right;">${d.sharpe?.toFixed(2) || "?"}</td>
          <td style="padding:4px 6px;text-align:right;color:#ef4444;">${pct(d.max_dd)}</td>
          <td style="padding:4px 6px;text-align:right;">${d.skew?.toFixed(2) || "?"}</td>
          <td style="padding:4px 6px;text-align:right;">${d.n_days}</td>
        </tr>`;
      });
      html += `</tbody></table>`;
      tableDiv.innerHTML = html;
    }

    searchInput.addEventListener("input", renderTable);
    typeFilter.addEventListener("change", renderTable);
    sortBy.addEventListener("change", renderTable);
    renderTable();
  }

  // ─── Metadata ───
  const metaDiv = document.getElementById("metadata");
  if (metaDiv && data.metadata) {
    const m = data.metadata;
    let html = `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;">`;
    const pairs = [
      ["Items (filtered)", m.n_items],
      ["Items (total scanned)", m.n_items_total],
      ["Date Range", `${m.date_range?.[0]} to ${m.date_range?.[1]}`],
      ["Trading Days", m.n_days],
      ["Min Days Filter", m.filters?.min_days],
      ["Max Gap Filter", pct(m.filters?.max_gap_pct || 0)],
    ];
    pairs.forEach(([k, v]) => {
      html += `<div style="padding:8px;border:1px solid rgba(255,255,255,.1);border-radius:6px;background:rgba(255,255,255,.02);">
        <div style="opacity:.6;font-size:11px;margin-bottom:2px;">${k}</div>
        <div style="font-weight:600;font-size:14px;">${v}</div>
      </div>`;
    });

    // Type distribution
    if (m.type_distribution) {
      Object.entries(m.type_distribution).sort((a, b) => b[1] - a[1]).forEach(([type, count]) => {
        html += `<div style="padding:8px;border:1px solid rgba(255,255,255,.1);border-radius:6px;background:rgba(255,255,255,.02);">
          <div style="opacity:.6;font-size:11px;margin-bottom:2px;">${type}</div>
          <div style="font-weight:600;font-size:14px;color:${TYPE_COLORS[type] || '#fff'}">${count}</div>
        </div>`;
      });
    }
    html += `</div>`;
    metaDiv.innerHTML = html;
  }
});
