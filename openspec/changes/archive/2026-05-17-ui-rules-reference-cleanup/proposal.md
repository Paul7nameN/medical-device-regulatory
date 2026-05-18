## Why

Acest change rezolvă 3 probleme identificate în timpul explorării:
1. **Redundanță UI**: Butonul "View History" și tab-ul "History" fac același lucru - neclaritate pentru utilizator
2. **Lipsește referința regulilor**: Nu există un loc central unde utilizatorul poate vedea TOATE cele 21 de reguli MED-THERM-2026 în limbaj natural
3. **Bug ID-uri reguli**: `converters.py` folosește ID-uri de reguli care nu există (`REG-TEMP-5`, `REG-OPS-3`, `REG-IMAGES-001`) - cauzează inconsistență când se analizează imagini/grafice

## What Changes

### Eliminare redundanță
- ✂️ Șterge butonul "View History" din `Dashboard.tsx`
- ✅ Păstrează doar tab-ul "History" care are aceeași funcționalitate

### Nouă funcționalitate: Rules Reference
- 🆕 Adaugă un tab nou "Rules" în Dashboard
- Afișează toate cele 21 de reguli MED-THERM-2026
- Filtrare pe categorii (TEMP, SENS, ALARM, DATA, POWER, COOL, INS, OPS)
- Filtrare pe status (Operational, Inspection, Info)
- Fiecare regulă arată: ID, prag, descriere, severitate, metodă de validare

### Bug Fix: ID-uri corecte pentru reguli
- 🐛 Corectează `CHART_VIOLATION_MAPPINGS` din `backend/app/ai/image/converters.py`:
  - `slow_recovery`: `REG-TEMP-5` → `REG-TEMP-3`
  - `frequent_access`: `REG-OPS-3` → `REG-OPS-2`
  - `fallback`: `REG-IMAGES-001` → elimină sau folosește un ID existent

## Capabilities

### New Capabilities
- `rules-reference`: Tab nou în Dashboard care afișează toate regulile MED-THERM-2026 cu filtre și descrieri detaliate

### Modified Capabilities
- `chart-image-data-extraction`: Corectează maparea ID-urilor de reguli pentru a fi consistente cu celelalte părți ale sistemului

## Impact

| Component | Impact |
|-----------|--------|
| Frontend `Dashboard.tsx` | Ștergere buton, adăugare tab nou + componenta RulesList |
| Frontend Components | Component nou: `RulesReference` (sau similar) |
| Backend `converters.py` | Bug fix - schimbare valorilor în dicționar |
| Rularea analizelor pe imagini | ID-urile de reguli vor fi consistente cu documentul oficial |
| Rapoartele și istoricul | Violările din imagini vor avea ID-uri corecte |
