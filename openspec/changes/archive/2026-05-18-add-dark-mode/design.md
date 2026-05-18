## Context

Acest design se bazeaza pe explorarea codului din 17 Mai 2026.

### Descoperiri cheie in timpul explorarii

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SITUATIA ACTUALA A CODULUI                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Tailwind CONFIGURAT pentru dark mode:                              │
│     tailwind.config.js:3 → darkMode: ["class"]                         │
│                                                                         │
│     → asta inseamna ca putem folosi:                                   │
│       • `dark:bg-gray-900`                                              │
│       • `dark:text-gray-100`                                            │
│       • pur si simplu adaugam/sterge clasa `.dark` pe `<html>`        │
│                                                                         │
│  2. CSS variables INCOMPLETE:                                           │
│     index.css are doar :root { ... }, fara .dark { ... }              │
│                                                                         │
│  3. MIX de abordari in componente:                                     │
│                                                                         │
│     ✅ SHADC/UI COMPONENTS (corecte):                                  │
│        bg-background, text-foreground, border-border                   │
│        → acestea folosesc hsl(var(--xxx)) si vor functiona            │
│          automat cand adaugam .dark cu variabilele corecte            │
│                                                                         │
│     ❌ TOATE CELELALTE (problema):                                     │
│        bg-white, bg-slate-50, bg-slate-100                            │
│        text-slate-900, text-slate-600, text-slate-500                 │
│        text-orange-600, bg-orange-50 (category colors)                │
│        bg-red-100, text-red-700 (severity badges)                     │
│                                                                         │
│  4. Nu exista:                                                          │
│     • ThemeContext                                                      │
│     • Toggle button                                                     │
│     • localStorage persistenta                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Goals / Non-Goals

**Goals:**
1. ✅ Dark Mode complet functional
2. ✅ Toggle in header (🌙 ↔ ☀️)
3. ✅ Persistenta in localStorage
4. ✅ Respecta `prefers-color-scheme` la prima pornire
5. ✅ Aceeasi paleta de culori (teal/cyan medical)
6. ✅ Toate ~275+ de hardcodari transformate

**Non-Goals:**
1. ❌ Nu schimbam identitatea vizuala (pastram acelasi ton)
2. ❌ Nu adaugam teme custom/altele (doar light ↔ dark)
3. ❌ Nu facem system complex (doar context + toggle)

---

## Decisions

### Decizia 1: Ce abordare folosim pentru culorile hardcodate?

**Problema:**
- Avem ~275+ de locuri cu `bg-slate-50`, `text-slate-900`, etc.
- Acestea NU functioneaza cu dark mode in modul actual

**Optiuni considerate:**

| Opțiune | Descriere | Pro | Contra |
|---------|-----------|-----|--------|
| **A: `dark:*` classes** | Inlocuim fiecare `bg-slate-50` cu `bg-slate-50 dark:bg-gray-800` | Functional, noul cod | 275+ schimbari, foarte verbose |
| **B: CSS variables noi** | Cream variabile noi: `--muted`, `--muted-foreground`, `--card-alt`, etc. + le folosim | Mai curat, semantic | Trebuie sa gasim/redefinim toate semanticele |
| **C: MIX (A + B)** | Variabile pentru cele comune, `dark:*` pentru unice | Flexibil | Trebuie sa gandim ce intra unde |

**Decizie: OPȚIUNEA C (MIX)**

**Rationale:**

