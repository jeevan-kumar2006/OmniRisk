/**
 * OmniRisk - Frontend Application Logic (Phase 2)
 * Underwriter Risk Profiling, JSON Explorer, What-If Simulation,
 * AI Execution Trace, Risk Provenance, and Portfolio Management.
 */

let allCustomers = [];
let currentAnalysisData = null;
let currentCustomerJson = null;

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  try {
    // 1. Load customers list
    const resp = await fetch("/api/customers");
    if (resp.ok) {
      allCustomers = await resp.json();
      populateCustomerDropdowns(allCustomers);
    }

    // 2. Load background tab data
    loadPortfolio();
    loadEvaluationData();

    // 3. Automatically run demo for CUST1003 (High Risk showcase)
    selectDemo("CUST1003");
  } catch (err) {
    console.error("Initialization error:", err);
  }
}

function populateCustomerDropdowns(customers) {
  const sel1 = document.getElementById("customerSelect");
  const sel2 = document.getElementById("explorerCustomerSelect");

  sel1.innerHTML = '<option value="">-- Choose a Customer Profile --</option>';
  sel2.innerHTML = '<option value="">-- Choose a Customer to Explore --</option>';

  customers.forEach(cid => {
    const opt1 = document.createElement("option");
    opt1.value = cid;
    opt1.textContent = `Customer ${cid}`;
    sel1.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = cid;
    opt2.textContent = `Customer ${cid}`;
    sel2.appendChild(opt2);
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

  if (event && event.target) {
    event.target.classList.add("active");
  }
  const target = document.getElementById(tabId);
  if (target) target.classList.add("active");

  if (tabId === "tab-explorer" && currentAnalysisData) {
    const cid = currentAnalysisData.customer_id;
    const sel = document.getElementById("explorerCustomerSelect");
    if (sel && sel.value !== cid) {
      sel.value = cid;
      loadCustomerJson(cid);
    }
  }
}

function selectDemo(customerId) {
  const sel = document.getElementById("customerSelect");
  if (sel) sel.value = customerId;

  document.querySelectorAll(".demo-btn").forEach(btn => {
    btn.classList.toggle("active", btn.textContent.includes(customerId));
  });

  analyzeCustomer(customerId);
}

function onSelectChange() {
  const cid = document.getElementById("customerSelect").value;
  if (cid) {
    document.querySelectorAll(".demo-btn").forEach(btn => {
      btn.classList.toggle("active", btn.textContent.includes(cid));
    });
    analyzeCustomer(cid);
  }
}

function runAnalysis() {
  const cid = document.getElementById("customerSelect").value;
  if (!cid) {
    alert("Please select a customer profile first.");
    return;
  }
  analyzeCustomer(cid);
}

async function analyzeCustomer(customerId) {
  const loading = document.getElementById("loadingIndicator");
  const results = document.getElementById("resultsSection");
  const analyzeBtn = document.getElementById("analyzeBtn");

  loading.classList.remove("hidden");
  results.classList.add("hidden");
  if (analyzeBtn) analyzeBtn.disabled = true;

  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customer_id: customerId }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Analysis request failed.");
    }

    const data = await res.json();
    currentAnalysisData = data;
    renderResults(data);
  } catch (err) {
    console.error("Analysis error:", err);
    alert(`Analysis Failed: ${err.message}`);
  } finally {
    loading.classList.add("hidden");
    results.classList.remove("hidden");
    if (analyzeBtn) analyzeBtn.disabled = false;
  }
}

