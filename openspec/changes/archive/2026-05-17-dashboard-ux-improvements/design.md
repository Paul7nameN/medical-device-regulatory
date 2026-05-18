## Context

Acest change se bazează pe probleme UX identificate în timpul explorării:

### Problema detaliată: Layout când `!hasData`

```
┌─────────────────────────────────────────────────────────────────────┐
│              PROBLEMA ACTUALĂ (când nu ai date)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Ordinea componentelor în Dashboard:                               │
│                                                                     │
│  1. Header (breadcrumbs + notifications)                           │
│  2. EmptyStateCard (PRIMUL)                                        │
│     - Title: "No Analysis Data"                                    │
│     - Description: "Upload device log files..."                    │
│     - Button: "Upload Logs" → actionTo="/" (INUTIL!)             │
│  3. Page Title (AL DOILEA)                                         │
│     - "Analysis Hub" + subtitle                                    │
│  4. Tabs (INUTILE când nu ai date)                                 │
│  5. EmptyStateCard (AL DOILEA, cu același text!)                  │
│     - Title: "No compliance data available"                        │
│     - Description: "Upload device log files..."                    │
│     - FileUploadZone (PREA JOS, trebuie scroll!)                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Problema detaliată: Sidebar

```
┌─────────────────────────────────────────────────────────────────────┐
│              SIDEBAR - COMPORTAMENT DIFERIT PE ECRANE             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PE MOBIL (sub 1024px):                                            │
│  - Sidebar = ascuns                                                │
│  - Există butonul [Menu] care deschide un Sheet (drawer)          │
│  - Componenta: <MobileNav> cu <Sheet>                             │
│                                                                     │
│  PE DESKTOP (peste 1024px):                                        │
│  - Sidebar = mereu deschis (256px wide)                           │
│  - NU există buton [Menu] (are lg:hidden)                          │
│  - Componenta: <Sidebar> cu flex lg:flex etc.                     │
│                                                                     │
│  PROBLEMA:                                                          │
│  - Butonul [Menu] este vizibil DOAR pe mobil                      │
│  - Utilizatorul vrea toggle pe TOATE ecranele                     │
│  - Sidebar-ul vrea să fie ÎNCHIS by default                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Goals / Non-Goals

**Goals:**
1. ✅ Layout DUAL: când `!hasData` → DOAR Upload Zone la TOP
2. ✅ Layout DUAL: când `hasData` → layout normal dar cu sidebar consistent
3. ✅ Sidebar = Sheet pe TOATE ecranele (nu doar mobil)
4. ✅ Butonul [Menu] vizibil pe toate ecranele
5. ✅ Fără informație redundantă
6. ✅ Butonul de upload vizibil imediat, fără scroll

**Non-Goals:**
1. ❌ Nu rescriem `FileUploadZone` (este deja funcțional)
2. ❌ Nu schimbăm logica din context
3. ❌ Nu schimbăm flow-ul când avem deja date (doar afișajul)
4. ❌ Nu adăugăm funcționalități noi

---

## Decisions

### Decizia 1: Cum implementăm Layout DUAL?

**Opțiuni considerate:**

| Opțiune | Descriere | Pro | Contra |
|---------|-----------|-----|--------|
| **A** | `{!hasData ? <EmptyLayout /> : <NormalLayout />}` | Curat, ușor de întreținut | Trebuie să mutăm codul |
| **B** | Conditional rendering pe componente | Mai puțin restructurare | Componentele devin complexe |
| **C** | O pagină nouă `EmptyPage` redirectată | Separat clar | Mai multe rute, complexity |

**Decizie: Opțiunea A**

**Rationale:**
- Când `!hasData`, afișăm un layout complet diferit (fără tab-uri, fără informații redundante)
- Când `hasData`, afișăm layout-ul existent
- Ușor de întreținut și de înțeles

**Structură în Dashboard.tsx:**
```typescript
if (!hasData) {
  return (
    <div className="min-h-screen flex flex-col">
      <HeaderForEmptyState />
      <main className="flex-1 flex items-center justify-center p-4">
        <UploadZoneCentered />
      </main>
    </div>
  )
}

// Altfel, layout normal...
return (
  <div className="space-y-6">
    <PageTitle />
    <Tabs>...</Tabs>
  </div>
)
```

---

### Decizia 2: Cum facem Sidebar consistent?

**Opțiuni:**

| Opțiune | Descriere | Pro | Contra |
|---------|-----------|-----|--------|
| **A** | Folosim DOAR Sheet (MobileNav) pe toate ecranele | Consistent, puțin cod | Nu mai avem sidebar permanent |
| **B** | Collapsible sidebar (deschis/închis) | Flexibil | Mai mult cod |
| **C** | Doar eliminăm `lg:hidden` de la butonul Menu | Simplu | Sidebar-ul rămâne permanent |

**Decizie: Opțiunea C + ajustare**

**Rationale:**
- Cea mai simplă soluție pentru început
- Eliminăm `lg:hidden` de la butonul Menu
- Astfel, butonul devine vizibil și pe desktop
- Sidebar-ul rămâne așa cum e, dar utilizatorul poate să vadă Menu Button

