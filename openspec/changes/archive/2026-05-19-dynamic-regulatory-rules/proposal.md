## Why

Regulile de conformitate MED-THERM-2026 sunt **hardcodate** in doua locuri:
1. **Backend**: 24 de clase Python în `backend/app/regulatory/rules/*.py`
2. **Frontend**: 307 linii în `frontend/src/lib/constants/regulatoryRules.ts`

Problema: Pentru orice dispozitiv nou (ex: transport de vaccinuri în loc de plasmă) sau standard nou (MED-THERM-2027), trebuie:
- Modifici cod sursă
- Rul teste
- Redeployezi

Conform cerințelor clientului enterprise:
> "extracting structured regulatory requirements from dense compliance documents"

Userul vrea să dea pur și simplu un fișier `.md` cu reguli și să funcționeze.

## What Changes

### Nou
- **Upload simultan**: Userul poate uploada în același timp logs + fișier de constraints (.md, .txt)
- **Extragere AI**: LLM extrage automat regulile structurate din documentul text
- **Validare dinamică**: `RegulatoryEngine` validează logurile pe baza regulilor extrase (nu doar cele hardcodate)
- **Audit trail**: Fiecare `analysis_session` salvează ce reguli au fost folosite
- **Display dinamic**: Tab-ul "Rules" afișează regulile din analiza curentă (dacă există custom rules)

### Modificări
- `FileUploadZone`: Detectează ce fișiere sunt logs vs. constraints
- `RulesList`: Încarcă regulile dinamic (din analiza sau default)
- `RegulatoryEngine`: Acceptă seturi dinamice de reguli

## Capabilities

### New Capabilities
- `regulatory-rule-extraction`: Extragere structurată de reguli din documente text folosind AI
- `dynamic-rule-validation`: Validare a logurilor pe baza de reguli dinamice, nu doar hardcodate
- `per-analysis-ruleset`: Stocare și afișare a setului de reguli folosit per sesiune de analiză

### Modified Capabilities
- `analysis-sessions`: Adaugă suport pentru reguli custom per analiză
- `compliance-reporting`: Raportul trebuie să menționeze ce reguli au fost folosite

## Impact

| Componentă | Impact |
|------------|--------|
| **Frontend** | `FileUploadZone`, `RulesList`, `AnalysisContext` |
| **Backend** | Nou endpoint `/api/ai/extract-rules`, extensie `TextAnalyzer`, extensie `RegulatoryEngine` |
| **Database** | `analysis_session.config` va stoca `extracted_rules` + metadate |
| **AI Prompts** | Nou sistem de prompt-uri pentru extragerea regulilor |
| **Tests** | Noi teste pentru extragere, teste pentru validare dinamică |

**Severitate schimbare**: Medie - extinde funcționalitatea existentă fără a rupe nimic.
