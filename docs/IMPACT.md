# Ambient Guard — Impact Narrative

## Core Problem

Environmental information exists, but users still have to manually interpret what it means for their own plans.

Weather apps answer: *"What are the environmental conditions?"*

Ambient Guard answers: *"What do those conditions mean for what I'm planning to do?"*

---

## Who Benefits

### Outdoor Exercisers

**Scenario:** A runner plans a 5 PM jog. Ambient Guard checks AQI, UV, and temperature for that window. If conditions are unfavorable, it suggests a better time — or confirms the plan is acceptable with appropriate precautions.

**Value:** No more guessing whether to exercise now or later.

### Commuters

**Scenario:** A cyclist commutes to work. Ambient Guard can evaluate whether an outdoor portion of the route is better now or in 2 hours, considering air quality and weather.

**Value:** Timing decisions informed by environmental data, not guesswork.

### Outdoor Workers

**Scenario:** A landscaper or construction worker has outdoor tasks. Ambient Guard can recommend shifting certain activities to cooler hours or lower-AQI windows.

**Value:** Reduced heat and pollution exposure during occupational tasks.

### Parents

**Scenario:** A parent plans an outdoor activity with children. Ambient Guard evaluates UV, temperature, and air quality for the planned time, suggesting alternatives if conditions are poor.

**Value:** Informed decisions about children's outdoor exposure.

### Haze- and Pollution-Affected Communities

**Scenario:** A user in a haze-prone region sees AQI warnings. Ambient Guard connects those warnings to their actual plans — "Your planned outdoor activity at 4 PM overlaps with elevated PM2.5; consider moving it indoors or shifting to tomorrow."

**Value:** Actionable guidance during air quality events, not just data.

### UV- and Heat-Sensitive Individuals

**Scenario:** A user planning outdoor errands. Ambient Guard flags high UV or temperature, suggesting an earlier or later window.

**Value:** Protection from sun and heat exposure through timing.

---

## Real Example: Jogging at 5 PM

**Bee captures:** "Go jogging at 5 PM."

**Ambient Guard:**
1. Extracts: jogging (outdoor), 17:00, user's location
2. Retrieves: AQI 117, PM2.5 26 µg/m³, UV 2.2, temp 29.8°C
3. Evaluates: ±3h window — no materially better time (15% threshold)
4. Checks: Personal feasibility — no conflicts detected
5. Returns: **KEEP PLANNED TIME — WITH CAUTION**

**Result:** The user jogs at 5 PM as planned, but takes precautions (hydration, lighter effort) because Ambient Guard flagged the AQI as unhealthy for sensitive groups.

**Why this matters:** The system didn't force a change because no better window existed. It provided useful context without disrupting the user's schedule unnecessarily.

---

## What Ambient Guard Does NOT Claim

- **Not a medical device** — Recommendations are informational, precautionary environmental guidance
- **Not a diagnostic tool** — Does not diagnose health conditions or predict health outcomes
- **Not a personal sensor** — Environmental data is forecast/model-based, not measured at the individual level
- **Not a replacement for local monitoring** — CAMS data is 3-hourly interpolated; local stations may differ

---

## Impact Potential

### Immediate

Users who integrate Bee with Ambient Guard get:

- **Personalized timing recommendations** for outdoor activities
- **Contextual AQI/UV/temperature guidance** tied to their actual plans
- **Provenance transparency** — every data point shows its source

### Broader

- **Public health:** Better timing of outdoor activities could reduce exposure to air pollution, UV, and heat
- **Behavioral change:** Making environmental data actionable could shift when people perform outdoor tasks
- **Wearable integration:** Demonstrates a new category of wearable-powered environmental agents

---

## Limitations

1. **Environmental data is forecast, not measurement** — Interpolated values may differ from local conditions
2. **Personal context requires Bee** — Users without Bee cannot access the personal-context integration
3. **No indoor monitoring** — Ambient Guard evaluates outdoor conditions only
4. **No personal exposure tracking** — Does not measure actual exposure during activities

---

## Future Potential

*(Not currently implemented — listed for transparency)*

- **BLE PM2.5 sensor integration** — Personal exposure tracking
- **Indoor air quality** — CO2, VOC monitoring for indoor activity recommendations
- **Noise exposure** — Urban noise levels affecting outdoor plans
- **Pollen data** — Allergy-sensitive activity timing
- **Smart-home integration** — Automatic air purifier activation based on forecasts
- **Hyperlocal sensing** — Neighborhood-level environmental data

---

## Summary

Ambient Guard solves the **interpretation gap**:

- Environmental data exists
- Personal plans exist (in Bee)
- **Ambient Guard connects them**

This is a new category of application: the **Personal Environmental Agent**.

Weather apps understand the environment. Bee understands the user. Together, they support contextual environmental decisions.
