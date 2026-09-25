// Demo Tender View Controller
// Controls interactive scenario switching for civic watchdog evaluation

const SCENARIOS = {
  1: {
    tenderId: "2025_DTP_554159_1",
    refNo: "ROC No.252/2023",
    authority: "Ettimadai Town Panchayat",
    department: "Directorate of Town Panchayats",
    adminType: "Town Panchayat",
    locality: "Ettimadai",
    zone: "N/A",
    ward: "Not Stated (null)",
    title: "Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park",
    workDesc: "Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park",
    category: "Solid Waste Management / Wet Waste",
    subCategory: "Wet Waste",
    value: "₹ 30,10,000",
    emd: "₹ 30,100",
    publishedDate: "2025-05-03",
    bidOpeningDate: "2025-05-20",
    workPeriod: "90",
    status: "Published / Active",
    sourceUrl: "https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndViewTender&service=direct&sp=S8Epcmeu8nBzBviWyfyF7Rg%3D%3D",
    expectedSignal: "🟢 No accountability signal detected",
    verificationNote: "Official verified tender record from source_dataset.xlsx (Sheet: 10 Panchayat). Verified initial solid-waste infrastructure procurement for Resource Recovery Park in Ettimadai."
  },
  2: {
    tenderId: "2024_DTP_456867_1",
    refNo: "166-6/2024",
    authority: "Pooluvapatti Town Panchayat",
    department: "Directorate of Town Panchayats",
    adminType: "Town Panchayat",
    locality: "Pooluvapatti",
    zone: "N/A",
    ward: "Not Stated (null)",
    title: "Construction of Storage Shed at RR Park",
    workDesc: "Construction of Storage Shed at RR Park",
    category: "Solid Waste Management",
    subCategory: "Storage Infrastructure",
    value: "₹ 4,00,000",
    emd: "₹ 4,000",
    publishedDate: "2024-06-22",
    bidOpeningDate: "2024-07-08",
    workPeriod: "60",
    status: "Period Expired (No Public Evidence)",
    sourceUrl: "https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndViewTender&service=direct&sp=SlDT5TMXqYEhwMMmtKcuNsw%3D%3D",
    expectedSignal: "🟠 Completion evidence gap",
    verificationNote: "Official verified tender record from source_dataset.xlsx (Sheet: 10 Panchayat). Published June 2024 with a 60-day execution period (due August 2024). Over 20 months have passed with no completion certificate or MB record uploaded."
  },
  3: {
    tenderId: "2026_DTP_554159_2",
    refNo: "ROC No.252-B/2026",
    authority: "Ettimadai Town Panchayat",
    department: "Directorate of Town Panchayats",
    adminType: "Town Panchayat",
    locality: "Ettimadai",
    zone: "N/A",
    ward: "Not Stated (null)",
    title: "Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park",
    workDesc: "Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park, Ettimadai Town Panchayat",
    category: "Solid Waste Management / Wet Waste",
    subCategory: "Wet Waste",
    value: "₹ 32,50,000",
    emd: "₹ 32,500",
    publishedDate: "2026-08-10",
    bidOpeningDate: "2026-08-28",
    workPeriod: "120",
    status: "Published / Active",
    sourceUrl: "https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndViewTender&service=direct&sp=S8Epcmeu8nBzBviWyfyF7Rg%3D%3D",
    expectedSignal: "🔴 Repeated procurement detected",
    verificationNote: "Watchdog Flag: Identical solid waste facility work (Windrow Pad with Roofing 2.5 MT at Resource Recovery Park) was previously procured under Tender ID: 2025_DTP_554159_1 within the same local body."
  },
  4: {
    tenderId: "2026_MAWS_649427_5",
    refNo: "E1/Eastzone/2026",
    authority: "Coimbatore City Municipal Corporation",
    department: "MAWS",
    adminType: "Corporation",
    locality: "Coimbatore",
    zone: "East Zone",
    ward: "Ward 24",
    title: "Providing Fencing and Drilling Of Bore Well at Gowthampuri Park Site in Ward No.24, East Zone",
    workDesc: "Providing Fencing and Drilling Of Bore Well at Gowthampuri Park Site in Ward No.24, East Zone",
    category: "Civil Works",
    subCategory: "Borewell & Fencing",
    value: "Not Disclosed",
    emd: "₹ 4,800",
    publishedDate: "2026-09-02",
    bidOpeningDate: "2026-09-18",
    workPeriod: "90",
    status: "Published / Active",
    sourceUrl: "https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndTenderDetails&service=direct&session=T&sp=SMRppx8jt5ysxHWSU%2F5zaJ%2BSJge%2FMOuBR%2BaAsI38I%2Bs4%3D",
    expectedSignal: "⚪ Verified Non-SWM Record (Civil Works)",
    verificationNote: "Official verified tender record from source_dataset.xlsx (Sheet: 10 CBE, Row 1). Verified borewell and fencing work in Ward 24, East Zone.",
    evidenceList: [
      {
        tender_id: "2026_MAWS_649427_5",
        title: "Providing Fencing and Drilling Of Bore Well at Gowthampuri Park Site in Ward No.24, East Zone",
        authority: "Coimbatore City Municipal Corporation",
        locality: "Coimbatore (East Zone / Ward 24)",
        published_date: "2026-09-02",
        similarity_score: 1.0,
        time_difference_days: 0,
        source_url: "https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndTenderDetails&service=direct&session=T&sp=SMRppx8jt5ysxHWSU%2F5zaJ%2BSJge%2FMOuBR%2BaAsI38I%2Bs4%3D",
        type: "CURRENT"
      }
    ]
  }
};

