## Ordine de executie

**Recomandare:** Progreseaza pe rand. Testeaza dupa fiecare task mare.

---

## PHAZA 1: INFRASTRUCTURA

Cand termini aceasta faza, toggle-ul va functiona, dar multe componente vor arata prost in dark mode (din cauza hardcodarilor).

---

### Task 1: Creeaza ThemeContext.tsx

- [x] 1.1 Creeaza fisierul nou: `frontend/src/lib/context/ThemeContext.tsx`

- [x] 1.2 Adauga acest cod:

```typescript
import React, { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

function getInitialTheme(): Theme {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('theme') as Theme | null
    if (stored === 'light' || stored === 'dark') {
      return stored
    }
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }
  }
  return 'light'
}

function applyThemeToDocument(theme: Theme) {
  if (typeof window === 'undefined') return
  
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme)

  useEffect(() => {
    applyThemeToDocument(theme)
  }, [theme])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setThemeState(newTheme)
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', newTheme)
    }
  }

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', newTheme)
    }
  }

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
```

- [x] 1.3 Verifica ca `lib/context` exista (exista deja, pentru ca ai `AnalysisContext.tsx` acolo)

---

### Task 2: Modifica main.tsx pentru a include ThemeProvider

- [x] 2.1 Deschide: `frontend/src/main.tsx`

- [x] 2.2 Importa `ThemeProvider`:
```typescript
import { ThemeProvider } from '@/lib/context/ThemeContext'
```

- [x] 2.3 Incapsuleaza `<App />` cu `<ThemeProvider>`:

**INAINTE:**
```tsx
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AnalysisProvider>
          <App />
        </AnalysisProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
```

**DUPA:**
```tsx
root.render(
  <React.StrictMode>
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AnalysisProvider>
            <App />
          </AnalysisProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  </React.StrictMode>
)
```

---

### Task 3: Adauga sectiunea .dark in index.css

- [x] 3.1 Deschide: `frontend/src/index.css`

- [x] 3.2 Dupa `@layer base { :root { ... } }` (dupa linia ~38), adauga variabilele pentru dark mode:

**IMPORTANT:** Verifica valorile din `:root` actual inainte de a copia. Acest cod se bazeaza pe ce am gasit in explorare.

```css
@layer base {
  .dark {
    --background: 240 5% 8%;
    --foreground: 160 84% 97%;

    --card: 240 4% 10%;
    --card-foreground: 160 84% 97%;

    --popover: 240 4% 10%;
    --popover-foreground: 160 84% 97%;

    --primary: 187 92% 69%;
    --primary-foreground: 187 90% 15%;

    --secondary: 173 60% 40%;
    --secondary-foreground: 0 0% 98%;

    --muted: 240 4% 16%;
    --muted-foreground: 240 5% 65%;

    --accent: 240 4% 16%;
    --accent-foreground: 0 0% 98%;

    --destructive: 0 72% 51%;
    --destructive-foreground: 0 0% 98%;

    --border: 240 4% 16%;
    --input: 240 4% 16%;
    --ring: 187 92% 69%;
  }
}
```

- [x] 3.3 (Optional) Adauga si --success pentru verde:

Dupa --ring in ambele sectiuni (:root si .dark), poti adauga:

In :root:
```css
--success: 142 76% 36%;
```

In .dark:
```css
--success: 142 71% 45%;
```

Si in tailwind.config.js la colors, adauga:
```javascript
success: "hsl(var(--success))",
```

**SAU** (mai simplu pentru inceput), cand ajungem la task-urile cu `text-green-600`, inlocuim cu `text-green-600 dark:text-green-400`.

---

### Task 4: Adauga Toggle Button in Layout.tsx Header

- [x] 4.1 Deschide: `frontend/src/components/Layout.tsx`

- [x] 4.2 Importa:
  - `useTheme` din `@/lib/context/ThemeContext`
  - `Sun`, `Moon` din `lucide-react` (acestea probabil nu sunt inca importate)

- [x] 4.3 In componenta `Header`, importa folosind `useTheme()`:

Intra in `function Header({ onMenuClick }: ...)` si adauga la inceput:
```typescript
const { theme, toggleTheme } = useTheme()
```

- [x] 4.4 Gasesceste butonul de Notifications (in jurul liniilor 243-251 in varianta actuala):