function renderResults(data) {
  const brief = data.underwriter_brief;
  const feats = data.features;
  const trace = data.execution_trace;
  const level = data.risk_level.toLowerCase();

  // 1. PRIMARY VISUAL ELEMENT: Score Gauge & Risk Badge
  const scoreCard = document.getElementById("scoreCard");
  scoreCard.className = `kpi-card score-card ${level}`;

  document.getElementById("riskScore").textContent = data.risk_score;
  const badge = document.getElementById("riskLevelBadge");
  badge.textContent = `${data.risk_level} RISK`;

  // 2. Profile Context
  document.getElementById("displayCustomerId").textContent = data.customer_id;
  const pol = feats.policy;
  const ageBandStr = (data.customer_id && currentAnalysisData && currentAnalysisData.customer_id) ? "Age: 35-49 · " : "";
  document.getElementById("customerLocation").textContent = 
    `${ageBandStr}${pol.coverage_count} Coverages · ${pol.policy_tenure} Mo Tenure`;

  const tagsContainer = document.getElementById("policyStatusTags");
  tagsContainer.innerHTML = `
    <span class="badge ${pol.policy_status === 'Active' ? 'badge-accent' : 'badge-neutral'}">
      ${pol.policy_status}
    </span>
    <span class="badge badge-neutral">${feats.claims.valid_claim_count} Valid Claims</span>
  `;

  // 3. Financial Snapshot
  const fin = feats.financial;
  document.getElementById("displayLossRatio").textContent = fin.loss_ratio.toFixed(2);
  document.getElementById("displayPaidPremium").textContent = `₹${fin.total_premium_paid.toLocaleString()}`;
  document.getElementById("displayClaimAmount").textContent = `₹${fin.total_claim_amount.toLocaleString()}`;

  // 4. Execution Mode & Latency Telemetry
  const modeBadge = document.getElementById("displayExecutionMode");
  const headerMode = document.getElementById("headerModeBadge");
  const briefModeTag = document.getElementById("briefModeTag");

  const isLive = trace.execution_mode === "LIVE GEMINI";
  modeBadge.textContent = trace.execution_mode;
  modeBadge.className = `execution-mode-pill ${isLive ? 'live' : 'fallback'}`;
  headerMode.textContent = `Execution: ${trace.execution_mode}`;
  headerMode.className = `badge ${isLive ? 'badge-live' : 'badge-fallback'}`;

  briefModeTag.textContent = `Mode: ${trace.execution_mode}`;
  briefModeTag.style.color = isLive ? '#34d399' : '#fbbf24';

  document.getElementById("briefModelTag").textContent = trace.model;
  document.getElementById("totalLatency").textContent = `${data.total_latency_sec.toFixed(3)}s`;

  const lat = data.latency_breakdown_ms || {};
  document.getElementById("latencyBreakdown").innerHTML = `
    <span>Lookup: ${(lat.data_lookup_ms || 0).toFixed(1)} ms</span>
    <span>Features: ${(lat.feature_engineering_ms || 0).toFixed(1)} ms</span>
    <span>Risk Engine: ${(lat.risk_calculation_ms || 0).toFixed(1)} ms</span>
    <span>Synthesis: ${(lat.summarizer_ms || 0).toFixed(1)} ms</span>
  `;

  // 5. Underwriter Brief
  document.getElementById("briefSummary").textContent = brief.summary;
  document.getElementById("briefConfidence").textContent = 
    `Synthesis Confidence: ${Math.round(brief.confidence * 100)}%`;
  document.getElementById("recommendedAction").textContent = brief.recommended_action;

  // 6. AI Execution Trace Checklist
  document.getElementById("traceApiCallVal").textContent = trace.gemini_api_called ? "✓ Yes" : "✗ No";
  document.getElementById("traceApiCall").className = `trace-item ${trace.gemini_api_called ? 'pass' : 'fail'}`;

  document.getElementById("traceFallbackVal").textContent = trace.fallback_used ? "✓ Fallback Active" : "✗ Fallback Unused";
  document.getElementById("traceFallback").className = `trace-item ${trace.fallback_used ? 'pass' : 'pass'}`;

  document.getElementById("traceProvider").textContent = trace.provider;
  document.getElementById("traceModel").textContent = trace.model;
  document.getElementById("traceRemoteLat").textContent = trace.remote_genai_latency_ms !== null ? `${trace.remote_genai_latency_ms} ms` : "N/A (Fallback)";
  document.getElementById("traceLocalLat").textContent = `${trace.local_processing_latency_ms} ms`;
  document.getElementById("traceStatusBadge").textContent = `Output Schema: ${trace.output_schema_status}`;

  // 7. Why This Risk? (Top Risk Drivers with Evidence)
  const driversList = document.getElementById("riskDriversList");
  driversList.innerHTML = "";
  if (brief.risk_drivers && brief.risk_drivers.length > 0) {
    brief.risk_drivers.slice(0, 3).forEach(d => {
      const item = document.createElement("div");
      item.className = "driver-item";
      item.innerHTML = `
        <div class="driver-header">
          <span class="driver-factor">${escapeHtml(d.factor)}</span>
          <span class="driver-impact ${d.impact}">${d.impact} IMPACT</span>
        </div>
        <div class="driver-evidence">${escapeHtml(d.evidence)}</div>
      `;
      driversList.appendChild(item);
    });
  }

  // 8. Strongest Positive Factors
  const posList = document.getElementById("positiveFactorsList");
  posList.innerHTML = "";
  if (brief.positive_factors && brief.positive_factors.length > 0) {
    brief.positive_factors.forEach(pf => {
      const li = document.createElement("li");
      li.textContent = pf;
      posList.appendChild(li);
    });
  } else {
    posList.innerHTML = "<li>No significant positive mitigating factors recorded.</li>";
  }

  // 9. Key Risk Indicators
  const indList = document.getElementById("keyIndicatorsList");
  indList.innerHTML = "";
  if (brief.key_indicators && brief.key_indicators.length > 0) {
    brief.key_indicators.forEach(ki => {
      const li = document.createElement("li");
      li.textContent = ki;
      indList.appendChild(li);
    });
  }

  // 10. Score Decomposition
  const contribList = document.getElementById("scoreContributorsList");
  contribList.innerHTML = "";
  if (data.score_breakdown && data.score_breakdown.length > 0) {
    data.score_breakdown.forEach(c => {
      const pct = Math.min(100, Math.round((c.points / c.max_points) * 100));
      const el = document.createElement("div");
      el.className = "contributor-item";
      el.innerHTML = `
        <div class="contributor-header">
          <span class="contributor-factor">${escapeHtml(c.factor)}</span>
          <span class="contributor-pts">+${c.points} / ${c.max_points} pts</span>
        </div>
        <div class="contributor-bar-bg">
          <div class="contributor-bar-fill" style="width: ${pct}%"></div>
        </div>
        <div class="contributor-desc">${escapeHtml(c.description)}</div>
      `;
      contribList.appendChild(el);
    });
  }

  // 11. Claim Timeline Table
  const timelineBody = document.getElementById("claimTimelineBody");
  timelineBody.innerHTML = "";
  const timeline = data.claim_timeline || [];
  if (timeline.length > 0) {
    timeline.forEach(c => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${escapeHtml(c.claim_id)}</strong></td>
        <td>${c.date}</td>
        <td>₹${c.amount.toLocaleString()}</td>
        <td><span class="demo-tag" style="background:var(--risk-${c.severity.toLowerCase()}-bg); color:var(--risk-${c.severity.toLowerCase()});">${c.severity}</span></td>
        <td>${c.status}</td>
        <td>${escapeHtml(c.policy_id)}</td>
        <td>${c.is_valid ? '<span style="color:#10b981;">✓ Valid</span>' : `<span style="color:#f59e0b;">⚠ Flagged (${c.flags.join(", ")})</span>`}</td>
      `;
      timelineBody.appendChild(tr);
    });
  } else {
    timelineBody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No historical claim records.</td></tr>';
  }

  // 12. What-If Simulator Defaults
  resetSimulation();

  // 13. Trend Summary
  document.getElementById("trendSummaryText").innerHTML = 
    `Historical claim velocity trend: <strong>${feats.claims.claim_trend}</strong> (Recent claims last 12m: ${feats.claims.claims_last_12_months}, prior 12m: ${feats.claims.claims_last_24_months - feats.claims.claims_last_12_months}).`;

  // 14. Data Quality vs Data Relevance Separation
  const dq = data.data_quality;
  const rel = data.data_relevance;
  document.getElementById("dqTemporalCount").textContent = `${dq.excluded_temporal_claims_count} records`;
  document.getElementById("dqAmountCount").textContent = `${dq.excluded_amount_claims_count} records`;
  document.getElementById("dqSummaryText").textContent = dq.warnings.length > 0 ? dq.warnings.join(" | ") : "All claims logically verified against policy terms.";

  document.getElementById("relScore").textContent = `${rel.relevance_score_percent}%`;
  document.getElementById("relRatio").textContent = `${rel.valid_source_records} / ${rel.total_source_records}`;
  document.getElementById("relImpactText").textContent = rel.impact_on_assessment;

  // 15. Risk Score Provenance Modal Table
  const provBody = document.getElementById("provenanceTableBody");
  provBody.innerHTML = "";
  const prov = data.provenance || [];
  prov.forEach(p => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(p.factor)}</strong></td>
      <td style="color:#38bdf8; font-weight:bold;">+${p.points} / ${p.max_points}</td>
      <td><code>${escapeHtml(p.feature_name)}</code></td>
      <td>${escapeHtml(p.supporting_evidence)}</td>
      <td>${escapeHtml(p.source_records)}</td>
      <td><code>${escapeHtml(p.json_path)}</code></td>
      <td style="font-size:0.75rem; color:#a78bfa;">${escapeHtml(p.source_module)}</td>
    `;
    provBody.appendChild(tr);
  });
}

