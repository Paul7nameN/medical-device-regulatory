## 1. UI Cleanup - Remove Redundant Button

- [x] 1.1 Identify and remove "View History" button from Dashboard.tsx (lines ~315-325)
- [x] 1.2 Verify History tab remains functional after button removal
- [x] 1.3 Test with single analysis (no button shown anyway)
- [x] 1.4 Test with multiple analyses (button should not appear)

---

## 2. Frontend - Rules Constants and Data Structures

- [x] 2.1 Create new file: frontend/src/lib/constants/regulatoryRules.ts
- [x] 2.2 Define TypeScript interfaces: RegulatoryRule, RuleCategory, RuleSeverity, ValidationType
- [x] 2.3 Populate with all 21 MED-THERM-2026 rules from document:
  - REG-TEMP-1, REG-TEMP-2, REG-TEMP-3, REG-TEMP-4
  - REG-SENS-1, REG-SENS-2, REG-SENS-3
  - REG-ALARM-1, REG-ALARM-2, REG-ALARM-3
  - REG-DATA-1, REG-DATA-2, REG-DATA-3
  - REG-POWER-1, REG-POWER-2
  - REG-COOL-1, REG-COOL-2
  - REG-INS-1, REG-INS-2
  - REG-OPS-1, REG-OPS-2
- [x] 2.4 Ensure each rule has: id, category, categoryName, title, description, threshold, severity, validationType, source, confidence
- [x] 2.5 Export helper functions: getAllRules(), getRulesByCategory(), getRulesByValidationType(), getRuleById()

---

## 3. Frontend - Rules Reference UI Components

- [x] 3.1 Create directory: frontend/src/components/RulesReference/
- [x] 3.2 Create RuleCard.tsx component (displays single rule)
- [x] 3.3 Create RulesFilter.tsx component (category and type dropdowns)
- [x] 3.4 Create RulesList.tsx component (grid of RuleCards with filters)
- [x] 3.5 Style components to match existing Dashboard aesthetic
- [x] 3.6 Add severity color coding (Critical=red, High=orange, etc.)
- [x] 3.7 Add validation type badges (Operational=blue, Inspection=gray)

---

## 4. Frontend - Integrate Rules Tab in Dashboard

- [x] 4.1 Add "Rules" tab trigger to TabsList in Dashboard.tsx
- [x] 4.2 Import RulesList component
- [x] 4.3 Add TabsContent for "rules" value
- [x] 4.4 Update grid-cols for TabsList on mobile (was 4, now 5)
- [x] 4.5 Test tab switching between all tabs
- [x] 4.6 Verify responsive behavior on mobile

---

## 5. Backend - Bug Fix: Correct Rule ID Mappings

- [x] 5.1 Locate CHART_VIOLATION_MAPPINGS in backend/app/ai/image/converters.py
- [x] 5.2 Update "slow_recovery" mapping: REG-TEMP-5 → REG-TEMP-3
- [x] 5.3 Update "frequent_access" mapping: REG-OPS-3 → REG-OPS-2
- [x] 5.4 Update fallback mapping: REG-IMAGES-001 → REG-TEMP-1
- [x] 5.5 Verify all mappings reference valid rule IDs that exist in @register_rule classes

---

## 6. Testing and Verification

- [x] 6.1 Manual test: Upload .png chart and verify violation rule IDs in response
- [x] 6.2 Manual test: Compare .txt analysis vs .png analysis rule IDs (should be consistent)
- [x] 6.3 Test Rules tab filters: select TEMP category → only 4 rules shown
- [x] 6.4 Test Rules tab filters: select Inspection type → only rules requiring physical inspection shown
- [x] 6.5 Verify History tab works without the button
- [x] 6.6 Quick visual check: All 5 tabs fit nicely on desktop and mobile

---

## Rezumat Implementare

**Task-uri completate:**
- ✅ Butonul "View History" a fost eliminat din Dashboard
- ✅ Fișierul `regulatoryRules.ts` creat cu toate cele 21 de reguli
- ✅ Componente UI create: `RuleCard`, `RulesFilter`, `RulesList`
- ✅ Tab-ul "Rules" integrat în Dashboard (acum sunt 5 taburi)
- ✅ Bug fix în `converters.py`: ID-urile de reguli acum sunt corecte:
  - `slow_recovery`: REG-TEMP-5 → REG-TEMP-3
  - `frequent_access`: REG-OPS-3 → REG-OPS-2
  - fallback: REG-IMAGES-001 → REG-TEMP-1

**Modificările făcute:**
1. `frontend/src/pages/Dashboard.tsx` - eliminat buton, adăugat tab Rules
2. `frontend/src/lib/constants/regulatoryRules.ts` - NOU (21 reguli)
3. `frontend/src/components/RulesReference/` - NOI componente
4. `backend/app/ai/image/converters.py` - fix ID-uri reguli