```
┌──────────────────────────────────────────────────────────────────────┐
│                STRATEGIA DE REFACTORARE                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  GRUP 1: Folosim VARIANTELE EXISTENTE din CSS vars:                │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                      │
│  bg-white        ──► bg-card                                         │
│  bg-slate-50     ──► bg-muted/30   (sau bg-accent/30)             │
│  bg-slate-100    ──► bg-muted                                       │
│  bg-slate-200    ──► bg-border                                      │
│                                                                      │
│  text-slate-900  ──► text-foreground                                │
│  text-slate-600   ──► text-muted-foreground (secondary)             │
│  text-slate-500   ──► text-muted-foreground                         │
│                                                                      │
│  border-slate-200 ──► border-border                                 │
│  border-slate-300 ──► border-border/80 sau ring                    │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  GRUP 2: Cream NOI VARIABILE in index.css:                          │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                      │
│  Pentru severity si categories:                                      │
│                                                                      │
│  --severity-critical-bg, --severity-critical-text, --severity-critical-border│
│  --severity-high-bg, --severity-high-text, ...                      │
│  --severity-medium-bg, ...                                           │
│  --severity-low-bg, ...                                              │
│  --severity-info-bg, ...                                             │
│                                                                      │
│  Similar pentru categories:                                          │
│  --category-temp-bg, --category-temp-text                           │
│  --category-sens-bg, --category-sens-text                           │
│  etc.                                                                 │
│                                                                      │
│  Sau, mai bine: le definim DUAL in index.css:                       │
│  :root { --severity-critical: ... light mode ... }                  │
│  .dark { --severity-critical: ... dark mode ... }                   │
│                                                                      │
│  Si apoi cream clase Tailwind custom:                                │
│  .bg-severity-critical { background-color: hsl(var(--severity-critical-bg))}│
│  .text-severity-critical { color: hsl(var(--severity-critical-text))}│
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  GRUP 3: Cazuri UNICE - folosim `dark:*` direct:                   │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                      │
│  Spre exemplu:                                                        │
│  "text-green-600" cand este "success/within range"                 │
│  "text-red-600" cand este "error/out of range"                      │
│                                                                      │
│  Pentru acestea, fie:                                                 │
│  • Cream un --success (verde) si --danger (rosu) in plus           │
│  • Sau folosim direct: text-green-600 dark:text-green-400         │
│                                                                      │
│  Decizie: Creezam --success si --danger in CSS vars                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

### Decizia 2: Cum implementam ThemeContext?

**Arhitectura:**

```
┌──────────────────────────────────────────────────────────────────────┐
│                   THEME CONTEXT ARCHITECTURE                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Tipuri de theme:                                                     │
│  • 'light'                                                            │
│  • 'dark'                                                             │
│  • 'system' (opțional - dar mai simplu fara)                         │
│                                                                      │
│  Pentru simplitate, folosim DOAR 'light' | 'dark', nu 'system'.    │
│  La initializare, citim:                                              │
│                                                                      │
│  1. localStorage.getItem('theme')                                    │
│     → daca exista ('light' sau 'dark'), folosim acel                │
│                                                                      │
│  2. Daca NU exista in localStorage:                                  │
│     → window.matchMedia('(prefers-color-scheme: dark)').matches    │
│     → daca true → 'dark', altfel 'light'                            │
│                                                                      │
│  La toggle:                                                           │
│  • Inversam: theme === 'light' ? 'dark' : 'light'                  │
│  • Actualizam clasa pe document.documentElement (html)              │
│  • Salvam in localStorage                                            │
│  • Actualizam contextul                                               │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Interfata Context:**

```typescript
type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}
```

**Toggle Button in Header:**
- Icon: `Sun` cand este dark (click = seteaza light)
- Icon: `Moon` cand este light (click = seteaza dark)
- Pozitie: langa butonul de Notifications in Header

---

### Decizia 3: CSS Variables - ce anume adaugam?

**La inceput, analiza ce EXISTA deja in :root:**

```css
/* Existent in index.css :root */
:root {
  --background: 160 84% 97%;      /* teal-50 */
  --foreground: 175 65% 18%;      /* teal-900 */
  
  --card: 0 0% 100%;               /* white */
  --card-foreground: 175 65% 18%;
  
  --popover: 0 0% 100%;
  --popover-foreground: 175 65% 18%;
  
  --primary: 187 90% 36%;          /* cyan-600 */
  --primary-foreground: 0 0% 98%;
  
  --secondary: 175 84% 32%;        /* teal-600 */
  --secondary-foreground: 0 0% 98%;
  
  --muted: 0 0% 96.1%;             /* slate-50? nu exact, dar similar */
  --muted-foreground: 0 0% 45.1%;
  
  --accent: 0 0% 96.1%;
  --accent-foreground: 0 0% 9%;
  
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 0 0% 98%;
  
  --border: 0 0% 89.8%;            /* ~slate-200 */
  --input: 0 0% 89.8%;
  --ring: 187 90% 36%;
}
```

**Ce TREBUIE adaugat in .dark:**

