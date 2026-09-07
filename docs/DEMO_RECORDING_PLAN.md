# Ambient Guard -- Demo Recording Plan

## Overview

- **Target duration:** 2:30-2:50
- **Platform:** Desktop browser recording (not mobile)
- **Resolution:** 1920x1080 or 1440x900
- **Format:** MP4 (primary), GIF (secondary for Devpost)
- **Production URL:** https://bee.andywongpt.com

---

## Pre-Recording Checklist

### Environment Setup

- [ ] Close all unnecessary browser tabs
- [ ] Hide browser bookmarks bar (Ctrl+Shift+B in Chrome)
- [ ] Ensure stable internet connection
- [ ] Verify production is healthy: `Invoke-RestMethod -Uri "https://bee.andywongpt.com/health"`
- [ ] Verify Bee mode is `mcp` (live Bee data)

### Bee Context Preparation

- [ ] Confirm Bee todo exists: "Go jogging at 5 PM" (ref 28703772)
- [ ] If missing, create new Bee todo with similar content
- [ ] Verify Bee location is reasonably current (not critical if stale)

### Recording Software

- [ ] OBS Studio installed (or Windows Game Bar: Win+G)
- [ ] Microphone tested (if recording voiceover live)
- [ ] Recording directory set to `$KIROCREW_SCRATCH/ambient-guard-demo/`

---

## Browser Tabs to Open

1. **Primary:** https://bee.andywongpt.com (Ambient Guard)
2. **Optional:** Bee app/web to show source context (if accessible)

---

## Recording Sequence

### Phase 1: Hook (0:00-0:15)

**Browser:**
- Navigate to https://bee.andywongpt.com
- Wait for full page load
- Position window to show decision prominently

**Actions:**
- Smooth scroll to ensure decision is centered
- No clicking yet

**Duration:** 15 seconds

---

### Phase 2: Bee Context (0:15-0:35)

**Browser:**
- Ambient Guard UI showing "My Plan" section

**Actions:**
- Point to "Activity: Jogging"
- Point to "Time: 5:00 PM"
- Point to "Source: Bee (ref 28703772)"

**Duration:** 20 seconds

---

### Phase 3: Decision (0:35-1:05)

**Browser:**
- Main decision section

**Actions:**
- Highlight "KEEP YOUR PLANNED TIME -- WITH CAUTION"
- Scroll to show environmental metrics
- Point to AQI, PM2.5, UV, temperature

**Duration:** 30 seconds

---

### Phase 4: Reasoning (1:05-1:30)

**Browser:**
- Evidence drawer (if closed, click to open)

**Actions:**
- Open evidence drawer
- Scroll to show reason codes
- Point to "no_better_window_in_range"
- Point to limitations

**Duration:** 25 seconds

---

### Phase 5: Personal Intelligence (1:30-1:55)

**Browser:**
- Personal context section (if visible) or timeline

**Actions:**
- Point to activity classification (outdoor=True)
- Point to personal feasibility note
- Point to location staleness note

**Duration:** 25 seconds

---

### Phase 6: Timeline (1:55-2:15)

**Browser:**
- Timeline component (scroll down if needed)

**Actions:**
- Scroll to timeline
- Point to 17:00 entry
- Point to "Data kind: forecast"
- Point to "Exposure kind: outdoor"
- Point to uncertainty label

**Duration:** 20 seconds

---

### Phase 7: Technical Proof (2:15-2:35)

**Browser:**
- Could show brief architecture diagram OR stay on UI

**Actions:**
- Quick highlight of production URL in address bar
- Optionally show test evidence (separate window, brief flash)

**Duration:** 20 seconds

---

### Phase 8: Close (2:35-2:50)

**Browser:**
- Ambient Guard main UI

**Actions:**
- Smooth scroll back to top
- Hold on decision + tagline
- Fade out or clean cut

**Duration:** 15 seconds

---

## Window Sizes

### Desktop Recording
- **Window size:** Maximized (1920x1080 or 1440x900)
- **Browser zoom:** 100% (default)

### Mobile View (Optional Second Pass)
- **DevTools:** Toggle device toolbar
- **Device:** iPhone 14 Pro (or similar)
- **Purpose:** Show responsive design in separate clip

---

## Privacy Redaction Checklist

- [ ] No Bee session tokens visible
- [ ] No AWS credentials visible
- [ ] No sensitive location data (precise home address)
- [ ] No personal conversations visible (only the jogging todo)
- [ ] No internal API keys in network tab (if shown)
- [ ] Browser DevTools closed during main recording

---

## Narration Options

### Option A: Live Voiceover
- Record audio during screen capture
- Speak naturally, moderate pace
- Use script from `docs/DEMO_SCRIPT.md`

### Option B: Post-Recording Voiceover
- Record screen first (no audio)
- Add voiceover in post-production
- Sync audio to video segments

### Option C: Text Overlays
- Add text captions during post-production
- No spoken narration
- Suitable for muted autoplay contexts

---

## Fallback Recording Strategy

### If Production Down

1. **Diagnose:** Check server status, Docker containers, Cloudflare tunnel
2. **Quick fix:** SSH to meow server, restart containers
3. **If unfixable:** Record against local development instance
   ```bash
   cd ambient-guard
   docker-compose up
   # Record against http://localhost:18080
   ```
4. **Note in description:** "Demo recorded on local instance"

### If Bee Data Stale

1. **Refresh:** Create new Bee todo immediately before recording
2. **Navigate:** Reload Ambient Guard UI
3. **Proceed:** Record with fresh data

### If Environmental API Down

1. **Check:** Open-Meteo status
2. **Fallback:** Use cached data (already in Ambient Guard response)
3. **Proceed:** Record available data

---

## Post-Recording Processing

### Basic Export
- **Format:** MP4 (H.264 codec)
- **Resolution:** Same as recording (no upscale)
- **Framerate:** 30 fps

### Optional Enhancements
- [ ] Add fade in/out (0.5s)
- [ ] Add subtle background music (royalty-free)
- [ ] Add text overlays for key points
- [ ] Add Ambient Guard logo watermark

### GIF Export
- **Tool:** ffmpeg or ezgif.com
- **Duration:** Full 2:30 or trimmed highlight (30-60s)
- **Size:** Optimize for Devpost (max 5MB recommended)
- **Framerate:** 10-15 fps

---

## File Output

**Primary deliverable:**
- `ambient-guard-demo.mp4` (2:30-2:50)

**Secondary deliverables:**
- `ambient-guard-demo.gif` (compressed, 30-60s highlight)
- `ambient-guard-thumbnail.png` (first frame or custom)

**Location:**
- `$KIROCREW_SCRATCH/ambient-guard-demo/`

---

## Estimated Total Time

| Phase | Duration |
|-------|----------|
| Setup | 10 min |
| Recording (takes) | 20 min |
| Post-processing | 15 min |
| Export | 5 min |
| **Total** | **50 min** |

---

## Success Criteria

- [ ] Duration under 3 minutes
- [ ] Real Bee data visible
- [ ] Decision clearly shown
- [ ] Environmental evidence visible
- [ ] Timeline/provenance shown
- [ ] No secrets exposed
- [ ] Smooth, professional quality
