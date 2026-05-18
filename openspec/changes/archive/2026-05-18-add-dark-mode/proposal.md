## Why

Acest change adauga **Dark Mode complet** la MED-THERM Compliance Engine, cu:
- Toggle in header (Sun ↔ Moon)
- Aceeasi paleta de culori (teal/cyan medical), doar adaptata
- Persistenta in localStorage
- Respecta `prefers-color-scheme` la prima pornire

---

### Problema identificata in timpul explorarii

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     AUDIT DARK MODE READINESS                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ tailwind.config.js    →  deja are: darkMode: ["class"]             │
│  ❌ index.css             →  are doar :root, NU are sectiunea .dark   │
│  ⚠️ Componente mixte:                                                  │
│     • ✅ Folosesc CSS vars (shadcn/ui): bg-background, border-border  │
│     • ❌ ~350 de culori HARDCODATE: bg-white, bg-slate-50,            │
│                                     text-slate-900, text-orange-600    │
│  ❌ Nu exista:                                                          │
│     • ThemeContext                                                      │
│     • Toggle Button                                                     │
│     • Persistenta                                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Detalii despre hardcodari

Scanarea codului a revelat:

| Tip | Numar | Exemple |
|-----|-------|---------|
| `bg-slate-*` | ~45 | `bg-slate-50`, `bg-slate-100`, `bg-slate-200` |
| `bg-white` | ~10 | Carduri, sidebar, header |
| `bg-(orange/purple/red/etc.)-50` | ~20 | Category colors, severity badges |
| `text-slate-*` | ~120 | `text-slate-900`, `text-slate-600`, `text-slate-500` |
| `text-(orange/purple/red/etc.)-600/700` | ~80 | Category icons, labels |

**In total:** ~275+ de schimbari necesare in componente.

---

## What Changes

### 1. Arhitectura Dark Mode

```
┌──────────────────────────────────────────────────────────────────────┐
│                        THEME FLOW                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   First Load:                                                        │
│   ┌──────────────┐                                                   │
│   │ localStorage │───► daca exista ───► foloseste-l                │
│   │   'theme'    │                                                   │
│   └──────────────┘                                                   │
│          │                                                           │
│          ▼ (daca NU exista)                                          │
│   ┌──────────────────┐                                               │
│   │ prefers-color-   │───► 'dark'  ──► seteaza .dark pe html      │
│   │ scheme           │───► 'light' ──► nu seteaza nimic            │
│   └──────────────────┘                                               │
│                                                                      │
│   Toggle Action:                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  User click pe 🌙/☀️                                          │  │
│   │     ├──► Inverseaza clasa .dark pe <html>                   │  │
│   │     ├──► Salveaza in localStorage: 'theme' = 'dark'|'light'│  │
│   │     └──► Actualizeaza contextul                              │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 2. Paleta de culori - aceeasi, dar inversata

**Principiul:** acelasi `hue` (ciano/teal), dar inversam **luminosity**:

```
┌──────────────────────────────────────────────────────────────────────┐
│                    LIGHT MODE ──► DARK MODE                           │
│                (aceeasi paleta, luminozitate inversata)              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  LIGHT:                              DARK:                            │
│  ┌─────────────────────┐            ┌─────────────────────┐          │
│  │ --background        │            │ --background        │          │
│  │   hsl(160, 84%, 97%)│──► INVERS  │   hsl(240, 5%, 8%) │          │
│  │   (teal-50)         │            │   (gray-950)        │          │
│  └─────────────────────┘            └─────────────────────┘          │
│                                                                      │
│  ┌─────────────────────┐            ┌─────────────────────┐          │
│  │ --foreground        │            │ --foreground        │          │
│  │   hsl(175, 65%, 18%)│──► INVERS  │   hsl(160, 84%, 97%)│         │
│  │   (teal-900)        │            │   (teal-50!)        │          │
│  └─────────────────────┘            └─────────────────────┘          │
│                                                                      │
│  ┌─────────────────────┐            ┌─────────────────────┐          │
│  │ --card              │            │ --card              │          │
│  │   hsl(0, 0%, 100%)  │──► INVERS  │   hsl(240, 4%, 10%) │          │
│  │   (white)           │            │   (gray-900)        │          │
│  └─────────────────────┘            └─────────────────────┘          │
│                                                                      │
│  ┌─────────────────────┐            ┌─────────────────────┐          │
│  │ --primary           │            │ --primary           │          │
│  │   hsl(187, 90%, 36%)│──► BRIGHTER│   hsl(187, 92%, 69%)│         │
│  │   (cyan-600)        │            │   (cyan-400)        │          │
│  └─────────────────────┘            └─────────────────────┘          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 3. Severity & Category Colors - Dark Mode variants