```css
.dark {
  --background: 240 5% 8%;         /* gray-950 */
  --foreground: 160 84% 97%;       /* teal-50 - invers! */
  
  --card: 240 4% 10%;               /* gray-900 */
  --card-foreground: 160 84% 97%;
  
  --popover: 240 4% 10%;
  --popover-foreground: 160 84% 97%;
  
  --primary: 187 92% 69%;           /* cyan-400 - mai luminos */
  --primary-foreground: 187 90% 15%;
  
  --secondary: 173 60% 40%;         /* teal-500 ajustat */
  --secondary-foreground: 0 0% 98%;
  
  --muted: 240 4% 16%;              /* gray-800 */
  --muted-foreground: 240 5% 65%;   /* gray-400 */
  
  --accent: 240 4% 16%;
  --accent-foreground: 0 0% 98%;
  
  --destructive: 0 72% 51%;         /* red-600, putem pastra */
  --destructive-foreground: 0 0% 98%;
  
  --border: 240 4% 16%;             /* gray-800 */
  --input: 240 4% 16%;
  --ring: 187 92% 69%;              /* cyan-400 */
}
```

**Pe langa acestea, trebuie adaugate:**

1. **Severity colors** (pentru badge-uri):
```css
:root {
  --severity-critical-bg: 0 93% 94%;     /* red-50 */
  --severity-critical-text: 0 74% 42%;   /* red-700 */
  --severity-critical-border: 0 91% 91%;  /* red-100 */
  
  --severity-high-bg: 30 100% 95%;        /* orange-50 */
  --severity-high-text: 24 94% 36%;       /* orange-700 */
  --severity-high-border: 30 96% 89%;     /* orange-100 */
  
  /* ... medium, low, info similar ... */
}

.dark {
  --severity-critical-bg: 0 80% 8%;       /* red-950 */
  --severity-critical-text: 0 91% 71%;    /* red-400 */
  --severity-critical-border: 0 70% 15%;  /* red-900 */
  
  --severity-high-bg: 20 80% 8%;           /* orange-950 */
  --severity-high-text: 20 91% 65%;        /* orange-400 */
  --severity-high-border: 20 70% 15%;      /* orange-900 */
  
  /* ... medium, low, info similar ... */
}
```

2. **Category colors** (pentru SummaryCard):
```css
:root {
  --category-temp-bg: 30 100% 95%;     /* orange-50 */
  --category-temp-text: 24 94% 36%;    /* orange-700 */
  
  --category-sens-bg: 270 100% 97%;    /* purple-50 */
  --category-sens-text: 270 67% 46%;   /* purple-700 */
  
  /* ... data, power, cool, ins, ops similar ... */
}

.dark {
  --category-temp-bg: 20 80% 10%;      /* orange-950/50 */
  --category-temp-text: 20 91% 65%;    /* orange-400 */
  
  --category-sens-bg: 270 80% 10%;     /* purple-950/50 */
  --category-sens-text: 268 94% 75%;   /* purple-400 */
  
  /* ... restul similar ... */
}
```

3. **Success/Info extra** (pentru statusuri):
```css
:root {
  --success: 142 76% 36%;    /* green-600 */
  --success-foreground: 0 0% 98%;
}

.dark {
  --success: 142 71% 45%;    /* green-500 */
  --success-foreground: 0 0% 98%;
}
```

Si apoi in tailwind.config.js sau direct in @layer utilities, definim clasele:

```css
@layer utilities {
  .bg-severity-critical { background-color: hsl(var(--severity-critical-bg)); }
  .text-severity-critical { color: hsl(var(--severity-critical-text)); }
  .border-severity-critical { border-color: hsl(var(--severity-critical-border)); }
  /* ... si la fel pentru high, medium, low, info ... */
  
  .bg-category-temp { background-color: hsl(var(--category-temp-bg)); }
  .text-category-temp { color: hsl(var(--category-temp-text)); }
  /* ... si la fel pentru toate categoriile ... */
  
  .text-success { color: hsl(var(--success)); }
}
```

**SAU**, varianta si mai simpla:
- Fara clase custom, doar modificam direct componentele sa foloseasca perechi `dark:*`
- Pentru ca sunt mai putine componente care folosesc severity si category colors