// Add evidenceList to Scenarios 1, 2, 3
SCENARIOS[1].evidenceList = [
  {
    tender_id: "2025_DTP_554159_1",
    title: "Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park",
    authority: "Ettimadai Town Panchayat",
    locality: "Ettimadai",
    published_date: "2025-05-03",
    similarity_score: 1.0,
    time_difference_days: 0,
    source_url: "https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndViewTender&service=direct&sp=S8Epcmeu8nBzBviWyfyF7Rg%3D%3D",
    type: "CURRENT"
  }
];

SCENARIOS[2].evidenceList = [
  {
    tender_id: "2024_DTP_456867_1",
    title: "Construction of Storage Shed at RR Park",
    authority: "Pooluvapatti Town Panchayat",
    locality: "Pooluvapatti",
    published_date: "2024-06-22",
    similarity_score: 1.0,
    time_difference_days: 0,
    source_url: "https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndViewTender&service=direct&sp=SlDT5TMXqYEhwMMmtKcuNsw%3D%3D",
    type: "CURRENT"
  }
];

SCENARIOS[3].evidenceList = [
  {
    tender_id: "2026_DTP_554159_2",
    title: "Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park",
    authority: "Ettimadai Town Panchayat",
    locality: "Ettimadai",
    published_date: "2026-08-10",
    similarity_score: 1.0,
    time_difference_days: 0,
    source_url: "https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndViewTender&service=direct&sp=S8Epcmeu8nBzBviWyfyF7Rg%3D%3D",
    type: "CURRENT"
  },
  {
    tender_id: "2025_DTP_554159_1",
    title: "Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park",
    authority: "Ettimadai Town Panchayat",
    locality: "Ettimadai",
    published_date: "2025-05-03",
    similarity_score: 0.73,
    time_difference_days: 305,
    source_url: "https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndViewTender&service=direct&sp=S8Epcmeu8nBzBviWyfyF7Rg%3D%3D",
    type: "HISTORICAL_MATCH"
  }
];

