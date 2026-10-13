"use strict";

// Descriptive Kramer zones only; no bilirubin estimation or risk classification.
const DISTRIBUTIONS = Object.freeze([
  "No visible jaundice reported",
  "Head and neck",
  "Upper trunk (chest and upper abdomen)",
  "Lower abdomen and thighs",
  "Arms and lower legs",
  "Palms and soles"
]);
const LIMITATION = "Kramer distribution is observational only. It cannot determine bilirubin concentration, risk category, or treatment threshold.";

function optionalNumber(value, field, min, max) {
  if (value === "" || value === null || value === undefined) return null;
  const numeric = Number(value);
  if (typeof value === "boolean" || !Number.isFinite(numeric) || numeric < min || numeric > max) {
    throw new RangeError(field + " must be a finite number between " + min + " and " + max);
  }
  return numeric;
}

function assessKramer({ zone, age_hours = null, gestational_weeks = null }) {
  if (typeof zone === "boolean" || !/^[0-5]$/.test(String(zone))) {
    throw new RangeError("Zone must be an integer between 0 and 5");
  }
  const selected = Number(zone);
  const age = optionalNumber(age_hours, "Age in hours", 0, 672);
  const gestation = optionalNumber(gestational_weeks, "Gestational age", 22, 44);
  const early = selected > 0 && age !== null && age < 24;

  let action;
  if (early) {
    action = "Visible jaundice before 24 hours: urgent serum bilirubin measurement and clinical assessment are required.";
  } else if (selected > 0) {
    action = "Visible jaundice: obtain objective bilirubin measurement and assess using an age- and gestation-appropriate guideline.";
  } else {
    action = "No visible jaundice recorded. This does not exclude hyperbilirubinemia; follow routine objective bilirubin screening.";
  }
  if (gestation !== null && gestation < 35) {
    action += " Gestation under 35 weeks: use serum bilirubin and a prematurity-specific clinical protocol.";
  }
  return {
    zone: selected,
    distribution: DISTRIBUTIONS[selected],
    age_hours: age,
    gestational_weeks: gestation,
    early_jaundice: early,
    action,
    limitation: LIMITATION
  };
}

if (typeof document !== "undefined") {
  const form = document.getElementById("assessment-form");
  const result = document.getElementById("result");
  const download = document.getElementById("download");
  let latest = null;

  function paragraph(label, value, cssClass = "") {
    const p = document.createElement("p");
    if (cssClass) p.className = cssClass;
    if (label) {
      const strong = document.createElement("strong");
      strong.textContent = label + " ";
      p.appendChild(strong);
    }
    p.appendChild(document.createTextNode(value));
    return p;
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    try {
      latest = assessKramer({
        zone: document.getElementById("zone").value,
        age_hours: document.getElementById("age").value,
        gestational_weeks: document.getElementById("gestation").value
      });
      result.replaceChildren(
        paragraph("Zone " + latest.zone + ":", latest.distribution, "selected-zone"),
        paragraph("Next step:", latest.action, latest.early_jaundice ? "urgent" : "action"),
        paragraph("Limitation:", latest.limitation),
        paragraph("Recorded context:",
          (latest.age_hours === null ? "Age not provided" : latest.age_hours + " hours") + " · " +
          (latest.gestational_weeks === null ? "Gestation not provided" : latest.gestational_weeks + " weeks"),
          "context")
      );
      document.querySelectorAll(".zone-list li").forEach((li) => {
        li.classList.toggle("active", Number(li.dataset.zone) === latest.zone);
      });
      download.disabled = false;
    } catch (error) {
      latest = null;
      download.disabled = true;
      result.replaceChildren(paragraph("Invalid input:", error.message, "urgent"));
    }
  });

  download.addEventListener("click", () => {
    if (!latest) return;
    const blob = new Blob([JSON.stringify(latest, null, 2) + "\n"], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "kramer-observation.json";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { assessKramer, optionalNumber, DISTRIBUTIONS };
}