// What-If Simulator
async function runSimulation() {
  if (!currentAnalysisData) return;

  const cid = currentAnalysisData.customer_id;
  const delta = parseInt(document.getElementById("simClaimsDelta").value) || 0;
  const lrInput = document.getElementById("simLossRatio").value;
  const openInput = document.getElementById("simOpenClaims").value;
  const sevInput = document.getElementById("simSeverity").value;

  const payload = {
    customer_id: cid,
    claims_last_12_months_delta: delta,
    loss_ratio_override: lrInput ? parseFloat(lrInput) : null,
    open_claims_override: openInput ? parseInt(openInput) : null,
    severity_override: sevInput ? sevInput : null,
  };

  try {
    const res = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Simulation failed");
    const sim = await res.json();

    const box = document.getElementById("simResultBox");
    box.classList.remove("hidden");

    document.getElementById("simBeforeScore").textContent = `${sim.before_score} (${sim.before_level})`;
    document.getElementById("simAfterScore").textContent = `${sim.after_score} (${sim.after_level})`;
    document.getElementById("simScoreDelta").textContent = `${sim.score_delta >= 0 ? '+' : ''}${sim.score_delta} pts`;
    document.getElementById("simScoreDelta").style.color = sim.score_delta > 0 ? 'var(--risk-high)' : (sim.score_delta < 0 ? 'var(--risk-low)' : 'var(--text-primary)');

    document.getElementById("simChangedFactors").innerHTML = 
      `<strong>Parameter Adjustments:</strong> ${sim.changed_factors.join(" | ")}<br><small style="color:var(--text-muted);">${sim.simulation_notice}</small>`;
  } catch (err) {
    alert(`Simulation error: ${err.message}`);
  }
}

