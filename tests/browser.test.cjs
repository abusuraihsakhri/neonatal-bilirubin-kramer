"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { assessKramer, DISTRIBUTIONS } = require("../app.js");

test("all six observational zones are supported", () => {
  for (let zone = 0; zone <= 5; zone++) {
    const value = assessKramer({ zone });
    assert.equal(value.zone, zone);
    assert.equal(value.distribution, DISTRIBUTIONS[zone]);
    assert.equal(value.tier, undefined);
  }
});

test("jaundice before 24 hours warrants urgent serum measurement", () => {
  const value = assessKramer({ zone: 1, age_hours: 12, gestational_weeks: 38 });
  assert.equal(value.early_jaundice, true);
  assert.match(value.action, /urgent serum bilirubin/);
});

test("no early-onset flag at 24 hours", () => {
  assert.equal(assessKramer({ zone: 2, age_hours: 24 }).early_jaundice, false);
});

test("premature infant notes serum and preterm guidance", () => {
  assert.match(assessKramer({ zone: 3, gestational_weeks: 34 }).action, /prematurity-specific/);
});

test("no visible jaundice does not rule out hyperbilirubinemia", () => {
  assert.match(assessKramer({ zone: 0 }).action, /does not exclude/);
});

test("invalid, nonfinite and missing values are rejected", () => {
  for (const zone of [-1, 6, "2.0", null, undefined, true]) {
    assert.throws(() => assessKramer({ zone }), RangeError);
  }
  assert.throws(() => assessKramer({ zone: 1, age_hours: "Infinity" }), RangeError);
  assert.throws(() => assessKramer({ zone: 1, gestational_weeks: 0 }), RangeError);
});