Acestea sunt MAI PROBLEMATICE pentru ca au fost hardcodate cu variante light mode:

```
┌──────────────────────────────────────────────────────────────────────┐
│         SEVERITY BADGES - LIGHT vs DARK                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  LIGHT MODE (actual):                    DARK MODE (necesar):        │
│  ┌─────────────────────────────┐        ┌─────────────────────────┐ │
│  │ critical:                   │        │ critical:               │ │
│  │   bg-red-100    (deschis)  │──►►►   │   bg-red-950/50       │ │
│  │   text-red-700  (intens)   │        │   text-red-400         │ │
│  │   border-red-200           │        │   border-red-900       │ │
│  └─────────────────────────────┘        └─────────────────────────┘ │
│                                                                      │
│  high: bg-orange-100  ──►►►  bg-orange-950/50 + text-orange-400 │
│  medium: bg-yellow-100 ──►►►  bg-yellow-950/50 + text-yellow-400 │
│  low: bg-green-100    ──►►►  bg-green-950/50  + text-green-400  │
│  info: bg-blue-100    ──►►►  bg-blue-950/50   + text-blue-400   │
│                                                                      │
│  Aceeasi logica pentru:                                              │
│  • categoryColors (SummaryCard.tsx): orange, purple, red, teal... │
│  • DATA_SOURCE_COLORS (types.ts): green, gray, orange, blue       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Capabilities

### Modified Capabilities
- `dashboard-layout`: Adauga toggle dark mode in header
- `compliance-visualization`: Toate cardurile, tabelele, graficele acum functioneaza in ambele moduri

### New Capabilities
- `theme-system`: Dark mode cu persistenta, respecta preferintele sistemului

---

## Impact

| Component | Tip | Descriere |
|-----------|-----|-----------|
| **NOU: `ThemeContext.tsx`** | Creare | React Context cu useTheme hook, toggle, persistenta |
| **`main.tsx`** | Modificare | Incapsuleaza app cu `<ThemeProvider>` |
| **`index.css`** | Modificare MAJORE | Adauga sectiunea `.dark {}` cu TOATE CSS variables |
| **`tailwind.config.js`** | Posibila modificare | Adauga `success`, `warning` semantic colors daca este nevoie |
| **`Layout.tsx`** | Modificare | Adauga buton toggle in Header langa Notifications |
| **`badge.tsx`** | Modificare MAJORE | Refactor severity variants pentru dark mode |
| **`types.ts`** | Modificare | `SEVERITY_COLORS`, `DATA_SOURCE_COLORS` - trebuie eliminate sau transformate |
| **`SummaryCard.tsx`** | Modificare | `categoryColors` - refactor pentru dark mode |
| **`Dashboard.tsx`** | Modificare MAJORE | ~100+ schimbari: bg-slate-*, text-slate-*, culori severity |
| **`History.tsx`** | Modificare | Similar cu Dashboard |
| **`Upload.tsx`** | Modificare | Similar |
| **+15 componente** | Modificare | Toate celelalte componente cu hardcodari |

---

## Beneficii dupa schimbare

1. **Dark Mode complet**: Toggle, persistenta, respecta sistemul
2. **Aceeasi identitate vizuala**: Nu schimbam paleta, doar luminozitatea
3. **UX mai bun**: Utilizatorii care lucreaza pe timp de noapte sau prefera dark mode
4. **Consistenta**: Toate componentele functioneaza identic in ambele moduri
