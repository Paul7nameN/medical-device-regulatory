## Why

Arhitectura curentă are 4 pagini separate care toate afișează practic același set de date, doar în moduri diferite:

- **Dashboard**: Score + Severity + Temperature + Violations (rezumat)
- **Temperature**: Doar graficul de temperatură + statistici
- **Violations**: Doar tabelul cu nereguli + filtre
- **Reports**: Istoric + export + grafice agregate

Probleme identificate:
1. **Redundanță**: Toate 4 paginile folosesc **exact același obiect** din `AnalysisContext` (`latestAnalysis`)
2. **Navigare confuză**: Utilizatorul se întreabă "unde am văzut asta?"
3. **Context împărțit**: Informația despre o analiză nu este într-un singur loc
4. **Inutil pentru cazul "o analiză activă"**: Când ai doar o analiză activă, multiplele pagini nu aduc valoare

## What Changes

- **Creează o singură pagină "Analysis Hub"** care unifică Dashboard, Temperature, Violations
- **Utilizează tab-uri sau butoane segmentate** pentru a comuta între vizualizări
- **Sidebar simplificat**: doar "Home" (Hub), "Upload", și eventualmente "History" (dacă este necesar)
- **Paginile vechi devin redundante** și pot fi eliminate sau redirecționate
- **Istoricul** (din Reports) devine un dropdown/modal în Hub ("Load Previous Analysis")
- **Export** devine un buton în Hub, nu o pagină separată

## Capabilities

### Modified Capabilities
- `dashboard`: Redefinit ca "Analysis Hub" - un singur loc pentru toate datele unei analize
- `navigation`: Simplificare sidebar și rute

## Impact

- **Frontend React**:
  - `App.tsx`: Reducere rute de la 5 la 2-3
  - `Layout.tsx`: Simplificare sidebar navigation
  - `pages/Dashboard.tsx`: Extins cu tab-uri și secțiuni consolidate
  - `pages/Temperature.tsx`: Conținutul mutat în Dashboard ca tab/secțiune
  - `pages/Violations.tsx`: Conținutul mutat în Dashboard ca tab/secțiune
  - `pages/Reports.tsx`: Parțial eliminat - doar istoricul rămâne relevant, dar ca modal

- **UX**:
  - Claritate sporită - totul despre o analiză într-un singur loc
  - Navigare redusă - click-uri mai puține pentru a vedea toate datele
  - Context consistent - vezi mereu ce analiză ai activă