Arata cam asa:
```tsx
<div className="flex items-center gap-2">
  <Button
    variant="ghost"
    size="icon"
    className="h-9 w-9 touch-target"
    aria-label="Notifications"
  >
    <AlertTriangle className="h-5 w-5 text-slate-500" />
  </Button>
</div>
```

- [x] 4.5 **ADAUGA** butonul de Theme inainte de Notifications:

```tsx
<div className="flex items-center gap-2">
  <Button
    variant="ghost"
    size="icon"
    className="h-9 w-9 touch-target"
    aria-label="Toggle theme"
    onClick={toggleTheme}
  >
    {theme === 'dark' ? (
      <Sun className="h-5 w-5" />
    ) : (
      <Moon className="h-5 w-5" />
    )}
  </Button>
  <Button
    variant="ghost"
    size="icon"
    className="h-9 w-9 touch-target"
    aria-label="Notifications"
  >
    <AlertTriangle className="h-5 w-5 text-slate-500" />
  </Button>
</div>
```

- [x] 4.6 Verifica importurile pentru `Sun`, `Moon`

---

### TESTARE RAPIDA dupa Phaza 1

- [ ] Porneste `npm run dev`
- [ ] Verifica daca in Header apare 🌙 sau ☀️ langa Notifications
- [ ] Da click pe el - se schimba iconita?
- [ ] Verifica daca `<html>` are clasa `dark` cand toggle pe dark
- [ ] **Observatie**: Majoritatea lucrurilor vor arata PROST acum (din cauza hardcodarilor). Dar infrastructura functioneaza!

---

## PHAZA 2: CORE COMPONENTS

Acum refactorizam componentele centrale care au culoari hardcodate.

---

### Task 5: badge.tsx - Dark mode pentru severity variants

- [x] 5.1 Deschide: `frontend/src/components/ui/badge.tsx`

- [x] 5.2 Gasesceste `badgeVariants` ~linia 7

Varianta actuala pentru severity:
```typescript
critical: "border-transparent bg-red-100 text-red-700 border-red-200",
high: "border-transparent bg-orange-100 text-orange-700 border-orange-200",
medium: "border-transparent bg-yellow-100 text-yellow-700 border-yellow-200",
low: "border-transparent bg-green-100 text-green-700 border-green-200",
info: "border-transparent bg-blue-100 text-blue-700 border-blue-200",
```

- [x] 5.3 **INLOCUIESTE-Le** cu variante cu dark mode:

```typescript
critical: "border-transparent bg-red-100 text-red-700 border-red-200 dark:bg-red-950/50 dark:text-red-400 dark:border-red-900",
high: "border-transparent bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950/50 dark:text-orange-400 dark:border-orange-900",
medium: "border-transparent bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-950/50 dark:text-yellow-400 dark:border-yellow-900",
low: "border-transparent bg-green-100 text-green-700 border-green-200 dark:bg-green-950/50 dark:text-green-400 dark:border-green-900",
info: "border-transparent bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-900",
```

---

### Task 6: SummaryCard.tsx - categoryColors cu dark mode

- [x] 6.1 Deschide: `frontend/src/components/SummaryCard.tsx`

- [x] 6.2 Gasesceste `categoryColors` ~linia 33:

```typescript
const categoryColors: Record<RegCategory, string> = {
  TEMP: 'text-orange-600 bg-orange-50',
  SENS: 'text-purple-600 bg-purple-50',
  ALARM: 'text-red-600 bg-red-50',
  DATA: 'text-teal-600 bg-teal-50',
  POWER: 'text-amber-600 bg-amber-50',
  COOL: 'text-cyan-600 bg-cyan-50',
  INS: 'text-indigo-600 bg-indigo-50',
  OPS: 'text-slate-600 bg-slate-50',
}
```

- [x] 6.3 **INLOCUIESTE-Le** cu:

```typescript
const categoryColors: Record<RegCategory, string> = {
  TEMP: 'text-orange-600 bg-orange-50 dark:text-orange-400 dark:bg-orange-950/40',
  SENS: 'text-purple-600 bg-purple-50 dark:text-purple-400 dark:bg-purple-950/40',
  ALARM: 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-950/40',
  DATA: 'text-teal-600 bg-teal-50 dark:text-teal-400 dark:bg-teal-950/40',
  POWER: 'text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/40',
  COOL: 'text-cyan-600 bg-cyan-50 dark:text-cyan-400 dark:bg-cyan-950/40',
  INS: 'text-indigo-600 bg-indigo-50 dark:text-indigo-400 dark:bg-indigo-950/40',
  OPS: 'text-slate-600 bg-slate-50 dark:text-slate-400 dark:bg-slate-800/50',
}
```