**Mai târziu** (într-o altă schimbare):
- Putem face sidebar-ul collapsible
- Sau putem folosi Sheet pe toate ecranele

**Modificări minime în Layout.tsx:**
```typescript
// ÎNAINTE (doar mobil):
className="lg:hidden p-2 hover:bg-slate-100..."

// ACUM (toate ecranele):
className="p-2 hover:bg-slate-100..."
```

---

### Decizia 3: Ce facem cu EmptyState din celelalte tab-uri?

Problema:
- Temperature tab: `EmptyStateCard` cu buton `Link to="/"`
- Violations tab: același
- History tab: același

Soluții:

| Opțiune | Descriere |
|---------|-----------|
| **A** | Înlocuim `Link` cu `onClick={() => setActiveTab('overview')}` |
| **B** | Eliminăm butonul complet, lăsăm doar text |
| **C** | Când `!hasData`, nu afișăm deloc aceste tab-uri (sau le dezactivăm) |

**Decizie:**
- Pentru acest change: **Opțiunea A** (minimă, dar funcțională)
- Viitor: Odată ce avem Layout DUAL, când `!hasData` nici nu ajungem să afișăm tab-urile

---

## Architecture / Component Diagram

### DUPĂ SCHIMBARE

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYOUT DUAL - CÂND NU AI DATE                  │
│                    (!hasData === true)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Header (simplificat)                                        │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │ 🛡️ MED-THERM                [Menu] [Notifications] │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Main (centrat, pe toată înălțimea):                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │              ┌───────────────────────────┐                 │   │
│  │              │                           │                 │   │
│  │              │   📁 Upload Zone          │                 │   │
│  │              │                           │                 │   │
│  │              │   Title: "Upload files    │                 │   │
│  │              │   to start compliance     │                 │   │
│  │              │   analysis"               │                 │   │
│  │              │                           │                 │   │
│  │              │   [ DRAG & DROP ZONE ]   │                 │   │
│  │              │   [ Butoane vizibile ]    │                 │   │
│  │              │                           │                 │   │
│  │              └───────────────────────────┘                 │   │
│  │                                                             │   │
│  │  (NICIUN TAB, NICIUN TITLU DUBLU, NICIUN                 │   │
│  │   EMPTYSTATE REDUNDANT)                                    │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    LAYOUT DUAL - CÂND AI DATE                      │
│                    (!hasData === false)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Layout CA ACUM, dar cu:                                            │
│  - Butonul [Menu] vizibil și pe desktop                            │
│  - Eventual (viitor): sidebar collapsible sau Sheet                │
│                                                                     │
│  ┌──────────────┬────────────────────────────────────────────────┐ │
│  │  Sidebar     │  Header (cu [Menu] vizibil)                    │ │
│  │  (sau Sheet) │                                                │ │
│  │              │  Page Title: "Analysis Hub"                   │ │
│  │              │                                                │ │
│  │  📊 Home     │  [Overview] [Temperature] [Violations] ...   │ │
│  │              │                                                │ │
│  │              │  ...toate componentele, scorul, etc.         │ │
│  │              │                                                │ │
│  └──────────────┴────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Risks / Trade-offs

### Riscul 1: Header diferit pentru cele două stări

**Descriere:**
- Când `!hasData`, Header-ul trebuie să arate diferit (fără breadcrumb, cu Logo + Title)
- Când `hasData`, Header-ul este așa cum e acum

**Mitigare:**
- Putem crea două componente separate: `HeaderEmptyState` și `HeaderNormal`
- Sau putem pasa un prop `isCompact` sau similar
- Sau, și mai bine: Layout-ul complet (inclusiv Header) este diferit când `!hasData`

**Decizie:**
- Folosim return condițional la începutul `DashboardPage`:
  ```typescript
  if (!hasData) {
    return <EmptyDashboard />
  }
  return <NormalDashboard />
  ```

### Riscul 2: Sidebar-ul rămâne permanent pe desktop

**Descriere:**
- Pentru acest change, doar eliminăm `lg:hidden` de la buton
- Sidebar-ul rămâne așa cum e (mereu deschis)

**Trade-off:**
- ✅ Simplu, puțin cod
- ⚠️ Nu rezolvă complet cerința utilizatorului ("sidebar închis by default")

**Plan:**
- Acest change: doar butonul Menu vizibil
- Următorul change (dacă este nevoie): sidebar collapsible sau Sheet

---

## Migration Plan

### Pas 1: Layout.tsx - Butonul Menu pe toate ecranele

**Fișier:** `frontend/src/components/Layout.tsx`

**Locație:** Butonul Menu din `Header` (liniile ~227-233)

**Acțiune:**
Eliminăm `lg:hidden` din className:

```typescript
// ÎNAINTE:
<button
  onClick={onMenuClick}
  className="lg:hidden p-2 hover:bg-slate-100 rounded-lg touch-target"
  ...
>
  <Menu className="h-5 w-5" />
</button>

// DUPĂ:
<button
  onClick={onMenuClick}
  className="p-2 hover:bg-slate-100 rounded-lg touch-target"
  ...
>
  <Menu className="h-5 w-5" />
</button>
```

### Pas 2: Dashboard.tsx - Layout DUAL

**Fișier:** `frontend/src/pages/Dashboard.tsx`

**Acțiune:**
Adăugăm un return condițional LA ÎNCEPUTUL funcției `DashboardPage`:

```typescript
export function DashboardPage({ isLoading = false }: DashboardPageProps) {
  const navigate = useNavigate()
  const { hasData, ... } = useAnalysis()

  // LAYOUT DUAL: Cand nu avem date, afisam DOAR Upload Zone centrat
  if (!hasData && !isAnalyzing) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        {/* Header simplificat - similar cu cel din Layout, dar fara breadcrumb */}
        <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-lg border-b border-slate-200">
          <div className="flex items-center justify-between px-4 h-14">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              <span className="font-semibold text-slate-900 font-heading">
                MED-THERM
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" className="h-9 w-9 touch-target">
                <AlertTriangle className="h-5 w-5 text-slate-500" />
              </Button>
            </div>
          </div>
        </header>

        {/* Main content centrat */}
        <main className="flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-8">
          <div className="w-full max-w-3xl">
            <div className="text-center mb-6">
              <h2 className="text-xl font-semibold text-slate-900 font-heading mb-2">
                Upload files to start compliance analysis
              </h2>
              <p className="text-sm text-slate-500">
                Drag and drop device log files or chart images below
              </p>
            </div>
            
            <FileUploadZone
              onUploadComplete={() => {}}
              maxFiles={10}
              maxSize={50 * 1024 * 1024}
            />
          </div>
        </main>

        {/* Footer simplu */}
        <footer className="border-t border-slate-200 bg-white p-4 text-center">
          <p className="text-xs text-slate-500">
            MED-THERM Compliance Engine v0.1.0
          </p>
        </footer>
      </div>
    )
  }

  // Daca avem date, layout normal...
  return (
    <div className="space-y-6">
      {/* Tot codul existent aici */}
    </div>
  )
}
```

**Important:**
- Trebuie să importăm componentele necesare în noua secțiune: `Shield`, `AlertTriangle`, `Button`, etc.
- Acestea sunt deja importate, dar trebuie să fim siguri

### Pas 3: Dashboard.tsx - Îmbunătățim butoanele EmptyState

**Acțiune:**
Înlocuim `Link to="/"` cu `onClick={() => setActiveTab('overview')}`:

```typescript
// Trebuie sa modificam componenta EmptyStateCard pentru a accepta si onClick
// SAU sa inlocuim Link cu un Button care apeleaza setActiveTab

// Varianta mai buna: Modificam EmptyStateCard
function EmptyStateCard({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionTo,
  onActionClick,  // NOU
}: {
  icon: React.ElementType
  title: string
  description: string
  actionLabel?: string
  actionTo?: string
  onActionClick?: () => void  // NOU
}) {
  // Daca avem onActionClick, folosim un Button cu onClick
  // Altfel, daca avem actionTo, folosim Link
  
  return (
    ...
    {actionLabel && (
      onActionClick ? (
        <Button onClick={onActionClick} ...>
          ...
        </Button>
      ) : actionTo ? (
        <Link to={actionTo}>
          <Button ...>...</Button>
        </Link>
      ) : null
    )}
  )
}
```

**Apoi, folosirea:**
```typescript
// In Temperature tab:
<EmptyStateCard
  ...
  actionLabel="Go to Overview"
  onActionClick={() => setActiveTab('overview')}
/>

// In Violations tab:
<EmptyStateCard
  ...
  actionLabel="Go to Overview"
  onActionClick={() => setActiveTab('overview')}
/>

// In History tab:
<EmptyStateCard
  ...
  actionLabel="Go to Overview"
  onActionClick={() => setActiveTab('overview')}
/>
```

---

## Open Questions

1. **Vrem să schimbăm și Header-ul din Layout.tsx pentru a fi consistent?**
   - Acum Header are breadcrumb pe desktop
   - Vrem să îl schimbăm cu Logo + Title pe toate ecranele?
   - Sau rămâne așa cum e?

2. **Vrem să facem sidebar-ul complet închis by default în schimbarea asta?**
   - Sau doar butonul Menu vizibil?
   - Sidebar collapsibil ar necesita mai mult cod

3. **EmptyStateCard modificată:**
   - Vrem să modificăm componenta pentru a accepta `onActionClick`?
   - Sau să folosim o abordare diferită?

**Răspunsuri implicite (dacă nu se specifică altceva):**
1. Header din Layout rămâne așa cum e (breadcrumb). Doar în Empty Dashboard vom avea un header simplificat.
2. Doar butonul Menu devine vizibil. Sidebar-ul rămâne așa cum e pentru acest change.
3. Modificăm `EmptyStateCard` pentru a accepta `onActionClick`.