**Decizie FINALA:**
- Pentru `bg-slate-*`, `text-slate-*`, `border-slate-*` → folosim variabilele CSS existente (`bg-muted`, `text-muted-foreground`, etc.)
- Pentru `severity` in badge.tsx → modificam CVA variants sa aiba perechi `dark:bg-red-950/50 dark:text-red-400 dark:border-red-900`
- Pentru `categoryColors` in SummaryCard → similar, adaugam variante dark
- Pentru `SEVERITY_COLORS`, `DATA_SOURCE_COLORS` in types.ts → trebuie eliminate sau folosite cu variante `dark:*` (vezi tasks.md)

---

## Architecture / Component Diagram

### Dupa implementare

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ARHITECTURA DUPA SCHIMBARE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                           ┌───────────────┐                            │
│                           │   main.tsx    │                            │
│                           │               │                            │
│                           │ ┌───────────┐ │                            │
│                           │ │ThemeProvid│ │                            │
│                           │ │   (wrap)  │ │                            │
│                           │ └─────┬─────┘ │                            │
│                           └───────┼───────┘                            │
│                                   │                                      │
│                                   ▼                                      │
│                         ┌───────────────┐                                │
│                         │   App.tsx     │                                │
│                         │    (routing)  │                                │
│                         └───────┬───────┘                                │
│                                 │                                          │
│         ┌───────────────────────┼───────────────────────┐              │
│         │                       │                       │              │
│         ▼                       ▼                       ▼              │
│  ┌─────────────┐       ┌───────────────┐       ┌─────────────┐       │
│  │  Layout.tsx │       │ Dashboard.tsx │       │ History.tsx │       │
│  │             │       │               │       │             │       │
│  │  ┌───────┐  │       │  Toate bg-*   │       │  Similar    │       │
│  │  │Toggle │  │       │  text-* acum  │       │             │       │
│  │  │Button │  │       │  folosesc     │       │             │       │
│  │  │InHeader│ │       │  CSS vars!    │       │             │       │
│  │  └───┬───┘  │       └───────────────┘       └─────────────┘       │
│  └──────┼──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    useTheme() Hook                                │  │
│  │                                                                   │  │
│  │  • theme: 'light' | 'dark'                                       │  │
│  │  • toggleTheme(): inverseaza si salveaza                        │  │
│  │  • setTheme(theme): seteaza explicit                             │  │
│  │                                                                   │  │
│  │  Se ocupa automat de:                                            │  │
│  │  • document.documentElement.classList.toggle('dark')             │  │
│  │  • localStorage.setItem('theme', theme)                          │  │
│  │  • Initial reading din localStorage sau prefers-color-scheme     │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Risks / Trade-offs

### Riscul 1: Refactoring masiv - ~275+ schimbari

**Descriere:**
- Sunt foarte multe locuri de modificat
- Risc de omisiuni, risc de regressioni

**Mitigare:**
1. **Impartim pe task-uri mici** in tasks.md
2. **Testam dupa fiecare grup** de componente
3. **Strategia**: inlocuim doar cele care se potrivesc perfect cu semantica:
   - `bg-white` → `bg-card` (RISK MIC: card exista si functioneaza)
   - `bg-slate-50` → `bg-muted/30` sau `bg-accent/30`
   - `text-slate-900` → `text-foreground`
   - `text-slate-600`, `text-slate-500` → `text-muted-foreground`
   - `border-slate-200`, `border-slate-300` → `border-border`

**Trade-off:**
- Uneori `bg-slate-50` este folosit pentru un scop mai specific
- Daca observam ca ceva nu arata corect, putem ajusta cu `dark:*`

---

### Riscul 2: SEVERITY_COLORS si DATA_SOURCE_COLORS sunt folosite ca string-uri

**Problema din types.ts:**
```typescript
export const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  // ...
}
```

Acestea sunt **clase Tailwind ca string-uri** folosite in:
- `cn(..., SEVERITY_COLORS[critical])`

Acestea **NU functioneaza** cu `dark:` pentru ca nu putem avea:
`'bg-red-100 dark:bg-red-950/50 text-red-700 dark:text-red-400...'`

... OK, de fapt putem, dar trebuie sa modificam constante.