---

### Task 7: types.ts - SEVERITY_COLORS si DATA_SOURCE_COLORS

- [x] 7.1 Deschide: `frontend/src/lib/api/types.ts`

- [x] 7.2 Gasesceste `SEVERITY_COLORS`:

```typescript
export const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  low: 'bg-green-100 text-green-700 border-green-200',
  info: 'bg-blue-100 text-blue-700 border-blue-200',
}
```

- [x] 7.3 **INLOCUIESTE-Le** cu:

```typescript
export const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200 dark:bg-red-950/50 dark:text-red-400 dark:border-red-900',
  high: 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950/50 dark:text-orange-400 dark:border-orange-900',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-950/50 dark:text-yellow-400 dark:border-yellow-900',
  low: 'bg-green-100 text-green-700 border-green-200 dark:bg-green-950/50 dark:text-green-400 dark:border-green-900',
  info: 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-900',
}
```

- [x] 7.4 Gasesceste `DATA_SOURCE_COLORS`:

```typescript
export const DATA_SOURCE_COLORS: Record<DataSource, { badge: string; text: string }> = {
  logs: {
    badge: 'bg-green-100 text-green-700 border-green-200',
    text: 'text-green-600',
  },
  inspection: {
    badge: 'bg-gray-100 text-gray-700 border-gray-200',
    text: 'text-gray-600',
  },
  combined: {
    badge: 'bg-orange-100 text-orange-700 border-orange-200',
    text: 'text-orange-600',
  },
  images: {
    badge: 'bg-blue-100 text-blue-700 border-blue-200',
    text: 'text-blue-600',
  },
}
```

- [x] 7.5 **INLOCUIESTE-Le** cu:

```typescript
export const DATA_SOURCE_COLORS: Record<DataSource, { badge: string; text: string }> = {
  logs: {
    badge: 'bg-green-100 text-green-700 border-green-200 dark:bg-green-950/40 dark:text-green-400 dark:border-green-900',
    text: 'text-green-600 dark:text-green-400',
  },
  inspection: {
    badge: 'bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800/60 dark:text-gray-300 dark:border-gray-700',
    text: 'text-gray-600 dark:text-gray-400',
  },
  combined: {
    badge: 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950/40 dark:text-orange-400 dark:border-orange-900',
    text: 'text-orange-600 dark:text-orange-400',
  },
  images: {
    badge: 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-900',
    text: 'text-blue-600 dark:text-blue-400',
  },
}
```

---

### Task 8: Layout.tsx - Refactor restul hardcodarilor

- [x] 8.1 Deschide: `frontend/src/components/Layout.tsx`

Găsește și înlocuiește după această mapare:

| Gaseste | Inlocuieste cu |
|---------|----------------|
| `bg-white` (la sidebar) | `bg-card` |
| `bg-slate-50` | `bg-muted/40` |
| `bg-slate-100` | `bg-muted` |
| `border-slate-200` | `border-border` |
| `text-slate-900` | `text-foreground` |
| `text-slate-600` | `text-muted-foreground` |
| `text-slate-500` | `text-muted-foreground` |

**Atentie:** Unele dintre acestea apar in clase multiple cum ar fi:
- `hidden lg:flex lg:flex-col lg:w-64 lg:border-r lg:border-slate-200 lg:bg-white lg:h-screen lg:sticky lg:top-0`

Cand inlocuiesti, schimba doar partea relevanta:
- `lg:border-slate-200` → `lg:border-border`
- `lg:bg-white` → `lg:bg-card`

**De asemenea, cu grija:**
- `hover:bg-slate-100` → `hover:bg-muted`
- `hover:text-slate-900` → `hover:text-foreground`

---

### Task 9: ChatMessageBubble.tsx + AIChat.tsx

- [x] 9.1 Deschide: `frontend/src/components/AIChat/ChatMessageBubble.tsx`