function resetSimulation() {
  document.getElementById("simClaimsDelta").value = 0;
  document.getElementById("simLossRatio").value = "";
  document.getElementById("simOpenClaims").value = "";
  document.getElementById("simSeverity").value = "";
  const box = document.getElementById("simResultBox");
  if (box) box.classList.add("hidden");
}

// Risk Provenance Modal
function toggleProvenanceModal() {
  const modal = document.getElementById("provenanceModal");
  modal.classList.toggle("hidden");
}

// Customer JSON Explorer
async function loadCustomerJson(customerId) {
  if (!customerId) return;
  const viewer = document.getElementById("jsonViewer");
  viewer.textContent = "Loading customer JSON...";
  document.getElementById("currentJsonPath").textContent = `data/processed/customer_profiles.json -> [${customerId}]`;

  try {
    const res = await fetch(`/api/customer-json/${customerId}`);
    if (!res.ok) throw new Error("Failed to load customer JSON");
    const data = await res.json();
    currentCustomerJson = data;
    viewer.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    viewer.textContent = `Error: ${err.message}`;
  }
}

function copyCustomerJson() {
  if (!currentCustomerJson) {
    alert("No customer JSON loaded.");
    return;
  }
  navigator.clipboard.writeText(JSON.stringify(currentCustomerJson, null, 2))
    .then(() => alert("Customer JSON copied to clipboard!"))
    .catch(() => alert("Failed to copy JSON."));
}

