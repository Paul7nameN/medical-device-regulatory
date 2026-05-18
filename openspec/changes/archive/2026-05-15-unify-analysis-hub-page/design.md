## Context

**Arhitectura curentă:**

```
App.tsx Routes:
  /          → DashboardPage
  /upload    → UploadPage
  /violations → ViolationsPage
  /temperature → TemperaturePage
  /reports   → ReportsPage

Toate împărtășesc: AnalysisContext.latestAnalysis
```

**Probleme:**
1. **4 pagini pentru același set de date** - Toate citesc din același context
2. **Redundanță** - Același Compliance Score, același Temperature Chart, aceleași calcule
3. **Navigare ineficientă** - Utilizatorul trebuie să meargă între pagini pentru a vedea datele unei analize
4. **Istoricul** este doar în Reports, dar ar trebui să fie accesibil de oriunde

## Goals / Non-Goals

**Goals:**
- Unifica Dashboard, Temperature, Violations într-o singură pagină "Analysis Hub"
- Simplifica navigarea (sidebar mai puține opțiuni)
- Păstra accesul la istoricul analizelor (dar mai ușor)
- Păstra capacitatea de export

**Non-Goals:**
- Nu rescriem componentele existente (le reutilizăm)
- Nu schimbăm logica din AnalysisContext
- Nu adăugăm funcționalități noi - doar reorganizăm UI
- Nu afectăm Upload (rămâne pagină separată)

## Decisions

### Decizia 1: Structura paginii unificate

**Opțiuni:**
1. **Tab-uri** - Clasic, ușor de înțeles
2. **Butoane segmentate** - Modern, mai compact
3. **Accordion/Expandable** - Toate vizibile simultan, dar depășite

**Decizie:** Combinație

```
┌────────────────────────────────────────────────────────────┐
│  [Score Card cu statistici - mereu vizibil]               │
│  Score: 87%  │  Device: FRIDGE-001  │  [📥 Export]       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [Overview]  [Temperature]  [Violations]  [History]      │  ← Tab-uri
│                                                            │
│  Conținut dinamic:                                         │
│  • Overview: score details + severity breakdown + summary  │
│  • Temperature: chart + min/max/avg cards                 │
│  • Violations: tabel + filtre                             │
│  • History: lista analize anterioare + "Load"            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Rationale:**
- Score Card mereu vizibil = context constant
- Tab-uri pentru conținut detaliat = claritate
- Istoricul ca tab = accesibil ușor, dar nu în primul plan

### Decizia 2: Sidebar simplificat

**Înainte:**
```
┌───────────┐
│ Dashboard │ ← același lucru cu restul
│ Upload    │
│ Violations│ ← redundant
│ Temperature│ ← redundant
│ Reports   │ ← redundant
└───────────┘
```

**După:**
```
┌───────────┐
│ Home      │ ← Analysis Hub (toate datele)
│ Upload    │ ← rămâne
└───────────┘
```

**Sau dacă păstrăm un entry rapid:**
```
┌───────────┐
│ Home      │
│ Upload    │
│ ───────── │
│ History   │ ← shortcut (opțional)
└───────────┘
```

**Decizie:** Minimul necesar - doar "Home" și "Upload"

**Rationale:**
- Pentru cazul "o analiză activă", History poate fi un tab în interior
- Dacă apoi avem nevoie de accese rapid, putem adăuga în sidebar
- Menținem flexibilitatea fără a supraingreuna UI-ul

### Decizia 3: Ce facem cu paginile vechi

**Opțiuni:**
1. **Eliminăm complet** - Ștergem fișierele și rutele
2. **Redirecționăm** - Rutele vechi trimit la /
3. **Păstrăm pentru compatibilitate** - Dar golite/nedeprecate

**Decizie:** Redirecționăm la Home (/), apoi după o perioadă eliminăm.

**Rationale:**
- Bookmarks pot exista - redirecționarea e prietenoasă
- Nu dorim codebase cu cod neutilizat
- Pas intermediar = mai sigur

## Risks / Trade-offs

| Risk | Mitigare |
|------|----------|
| Utilizatorii sunt obișnuiți cu vechea structură | Redirecționăm rutele vechi + poate un tooltip temporar |
| Tab-urile pot ascunde informații | Score Card mereu vizibil + tab-ul "Overview" arată rezumat |
| Istoricul devine mai puțin accesibil | Îl punem ca ultim tab (ușor de găsit) + putem adăuga badge dacă sunt analize noi |
| Nu putem "compara" analize (dacă vom avea) | Arhitectura permite acest lucru viitor - tab-ul History poate fi extins |

## Migration Plan

**Etapa 1 (Implementare):**
1. Extinde `Dashboard.tsx` cu componentele din Temperature și Violations
2. Adaugă tab-uri și logica de comutare
3. Redirecționează rutele vechi (`/violations`, `/temperature`, `/reports`) către `/`
4. Simplifică sidebar

**Etapa 2 (După testare):**
1. Șterge paginile vechi (Temperature, Violations, Reports)
2. Curăță codul neutilizat

## Open Questions

1. **Vrem să păstrăm butoanele de "Reset zoom", "Export", etc. în interiorul tab-urilor?**
   - Da, le mutăm împreună cu componentele

2. **Ce facem cu "Analysis History" din Reports?**
   - Devine un tab în Hub: "History" sau "Previous Analyses"
   - Sau poate un dropdown în headerul paginii?
   - **Decizie:** Tab pentru flexibilitate (poate conține și comparare viitor)

3. **Reports avea grafice agregate (pie chart, bar chart) - păstrăm?**
   - Acestea sunt pentru "overview" - le putem pune în tab-ul "Overview"
   - Sau le eliminăm dacă nu aduc valoare
   - **Decizie:** Le păstrăm în "Overview" dacă există spațiu
