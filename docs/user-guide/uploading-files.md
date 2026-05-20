# How to Upload Files

---

## Accepted File Types

| Type | Format | Description |
|------|--------|-------------|
| **Logs** | `.txt` | Log files from medical devices |
| **Regulatory Constraints** | `.md`, `.txt` | Custom regulatory rules documents |
| **Images** | `.png`, `.jpg` | Temperature chart images |

---

## How to Upload

1. Go to the **Overview** page

2. **Drag & drop** into the upload zone

3. Or **click on the zone** to select files

Multiple files can be uploaded simultaneously (max 10 files, 50MB each).

---

## Upload Flow Detection

When you upload files, the system automatically detects their purpose:

### Detection Logic

| File Type | How it's detected |
|-----------|-------------------|
| **Constraints Document** | Filename contains `constraint`, `regulation`, `rule`, `reg-` OR content contains `REG-` patterns OR `.md` extension (fallback) |
| **Log File** | Content contains timestamps `YYYY-MM-DD HH:MM` OR keywords like `TEMP_READING`, `DOOR_OPEN`, `ALARM_TRIGGERED`, `SENSOR_TIMEOUT` OR `.txt` extension (fallback) |
| **Image** | `.png`, `.jpg` extension or MIME type `image/*` |

Each file shows a colored badge indicating its detected type:
- 🔵 **Blue** = Device Logs
- 🟣 **Purple** = Regulatory Constraints
- 🟢 **Green** = Chart Image

---

## Custom Regulatory Rules (Advanced)

Instead of using the default `MED-THERM-2026` ruleset, you can upload your own regulatory constraints document.

### How It Works

1. **Upload a constraints document** (`.md` or `.txt` with `REG-` patterns)
2. **AI extracts rules** automatically from the document
3. **Upload your log files** or images - they will use the extracted rules
4. **Results tab** shows violations based on YOUR rules
5. **Rules tab** displays your extracted rules with confidence levels

### Constraints Document Format

The AI can extract rules from almost any readable document. For best results, use the `REG-` pattern:

```markdown
# My Medical Device Constraints

## Temperature Safety

REG-TEMP-1 — Operating Range
The device must maintain temperature between 2°C and 8°C.

REG-TEMP-2 — Excursion Limits
Maximum single excursion: 5 minutes
Maximum cumulative per 24h: 10 minutes

## Sensor Requirements

REG-SENS-1 — Dual Redundancy
At least one primary and one secondary sensor required.
```

### Example Files

Test with the included examples:
- `Medical Device Regulatory Constraints.md` - Full MED-THERM-2026 ruleset

### Combined Upload

You can upload multiple files at once:

**Correct Order (Automatic):**
1. Constraints document is processed FIRST (rules extracted)
2. Logs/images are processed NEXT (using extracted rules)

**Manual Control:**
- After rules are extracted, a banner shows:
  - Number of rules extracted
  - Average confidence percentage
  - Toggle: "Merge with default rules"
  - "Clear" button to discard extracted rules

---

## What Happens After Upload

### Standard Flow (No Custom Rules)

1. **Log Parser** parses `.txt` files
2. **AI Image Analysis** analyzes `.png/.jpg` images (if AI is enabled)
3. **Regulatory Engine** runs default `MED-THERM-2026` rules
4. **Dashboard** updates with results

### Custom Rules Flow

1. **Rule Extraction** from constraints document via AI
   - Rules are categorized by type: `threshold_range`, `duration_limit`, `frequency_limit`, `presence_check`, `inspection_only`
   - Each rule has a confidence score (0.0 - 1.0)
   - Rules with confidence < 0.7 are SKIPPED from auto-validation

2. **Log/Image Analysis** using extracted rules
   - Rules passed to `/api/validate`, `/api/reports/generate`, `/api/ai/analyze-chart`
   - All endpoints now accept `extracted_rules` parameter

3. **Results saved with metadata**
   - `has_custom_rules`: `true`
   - `ruleset_name`: Filename of constraints document
   - `extracted_rules`: Full rule definitions
   - `ruleset_meta`: Source, filename, extraction time, model used

4. **Rules Tab displays custom rules**
   - Shows ruleset name instead of "MED-THERM-2026 Regulatory Rules"
   - Badge shows: "From [filename]"
   - Each rule card shows confidence percentage
   - Critical rules and inspection-only rules counted in header

---

## Confidence Levels

| Confidence | Meaning | Action |
|------------|---------|--------|
| **≥ 80%** | High confidence | Used in validation |
| **70-79%** | Medium confidence | Used in validation |
| **< 70%** | Low confidence | **SKIPPED** from auto-validation, displayed in Rules tab |

The Rules tab shows how many low-confidence rules were skipped (if any).

---

## Example Files

See practical examples in `docs/user-guide/examples/`:

| File | Description |
|------|-------------|
| `Medical Device Regulatory Constraints.md` | Custom rules document (upload this FIRST, then logs/images) |
| `medical_device_logs_1000.txt` | 1000 entry sample log file |
| `compliant_temperature_profile.png` | Compliant chart (test with custom rules) |
| `noncompliant_temperature_profile.png` | Non-compliant chart (test with custom rules) |
| `Super Basic & Generic Client Request.txt` | Simple API example |
| `Complex Enterprise-Level Client Request.txt` | Complex API example |
