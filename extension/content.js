// Municipal Tender Watchdog - Content Script
// Extracts tender information from active webpage without relying solely on rigid selectors

(function () {
  function cleanText(str) {
    return (str || "")
      .replace(/&nbsp;/gi, " ")
      .replace(/\u00a0/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function extractLabelValues() {
    const data = {};

    // 1. Scan tables for label -> value pairs (calibrated for live NIC-GEP portal tables)
    const rows = document.querySelectorAll("tr, div.row, dl");
    rows.forEach((row) => {
      const cells = row.querySelectorAll("td, th, dd, dt");
      if (cells.length >= 2) {
        for (let i = 0; i < cells.length - 1; i++) {
          const rawLabel = cleanText(cells[i].innerText || cells[i].textContent);
          const label = rawLabel.toLowerCase();
          const val = cleanText(cells[i + 1].innerText || cells[i + 1].textContent);
          if (!label || !val || label.length > 60) continue;

          if ((label.includes("tender id") || label === "tender id") && !data.tender_id) {
            // Filter out button labels
            const m = val.match(/\b(202\d_[A-Za-z0-9]{2,8}_\d+_\d+)\b/);
            data.tender_id = m ? m[1] : val.split(/\s+/)[0];
          }
          if ((label.includes("tender reference") || label.includes("ref no") || label === "reference number") && !data.reference_no) {
            data.reference_no = val;
          }
          if ((label.includes("organisation chain") || label.includes("organization chain") || label.includes("organisation") || label.includes("authority") || label.includes("department")) && !data.authority) {
            data.authority = val;
          }
          if ((label === "title" || label.includes("tender title") || label.includes("name of work")) && !data.title) {
            data.title = val;
          }
          if ((label.includes("work description") || label.includes("description of work")) && !data.work_description) {
            data.work_description = val;
          }
          if ((label.includes("tender value") || label.includes("estimated cost") || label.includes("contract value")) && !data.tender_value) {
            data.tender_value = val;
          }
          if ((label.includes("published date") || label.includes("publish date")) && !data.published_date) {
            data.published_date = val;
          }
          if ((label.includes("bid opening") || label.includes("opening date")) && !data.bid_opening_date) {
            data.bid_opening_date = val;
          }
          if ((label.includes("period of work") || label.includes("work period") || label.includes("completion period")) && !data.work_period_days) {
            data.work_period_days = val;
          }
          if ((label.includes("location") || label === "place") && !data.location) {
            data.location = val;
          }
          if (label === "status" && !data.status) {
            data.status = val;
          }
        }
      }
    });

    // 2. Scan meta tags or data attributes
    const metaId = document.querySelector('meta[name="tender-id"], [data-tender-id]');
    if (metaId && !data.tender_id) data.tender_id = metaId.getAttribute("content") || metaId.getAttribute("data-tender-id");

    return data;
  }

  function detectTenderPage() {
    const bodyText = document.body ? document.body.innerText : "";
    const lower = bodyText.toLowerCase();
    
    // Key procurement signals
    const hasTenderKeyword = lower.includes("tender id") || lower.includes("tender reference") || lower.includes("work description") || lower.includes("bid opening");
    const hasLocalGovKeyword = lower.includes("corporation") || lower.includes("town panchayat") || lower.includes("municipality") || lower.includes("tntenders");
    const isLivePortal = window.location.hostname.includes("tntenders.gov.in") || window.location.href.includes("tntenders.gov.in");

    const structured = extractLabelValues();
    const isDetected = hasTenderKeyword || Boolean(structured.tender_id) || Boolean(structured.reference_no);

    return {
      isTender: isDetected,
      isLivePortal: isLivePortal,
      portalHost: window.location.hostname || "local",
      structured: structured,
      source_url: window.location.href,
      raw_page_text: bodyText.slice(0, 20000)
    };
  }

  // Handle messages from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "detectPage" || request.action === "extractTender") {
      const result = detectTenderPage();
      sendResponse(result);
    }
    return true; // Keep message channel open for async response
  });
})();
