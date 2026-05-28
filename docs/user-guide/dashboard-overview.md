# Dashboard Overview

The dashboard has 5 main tabs, plus the Live Transport page:

---

## 1. Overview

General analysis summary:
- **Compliance Score** - Compliance percentage
- **Severity Counts** - Number of violations by severity
- **Compliance by Category** - Summary by category
- **AI Analysis** - If AI is enabled, you'll also see AI insights

---

## 2. Graphs

Telemetry charts:
- **Temperature** - Primary and secondary sensor temperature
- **Safe Range** - Green band indicates safe range (2-8°C)
- **Excursions** - In red/orange when temperature is outside range
- **Fan Speed** - Ventilation fan RPM
- **Humidity** - Relative humidity level

### Info Cards:
- **Sensor A (Avg)** - Average temperature of primary sensor
- **Sensor B (Avg)** - Average temperature of secondary sensor
- **Safe Range** - Safe range (2-8°C)
- **Status** - Number of detected issues

---

## 3. Violations

Table with all violations:
- **Severity** - Critical, High, Medium, Low
- **Rule Code** - E.g., REG-TEMP-1
- **Description** - Violation description
- **Detected At** - When it was detected
- **Status** - Open, Acknowledged, Resolved

### Top Cards:
- **Critical** - Critical violations (immediate action)
- **Open** - Open violations
- **Acknowledged** - Acknowledged violations
- **Resolved** - Resolved violations

---

## 4. Timeline

Unified chronological view of all events:
- Source badges: Logs (blue), Chart (green), Correlated (orange)
- Shows all violations in time order
- Filter by source, zoom, pan, hover for details

---

## 5. Rules

Reference to all MED-THERM-2026 rules:
- Category
- Rule code
- Description
- Default severity

---

## 6. History

Analysis history:
- Analysis number
- Device
- Analyzed At
- Score
- Violations
- Status
- Actions: Load, Remove

You can:
- **Load** - Load a previous analysis
- **Remove** - Delete an analysis from history
- **Clear All** - Delete all analyses (with confirmation)

---

## Live Transport

Seperate page for real-time monitoring:
- ✅ Runs in background when navigating away
- Persistent banner indicator on all pages
- Supports demo simulations and log file replay
- Real-time rule evaluation with live alerts

See [Live Transport Monitoring](live-monitoring.md) for complete details.