function renderScenario(scenNum) {
  const data = SCENARIOS[scenNum];
  if (!data) return;

  document.getElementById("tdAuthority").textContent = data.authority;
  document.getElementById("tdDepartment").textContent = data.department;
  document.getElementById("tdRefNo").textContent = data.refNo;
  document.getElementById("tdTenderId").textContent = data.tenderId;
  document.getElementById("tdAdminType").textContent = data.adminType;
  document.getElementById("tdTitle").textContent = data.title;
  document.getElementById("tdWorkDesc").textContent = data.workDesc;
  document.getElementById("tdCategory").textContent = data.category;
  document.getElementById("tdSubCategory").textContent = data.subCategory;
  document.getElementById("tdValue").textContent = data.value;
  document.getElementById("tdEmd").textContent = data.emd;
  document.getElementById("tdLocality").textContent = data.locality;
  document.getElementById("tdZone").textContent = data.zone;
  document.getElementById("tdWard").textContent = data.ward;
  document.getElementById("tdWorkPeriod").textContent = data.workPeriod;
  document.getElementById("tdPublishedDate").textContent = data.publishedDate;
  document.getElementById("tdBidOpeningDate").textContent = data.bidOpeningDate;
  document.getElementById("tdStatus").textContent = data.status;
  document.getElementById("tdSourceLink").href = data.sourceUrl;
  document.getElementById("expectedSignalText").textContent = data.expectedSignal;
  document.getElementById("tdVerificationNote").textContent = data.verificationNote;

  // Render Evidence Records
  const evidenceGrid = document.getElementById("demoEvidenceGrid");
  const badge = document.getElementById("demoEvidenceBadge");
  if (evidenceGrid && data.evidenceList) {
    evidenceGrid.innerHTML = "";
    if (badge) {
      badge.textContent = `${data.evidenceList.length} Verified Record${data.evidenceList.length === 1 ? '' : 's'}`;
    }

    data.evidenceList.forEach((ev) => {
      const isCurr = ev.type === "CURRENT";
      const card = document.createElement("div");
      card.className = `demo-evidence-card ${isCurr ? 'card-curr' : 'card-hist'}`;

      const scoreDisplay = !isCurr && ev.similarity_score != null
        ? `<span class="card-score">${Math.round(ev.similarity_score * 100)}% Similarity Match</span>`
        : (isCurr ? '<span style="font-size:11px;color:#1d4ed8;font-weight:600;">Active Tender Under Review</span>' : '');

      const timeDisplay = ev.time_difference_days === 0
        ? "Active Record"
        : `${ev.time_difference_days} days prior`;

      card.innerHTML = `
        <div class="card-badge-row">
          <span class="card-tag ${isCurr ? 'tag-blue' : 'tag-red'}">
            ${isCurr ? 'Current Tender' : 'Matched Historical Tender'}
          </span>
          ${scoreDisplay}
        </div>
        <div class="card-title-text">${ev.title}</div>
        <div class="card-meta-list">
          <div>Tender ID: <strong>${ev.tender_id}</strong></div>
          <div>Authority: <strong>${ev.authority}</strong></div>
          <div>Locality: <strong>${ev.locality}</strong></div>
          <div>Published: <strong>${ev.published_date}</strong></div>
          <div class="card-meta-full">Time Horizon: <strong>${timeDisplay}</strong></div>
        </div>
        <div class="card-link-row">
          <a href="${ev.source_url}" target="_blank" rel="noopener noreferrer" class="btn-open-official">
            Open Official Source ↗
          </a>
        </div>
      `;
      evidenceGrid.appendChild(card);
    });
  }

  // Update button active state
  [1, 2, 3, 4].forEach((n) => {
    const btn = document.getElementById(`scenario${n}Btn`);
    if (btn) {
      if (n === scenNum) btn.classList.add("active");
      else btn.classList.remove("active");
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("scenario1Btn")?.addEventListener("click", () => renderScenario(1));
  document.getElementById("scenario2Btn")?.addEventListener("click", () => renderScenario(2));
  document.getElementById("scenario3Btn")?.addEventListener("click", () => renderScenario(3));
  document.getElementById("scenario4Btn")?.addEventListener("click", () => renderScenario(4));

  // Default to Scenario 1
  renderScenario(1);
});