Inlocuiri:
| Gaseste | Inlocuieste cu |
|---------|----------------|
| `bg-slate-100 text-slate-800` | `bg-muted text-foreground` |
| `bg-purple-100` | `bg-purple-100 dark:bg-purple-900/30` |

- [x] 9.2 Verifica si `AIChat.tsx` (găsește `bg-purple-100`, `bg-slate-100`)

Inlocuiri similare:
- `bg-purple-100` → `bg-purple-100 dark:bg-purple-900/30`
- `bg-slate-100` → `bg-muted`
- `text-purple-600` → `text-purple-600 dark:text-purple-400`

- [x] 9.3 Verifica si `NaturalLanguageSummary.tsx` (acelasi pattern cu `bg-purple-100`)

---

## PHAZA 3: MAJOR REFACTOR - Pagini si Componente Mari

ACESTA ESTE CEL MAI MARE TASK. Ai grija si testeaza des.

---

### Task 10: Dashboard.tsx - Cel mai mare

**ATENTIE:** Aceasta pagina contine ~100+ de inlocuiri.

**Strategie:**
1. Inlocuieste intai toate pattern-urile SIMPLE care se potrivesc perfect
2. Pentru cele care par "specifice", lasa-le si testeaza
3. Daca ceva nu arata corect, ajusteaza

**Maparea pentru inlocuiri:**

| Caută | Înlocuiește cu |
|-------|----------------|
| `bg-white` | `bg-card` |
| `bg-slate-50/50` | `bg-muted/20` |
| `bg-slate-50` | `bg-muted/40` |
| `bg-slate-100` | `bg-muted` |
| `bg-slate-200` | `bg-border` |
| `border-slate-200` | `border-border` |
| `border-slate-300` | `border-border/80` |
| `border-dashed border-slate-300` | `border-dashed border-border/80` |
| `border-red-200 bg-red-50` | `border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-950/30` |
| `text-slate-900` | `text-foreground` |
| `text-slate-600` | `text-muted-foreground` |
| `text-slate-500` | `text-muted-foreground` |
| `hover:bg-slate-50` | `hover:bg-muted/40` |
| `bg-primary/5` | `bg-primary/10 dark:bg-primary/20` |

**Pentru culori de status (verde/rosu):**

| Caută | Înlocuiește cu |
|-------|----------------|
| `text-green-600` | `text-green-600 dark:text-green-400` |
| `text-red-600` | `text-red-600 dark:text-red-400` |
| `text-red-700` | `text-red-700 dark:text-red-400` |
| `text-orange-600` | `text-orange-600 dark:text-orange-400` |
| `text-purple-600` | `text-purple-600 dark:text-purple-400` |
| `hover:bg-red-50` | `hover:bg-red-50 dark:hover:bg-red-950/50` |
| `hover:text-red-700` | `hover:text-red-700 dark:hover:text-red-400` |

**Pentru culori hardcodate in skeleton/loading:**

Acestea sunt cam toate `bg-slate-200`, `bg-slate-100` pentru animate-pulse. In general:
- `bg-slate-100` → `bg-muted`
- `bg-slate-200` → `bg-border`

**Unde cauti in Dashboard.tsx:**
1. `EmptyStateCard` component (daca exista)
2. Toate componentele din tab-uri: Overview, Temperature, Violations, History, Rules
3. Skeleton states
4. Butoane, tabele, badge-uri

---

### Task 11: History.tsx

- [x] 11.1 Acelasi pattern ca Dashboard.tsx
- [x] 11.2 Aplica aceleasi reguli de inlocuire

---

### Task 12: Upload.tsx

- [x] 12.1 Similar, mai mic
- [x] 12.2 Inlocuiri: `bg-slate-50`, `border-slate-200` etc.

---

### Task 13: Restul componentelor

Acestea sunt componente mai mici, verifica fiecare:

| Componenta | De verificat |
|------------|--------------|
| `FileUploadZone.tsx` | `bg-slate-50`, `bg-slate-100`, `bg-slate-200`, `bg-red-50`, `border-slate-*`, `text-slate-*`, `text-cyan-600`, `text-red-500` |
| `RulesReference/RuleCard.tsx` | `bg-slate-50` |
| `RulesReference/RulesList.tsx` | Posibil |
| `RulesReference/RulesFilter.tsx` | Posibil |
| `AIAnalysis/AIAnalysisSection.tsx` | `bg-slate-50`, `text-slate-*`, `text-purple-500` |
| `AIAnalysis/ActionPlanCard.tsx` | `hover:bg-slate-50` |
| `AIAnalysis/InsightsList.tsx` | `hover:bg-slate-50`, `bg-slate-200`, `bg-red-500`, `bg-orange-500`, `bg-yellow-500` → pt acestea foloseste `dark:bg-red-600`, `dark:bg-orange-600`, `dark:bg-yellow-500` |
| `AIAnalysis/PredictionsList.tsx` | `bg-slate-200`, `bg-red-500`, `bg-orange-500`, `bg-red-50`, `border-red-100` |
| `AIAnalysis/RiskOverviewCard.tsx` | `bg-red-50`, `bg-slate-50` |
| `ComplianceScore.tsx` | `bg-slate-50`, `bg-red-50`, toate skeleturile |
| `PassFailSummary.tsx` | `bg-slate-100`, `bg-orange-500`, `bg-red-500`, toate skeleturile |
| `ViolationsTable.tsx` | `bg-slate-100`, `bg-slate-50`, `border-slate-200`, `text-slate-*`, status colors (open: `bg-red-100` etc.) |
| `TemperatureChart.tsx` | IMPORTANT - Recharts. Vezi taskul urmator. |
| `ErrorState.tsx` | `bg-red-100`, `bg-slate-100`, `text-slate-*` |
| `DataModeBanner.tsx` | `bg-slate-50`, `border-slate-200` |
| `ui/*.tsx` | Deja folosesc CSS vars, ar trebui sa fie ok. Verifica doar `skeleton.tsx` daca e hardcodat `bg-slate-200`. |

---

### Task 14: TemperatureChart.tsx (Recharts)

**Problema:** Recharts foloseste culoari inline, nu stie de `dark:` classes.

**Solutii:**

**Optiunea A (mai simpla):** Foloseste `useTheme()` si transmite culorile in functie de tema

Unde sunt culorile in TemperatureChart? Gaseste-le:
- Probabil `stroke="#..."` sau `fill="#..."`
- Sau culori pentru safe range, etc.

**Exemplu de abordare:**

```typescript
import { useTheme } from '@/lib/context/ThemeContext'

// In componenta:
const { theme } = useTheme()

const CHART_COLORS = {
  line: theme === 'dark' ? '#22d3ee' : '#0891b2',  // cyan-400 vs cyan-600
  safeRange: theme === 'dark' ? '#16a34a' : '#22c55e',
  // ...
}
```

**Optiunea B:** Defineste variabile CSS si le citeste folosind `getComputedStyle`

Mai complex, dar mai "corect" dpdv arhitectural.

**RECOMANDARE:** Foloseste Optiunea A pentru simplitate. Cand ajungi la acest task, analizeaza ce culori sunt hardcodate in Recharts si aplica un sistem similar.

**De asemenea:**
- `bg-slate-50`, `bg-slate-100`, `bg-slate-200` din jurul graficului - inlocuieste-le cu varianta standard
- `text-slate-600`, `text-slate-500` - la fel

---

## PHAZA 4: TESTARE FINALA

- [x] Testeaza ca toggle functioneaza corect in ambele sensuri
- [x] Refresh pagina - tema ramane salvata? (localStorage)
- [x] Sterge localStorage.getItem('theme') si refresh - se incarca corect conform `prefers-color-scheme`?
- [x] Testeaza PAGINA de Dashboard cu si fara date
- [x] Testeaza PAGINA de History
- [x] Testeaza PAGINA de Upload
- [x] Testeaza AI Chat area
- [x] Testeaza Rules Reference
- [x] Testeaza Temperature Chart (atentie la Recharts)
- [x] Testeaza ca LIGHT MODE nu s-a stricat nimic!
- [x] Verifica ca toate severity badges arata bine in ambele moduri
- [x] Verifica ca toate category cardurile arata bine
- [x] Verifica ca nu ramine niciun `bg-white` sau `text-slate-900` nerezolvat

---

## REZUMAT

Ordine recomandata de executie:
1. Tasks 1-4 → Infrastructura functionala
2. Tasks 5-9 → Core components
3. Tasks 10-13 → Major refactor (incepe cu cele mai mici)
4. Task 14 → Charts
5. Testare finala
