# How to Upload Files

---

## Accepted File Types

| Type | Format | Description |
|------|--------|-------------|
| **Logs** | `.txt` | Log files from medical devices |
| **Images** | `.png`, `.jpg` | Temperature chart images |

---

## How to Upload

1. Go to the **Overview** page

2. **Drag & drop** into the upload zone

3. Or **click on the zone** to select files

Multiple files can be uploaded simultaneously (max 10 files, 50MB each).

---

## What Happens After Upload

1. **Log Parser** parses `.txt` files

2. **AI Image Analysis** analyzes `.png/.jpg` images (if AI is enabled)

3. **Regulatory Engine** runs all rules

4. **Dashboard** updates with results

---

## Example Logs

See practical examples in `docs/user-guide/examples/`:
- `medical_device_logs_1000.txt` - 1000 entry sample
- `compliant_temperature_profile.png` - Compliant chart
- `noncompliant_temperature_profile.png` - Non-compliant chart