// Portfolio View
async function loadPortfolio() {
  try {
    const res = await fetch("/api/portfolio");
    if (!res.ok) return;
    const p = await res.json();

    document.getElementById("portLowCount").textContent = p.low_count;
    document.getElementById("portMedCount").textContent = p.medium_count;
    document.getElementById("portHighCount").textContent = p.high_count;

    const tbody = document.getElementById("portfolioTableBody");
    tbody.innerHTML = "";
    (p.all_customers || []).forEach(c => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${escapeHtml(c.customer_id)}</strong></td>
        <td style="font-weight:bold;">${c.risk_score}</td>
        <td><span class="demo-tag" style="background:var(--risk-${c.risk_level.toLowerCase()}-bg); color:var(--risk-${c.risk_level.toLowerCase()});">${c.risk_level}</span></td>
        <td>${c.valid_claims}</td>
        <td>${c.loss_ratio.toFixed(2)}</td>
        <td>${c.highest_severity}</td>
        <td>${c.policy_status}</td>
        <td>₹${c.annual_premium.toLocaleString()}</td>
        <td><button class="btn btn-sm btn-secondary" onclick="analyzeAndSwitch('${c.customer_id}')">Analyze ➔</button></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading portfolio:", err);
  }
}

function filterPortfolioTable() {
  const query = document.getElementById("portfolioSearch").value.toUpperCase();
  const rows = document.getElementById("portfolioTableBody").getElementsByTagName("tr");
  for (let i = 0; i < rows.length; i++) {
    const txt = rows[i].textContent || rows[i].innerText;
    rows[i].style.display = txt.toUpperCase().indexOf(query) > -1 ? "" : "none";
  }
}

function analyzeAndSwitch(customerId) {
  selectDemo(customerId);
  switchTab("tab-analyzer");
}

// Evaluation & ML Challengers
async function loadEvaluationData() {
  try {
    const res = await fetch("/api/evaluation");
    if (!res.ok) return;
    const ev = await res.json();

    document.getElementById("evalAccuracy").textContent = `${ev.overall_accuracy_percent}%`;
    document.getElementById("evalPrecision").textContent = `${ev.weighted_precision_percent}%`;
    document.getElementById("evalRecall").textContent = `${ev.weighted_recall_percent}%`;
    document.getElementById("evalF1").textContent = `${ev.weighted_f1_percent}%`;

    const tbody = document.getElementById("challengerTableBody");
    tbody.innerHTML = "";
    (ev.challenger_models || []).forEach(m => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${escapeHtml(m.model_name)}</strong></td>
        <td><span class="badge ${m.role.includes('Production') ? 'badge-accent' : 'badge-neutral'}">${m.role}</span></td>
        <td><strong>${m.accuracy}%</strong></td>
        <td>${m.macro_f1}%</td>
        <td>${m.weighted_f1}%</td>
        <td>${m.roc_auc}</td>
        <td>${m.brier_score}</td>
        <td><span class="demo-tag" style="${m.status.includes('Active') ? 'background:#064e3b; color:#34d399;' : 'color:var(--text-muted);'}">${m.status}</span></td>
      `;
      tbody.appendChild(tr);
    });

    if (ev.methodology && ev.methodology.disclaimer) {
      document.getElementById("evalDisclaimer").textContent = ev.methodology.disclaimer;
    }
  } catch (e) {
    console.error("Error loading benchmark evaluation:", e);
  }
}

// Custom JSON Toggle & Analysis
function toggleCustomJson() {
  const container = document.getElementById("customJsonContainer");
  container.classList.toggle("hidden");
}

function loadSampleJson() {
  const sample = {
    customer_id: "CUSTOM_ADVERSE_01",
    city: "Mumbai",
    state: "MH",
    age_band: "35-49",
    policies: [
      {
        policy_id: "POL9991",
        product_name: "Motor Comprehensive",
        policy_start_date: "2023-01-01",
        policy_end_date: "2026-01-01",
        policy_term_months: 36,
        annual_premium: 25000,
        sum_insured: 500000,
        status: "Active",
        coverages: [
          { coverage_id: "COV1", coverage_name: "OwnDamage", coverage_sum: 500000 },
          { coverage_id: "COV2", coverage_name: "ThirdParty", coverage_sum: 500000 }
        ]
      }
    ],
    claims: [
      {
        claim_id: "CLM_DEMO_1",
        policy_id: "POL9991",
        customer_id: "CUSTOM_ADVERSE_01",
        claim_date: "2025-05-10",
        claim_amount: 175000,
        claim_status: "Pending",
        severity: "Critical",
        is_date_valid: true,
        is_amount_valid: true,
        quality_flags: []
      },
      {
        claim_id: "CLM_DEMO_2",
        policy_id: "POL9991",
        customer_id: "CUSTOM_ADVERSE_01",
        claim_date: "2025-02-14",
        claim_amount: 85000,
        claim_status: "Settled",
        severity: "High",
        is_date_valid: true,
        is_amount_valid: true,
        quality_flags: []
      }
    ],
    payments: [
      {
        payment_id: "PAY_1",
        policy_id: "POL9991",
        customer_id: "CUSTOM_ADVERSE_01",
        payment_date: "2024-01-05",
        premium_amount: 25000,
        payment_method: "NetBanking"
      }
    ]
  };

  document.getElementById("customJsonInput").value = JSON.stringify(sample, null, 2);
}

async function runCustomJsonAnalysis() {
  const text = document.getElementById("customJsonInput").value.trim();
  if (!text) {
    alert("Please paste or write a valid JSON payload.");
    return;
  }

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch (err) {
    alert(`Invalid JSON: ${err.message}`);
    return;
  }

  const loading = document.getElementById("loadingIndicator");
  const results = document.getElementById("resultsSection");
  loading.classList.remove("hidden");
  results.classList.add("hidden");

  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: parsed }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Analysis request failed.");
    }

    const data = await res.json();
    currentAnalysisData = data;
    renderResults(data);
  } catch (err) {
    alert(`Analysis Failed: ${err.message}`);
  } finally {
    loading.classList.add("hidden");
    results.classList.remove("hidden");
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
