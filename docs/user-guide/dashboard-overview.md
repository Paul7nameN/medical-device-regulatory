# Dashboard Overview

The dashboard has 5 main tabs:

---

## 1. Overview

General analysis summary:
- **Compliance Score** - Compliance percentage
- **Severity Counts** - Number of violations by severity
- **Compliance by Category** - Summary by category
- **AI Analysis** - If AI is enabled, you'll also see AI insights

---

## 2. Temperature

Temperature chart:
- **Sensor A** - Primary sensor temperature
- **Sensor B** - Secondary sensor temperature (if exists)
- **Safe Range** - Green band indicates safe range (2-8°C)
- **Excursions** - In red/orange when temperature is outside range

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

## 4. Rules

Reference to all MED-THERM-2026 rules:
- Category
- Rule code
- Description
- Default severity

---

## 5. History

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
