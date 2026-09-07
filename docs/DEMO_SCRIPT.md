# Ambient Guard -- 3-Minute Demo Script

**Total duration target: 2:30-2:50**

---

## 0:00-0:15 -- Hook

**Narration:**
"Weather apps understand the environment. Bee understands what I'm doing. Ambient Guard connects the two."

**On screen:**
- Ambient Guard main UI
- Decision visible immediately
- Clean, focused interface

**Key point:**
Establish the core value proposition in the first 10 seconds.

---

## 0:15-0:35 -- Real Bee Context

**Narration:**
"Here's a real task from my Bee: Go jogging at 5 PM."

**On screen:**
- Bee context display (if available via Bee app/web)
- OR: Show the Bee context section in Ambient Guard's response

**UI elements to show:**
```
My Plan:
  Activity: Jogging
  Time: 5:00 PM
  Source: Bee (ref 28703772)
```

**Key point:**
Make it obvious this is real Bee data, not a mock. The ref ID proves authenticity.

---

## 0:35-1:05 -- Ambient Guard Decision

**Narration:**
"Ambient Guard retrieves environmental conditions for my jogging time and location, then decides."

**On screen:**
- Decision headline: **KEEP YOUR PLANNED TIME -- WITH CAUTION**
- Environmental evidence summary:
  - US AQI: 117 (Unhealthy for Sensitive Groups)
  - PM2.5: 26 µg/m³
  - UV: 2.2 (Low)
  - Temperature: 29.8°C
- All labelled as "forecast"

**Key point:**
Decision comes first. Environmental metrics support it, not the other way around.

---

## 1:05-1:30 -- Why the Agent Decided

**Narration:**
"Ambient Guard checked a three-hour window around my planned time. No materially better window exists. So it correctly preserves my plan -- but adds appropriate caution about the AQI level."

**On screen:**
- Reason codes: `no_better_window_in_range`
- Limitations: "No materially better time found within ±3h window"
- Evidence drawer showing ±3h comparison (if available)

**Key point:**
Ambient Guard can choose NOT to change the user's plan. This demonstrates controlled abstention rather than forced AI recommendations.

---

## 1:30-1:55 -- Personal Intelligence

**Narration:**
"Ambient Guard checks personal feasibility. It knows my jogging is outdoor, and it would check for conflicts if I had other Bee commitments during alternative windows."

**On screen:**
- Personal context section:
  - Activity classification: outdoor = True
  - Personal feasibility: unknown (no additional constraints detected)
  - Bee location: stale (~2h old), using default

**Honest note:**
"In this live session, I don't have other Bee commitments that would conflict with alternative jogging times. But if I did, Ambient Guard would avoid recommending a window that conflicts with my actual schedule."

**Key point:**
Environmentally better ≠ personally better. The system respects personal context.

---

## 1:55-2:15 -- Personal Environmental Timeline

**Narration:**
"The Personal Environmental Timeline shows my planned activity with environmental context. Note: this is forecast data from Open-Meteo and CAMS, not a personal PM2.5 sensor."

**On screen:**
- Timeline component:
  - 17:00 -- Planned jogging
  - Environmental conditions: AQI, PM2.5, UV, temp
  - Data kind: forecast
  - Exposure kind: outdoor
  - Uncertainty: ["forecast"]

**Key point:**
Transparency about data limitations. No fake sensor claims.

---

## 2:15-2:35 -- Technical Proof

**Narration:**
"Under the hood: Bee MCP provides real context, the normalizer extracts intent, Open-Meteo supplies environmental forecasts, the reasoning engine applies materiality and feasibility rules, and the decision state machine produces the recommendation."

**On screen:**
- Brief architecture diagram (optional, 2-3 seconds)
- OR: Quick flash of production URL (bee.andywongpt.com)
- Test evidence summary (44 passed, Playwright E2E)

**Key point:**
Real integration, real data flow, tested and deployed.

---

## 2:35-2:50 -- Close

**Narration:**
"Bee understands my life. Ambient Guard understands the environment around it."

**On screen:**
- Ambient Guard logo/name
- Tagline: **Your Personal Environmental Agent**
- Secondary: **Powered by real personal context from Bee**

**Key point:**
End cleanly before 3 minutes. Leave judges with the core message.

---

## Recording Checklist

- [ ] Browser: Chrome (clean profile)
- [ ] Resolution: 1920x1080 or 1440x900
- [ ] Window size: Maximize for desktop demo
- [ ] Bee context: Real todo "Go jogging at 5 PM" (ref 28703772)
- [ ] Production URL: https://bee.andywongpt.com
- [ ] Evidence drawer: Open to show metrics
- [ ] Timeline: Scroll to show structure
- [ ] No personal secrets visible
- [ ] No unnecessary browser UI (hide bookmarks if possible)
- [ ] Smooth scroll, no jerky movements
- [ ] Narration recorded separately (optional)

---

## Fallback Strategy

If production is unstable:
1. Use local development server (docker-compose up)
2. Record against localhost:18080
3. Note in description: "Demo recorded on local instance due to temporary production issue"

If Bee data is stale/missing:
1. Create a new Bee todo immediately before recording
2. Refresh Ambient Guard to pull latest context
3. Proceed with live recording

---

## Estimated Segment Durations

| Segment | Target | Content |
| ------- | ------ | ------- |
| Hook | 0:15 | Value proposition |
| Bee Context | 0:20 | Real Bee data |
| Decision | 0:30 | Main output |
| Reasoning | 0:25 | Why this decision |
| Personal Intelligence | 0:25 | Feasibility/conflict |
| Timeline | 0:20 | Provenance/limitations |
| Technical Proof | 0:20 | Architecture/tests |
| Close | 0:15 | Final message |
| **Total** | **2:30** | |

---

## Narration Script (Optional Voiceover)

"Weather apps understand the environment. Bee understands what I'm doing. Ambient Guard connects the two.

Here's a real task from my Bee: Go jogging at 5 PM.

Ambient Guard retrieves environmental conditions for my jogging time and location, then decides: Keep your planned time, but with caution.

It checked a three-hour window. No materially better time exists. So it preserves my plan and adds appropriate AQI guidance.

Ambient Guard checks personal feasibility too. It knows jogging is outdoor, and it would avoid recommending a time that conflicts with my other Bee commitments.

The Personal Environmental Timeline shows forecast data from Open-Meteo and CAMS -- not a personal sensor, but transparent, labelled environmental context.

Bee understands my life. Ambient Guard understands the environment around it.

Ambient Guard -- Your Personal Environmental Agent."

(Word count: ~150, estimated speaking time: 55-65 seconds at normal pace)