**Solutii:**

| Solutie | Descriere |
|---------|-----------|
| **A** | Modificam constantele sa includa si `dark:bg-* dark:text-*` |
| **B** | Eliminam constantele si folosim direct componenta `<SeverityBadge>` |
| **C** | Cream un hook `useSeverityColors()` care returneaza in functie de theme |

**Decizie:** **Solutia A + B**
- Pentru `badge.tsx` avem deja `badgeVariants` cu CVA. Putem adauga `dark:*` acolo.
- Pentru `SEVERITY_COLORS` din types.ts, DACA sunt folosite in alte locuri decat badge, le modificam sa includa `dark:`.
- Ideal: trecem totul prin `<SeverityBadge>` componenta.

---

### Riscul 3: Recharts (grafice) nu functioneaza cu CSS vars

**Descriere:**
- `TemperatureChart.tsx` foloseste Recharts
- Culorile pentru grafice sunt probabil inline sau hardcodate
- Recharts nu stie de `dark:` classes

**Mitigare:**
- Folosim `useTheme()` in componente care au grafice
- Transmitem culoarea in functie de theme
- SAU verificam daca exista `document.documentElement.classList.contains('dark')`

**Mai simplu:** Cand refactorizam `TemperatureChart.tsx`, verificam cum sunt definite culorile si folosim variabile conditionate de theme.

---

## Migration Plan

### Ordinea de implementare (crittical path)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     MIGRATION ORDER                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PHAZA 1: INFRASTRUCTURA (functioneaza, dar cu bug-uri vizuale)    │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                      │
│  1. Creeaza ThemeContext.tsx                                         │
│  2. Adauga .dark CSS variables in index.css                         │
│  3. Modifica main.tsx sa includa ThemeProvider                      │
│  4. Adauga Toggle Button in Layout.tsx Header                        │
│                                                                      │
│  → In aceasta faza: toggle functioneaza, dar majoritatea            │
│    componentelor arata GRESIT in dark mode (din cauza hardcodarilor)│
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PHAZA 2: REFACTORARE CORE COMPONENTS                               │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                      │
│  5. badge.tsx - adauga dark:* variants pentru severity              │
│  6. SummaryCard.tsx - adauga dark:* pentru categoryColors          │
│  7. types.ts - SEVERITY_COLORS, DATA_SOURCE_COLORS - daca raman,  │
│     le actualizam cu dark:*                                          │
│  8. ChatMessageBubble.tsx - simplu, doar cateva hardcodari         │
│  9. Layout.tsx - refactor restul (bg-white, bg-slate-50 etc.)      │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PHAZA 3: REFACTORARE RESTUL COMPONENTELOR                          │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                      │
│  10. Dashboard.tsx - CEA MAI MARE, ~100+ schimbari                 │
│  11. History.tsx - similar cu Dashboard                              │
│  12. Upload.tsx                                                      │
│  13. Toate componentele din AIAnalysis, RulesReference, etc.       │
│  14. TemperatureChart.tsx (Recharts, atentie)                       │
│  15. Componente mici: ErrorState, PassFailSummary, etc.             │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PHAZA 4: TESTARE                                                    │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                      │
│  16. Testam toggle in ambele sensuri                                 │
│  17. Testam persistenta dupa refresh                                 │
│  18. Testam toate paginile si toate componentele                    │
│  19. Verificam ca nimic nu s-a rupt in light mode                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Open Questions

1. **Vrem sa pastram `text-success` ca verde?**
   - Acum `text-green-600` este folosit pentru "Within safe range", "Completed"
   - In dark mode, devine `text-green-400`
   - Raspuns implicit: DA, folosim `hsl(var(--success))`

2. **Recharts - cum vrem sa gestionam?**
   - Avem nevoie de culori dinamice
   - Solutie: folosim `useTheme()` si returnam culori diferite
   - Sau: definim variante dark mode in CSS si citim din ele
   - Raspuns implicit: verificam cand ajungem acolo, probabil useTheme()

3. **Daca gasim ceva care arata prost cu `bg-muted` in loc de `bg-slate-50`?**
   - Atunci folosim varianta `dark:*` explicit
   - Nu ne panicam: strategia CSS variables functioneaza pentru 80% din cazuri
