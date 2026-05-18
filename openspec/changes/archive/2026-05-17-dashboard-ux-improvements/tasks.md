## 1. Layout.tsx - Butonul Menu vizibil pe toate ecranele

- [x] 1.1 Deschide `frontend/src/components/Layout.tsx`
- [x] 1.2 Găsește butonul Menu din componenta `Header` (liniile ~227-233)
- [x] 1.3 Identifică `className="lg:hidden p-2 hover:bg-slate-100..."`
- [x] 1.4 **ELIMINĂ** `lg:hidden` din className
- [x] 1.5 Verifică că acum butonul are doar `className="p-2 hover:bg-slate-100..."`
- [x] 1.6 Testează: pe desktop, acum ar trebui să vezi butonul [Menu] lângă Logo

---

## 2. Dashboard.tsx - Modificăm EmptyStateCard pentru a accepta onClick

- [x] 2.1 Deschide `frontend/src/pages/Dashboard.tsx`
- [x] 2.2 Găsește componenta `EmptyStateCard` (începe la ~linia 57)
- [x] 2.3 Modifică interfața (props) pentru a accepta și `onActionClick`:

```typescript
// INAINTE:
function EmptyStateCard({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionTo,
}: {
  icon: React.ElementType
  title: string
  description: string
  actionLabel?: string
  actionTo?: string
})

// DUPA:
function EmptyStateCard({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionTo,
  onActionClick,
}: {
  icon: React.ElementType
  title: string
  description: string
  actionLabel?: string
  actionTo?: string
  onActionClick?: () => void
})
```

- [x] 2.4 Modifică logica din interior pentru a folosi `onActionClick`:

```typescript
// INAINTE:
{actionLabel && actionTo && (
  <Link to={actionTo}>
    <Button ...>
      <Upload ... />
      {actionLabel}
    </Button>
  </Link>
)}

// DUPA:
{actionLabel && (
  onActionClick ? (
    <Button onClick={onActionClick} size="sm" className="touch-target">
      <Upload className="h-4 w-4 mr-2" />
      {actionLabel}
    </Button>
  ) : actionTo ? (
    <Link to={actionTo}>
      <Button size="sm" className="touch-target">
        <Upload className="h-4 w-4 mr-2" />
        {actionLabel}
      </Button>
    </Link>
  ) : null
)}
```

- [x] 2.5 Asigură-te că importul pentru `Button` există (deja ar trebui)

---

## 3. Dashboard.tsx - Actualizăm folosirile EmptyStateCard din celelalte tab-uri

- [x] 3.1 Găsește `EmptyStateCard` din **Temperature** tab (liniile ~512-520)
- [x] 3.2 Înlocuiește:
  ```typescript
  // INAINTE:
  actionLabel="Upload Files"
  actionTo="/"
  
  // DUPA:
  actionLabel="Go to Overview"
  onActionClick={() => setActiveTab('overview')}
  ```

- [x] 3.3 Găsește `EmptyStateCard` din **Violations** tab (liniile ~714-722)
- [x] 3.4 Înlocuiește același pattern:
  ```typescript
  actionLabel="Go to Overview"
  onActionClick={() => setActiveTab('overview')}
  ```

- [x] 3.5 Găsește `EmptyStateCard` din **History** tab (liniile ~790-798)
- [x] 3.6 Înlocuiește același pattern:
  ```typescript
  actionLabel="Go to Overview"
  onActionClick={() => setActiveTab('overview')}
  ```

- [x] 3.7 Verifică că `setActiveTab` există în scope (deja există ca `const [activeTab, setActiveTab] = useState('overview')`)

---

## 4. Dashboard.tsx - Layout DUAL (cel mai important task)

Acest task adaugă un layout complet diferit când `!hasData`.

- [x] 4.1 Deschide `frontend/src/pages/Dashboard.tsx`
- [x] 4.2 La începutul funcției `DashboardPage`, DUPĂ ce extrage toate variabilele din context (după `const {...} = useAnalysis()`), adaugă un return condițional:

**IMPORTANT:** Acest return trebuie să fie DUPĂ toate importurile și variabilele, dar ÎNAINTE de orice useMemo sau alte calcule.

Mai bine mutăm acest return LA ÎNCEPUT, chiar după ce avem `hasData` și `isAnalyzing`:

```typescript
export function DashboardPage({ isLoading = false }: DashboardPageProps) {
  const navigate = useNavigate()
  const [selectedCategory, setSelectedCategory] = useState<RegCategory | null>(null)
  const [activeTab, setActiveTab] = useState('overview')
  const {
    latestAnalysis,
    hasData,
    isAnalyzing,
    error,
    clearError,
    analysisHistory,
    switchAnalysis,
    removeAnalysis,
    clearHistory,
    activeAnalysisIndex,
  } = useAnalysis()

  // ============================================
  // LAYOUT DUAL: Cand nu avem date, afisam doar Upload Zone centrat
  // ============================================
  if (!hasData && !isAnalyzing) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        {/* Header simplificat */}
        <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-lg border-b border-slate-200">
          <div className="flex items-center justify-between px-4 h-14">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              <span className="font-semibold text-slate-900 font-heading">
                MED-THERM
              </span>
            </div>
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
          </div>
        </header>

        {/* Main content - Upload Zone centrat */}
        <main className="flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-8">
          <div className="w-full max-w-3xl">
            <div className="text-center mb-6">
              <h2 className="text-xl font-semibold text-slate-900 font-heading mb-2">
                Upload files to start compliance analysis
              </h2>
              <p className="text-sm text-slate-500">
                Drag and drop device log files (.txt) or chart images (.png, .jpg) below
              </p>
            </div>
            
            <FileUploadZone
              onUploadComplete={() => {}}
              maxFiles={10}
              maxSize={50 * 1024 * 1024}
            />
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200 bg-white p-4 text-center">
          <p className="text-xs text-slate-500">
            MED-THERM Compliance Engine v0.1.0
          </p>
        </footer>
      </div>
    )
  }

  // ============================================
  // Cand avem date, continuam cu layout-ul normal...
  // ============================================
  
  // TOATE useMemo-urile si restul calculelor vin AICI
  // (ele depind de hasData, latestAnalysis, etc.)
```

- [x] 4.3 Asigură-te că toate importurile necesare există:
  - `Shield` (deja importat din lucide-react)
  - `AlertTriangle` (deja importat)
  - `Button` (deja importat)
  - `FileUploadZone` (deja importat)

- [x] 4.4 **IMPORTANT:** Mută `const showLoading = isLoading || isAnalyzing` și toate useMemo-urile DUPĂ acel return condițional (altfel vor avea eroare dacă `latestAnalysis` este null)

**Alternativă (mai sigură):**
Păstrăm layout-ul normal existent, dar în Overview tab, când `!complianceScore`, afișăm DOAR `FileUploadZone` (fără acel `EmptyStateCard` de deasupra tab-urilor).

Aceasta presupune că eliminăm acel `EmptyStateCard` care apare ÎNAINTE de page title și tabs.

**Unde este acel EmptyStateCard?**
Este în `Layout.tsx`? Nu, este probabil un card care apare când...

Așteaptă, hai să analizăm mai bine:
- Userul spune că are 2 EmptyState: unul deasupra tab-urilor, unul în Overview
- Cel de deasupra tab-urilor trebuie eliminat CÂND `!hasData`

Deci, poate o abordare mai simplă:
1. Eliminăm acel prim `EmptyStateCard` care apare înainte de page title
2. Când `!hasData`, Overview tab afișează `FileUploadZone` (cum deja am făcut)

Dar userul vrea și mai mult: ca când `!hasData`, să NU afișăm deloc tab-urile și titlurile redundante.

Deci, abordarea corectă este cea cu **return condițional la început**.

- [x] 4.5 Verifică că tot codul care depinde de `latestAnalysis` sau alte valori care pot fi null sunt DUPĂ acel return condițional (sau sunt protejate de condiții)

---

## 5. Loading state special pentru primul upload

(Acest task a fost deja făcut în schimbarea anterioară, dar verificăm)

- [x] 5.1 Când `isAnalyzing && !hasData`, ar trebui să afișăm un loading clar, nu doar skeleton
- [x] 5.2 Verifică că în Overview tab există logica:
  ```typescript
  {isAnalyzing && !hasData ? (
    <Card...>
      <Loader2...>
      "Analyzing your files..."
    </Card>
  ) : showLoading ? (
    <ComplianceScoreSkeleton />
  ) : !complianceScore ? (
    <Card...>
      <FileUploadZone...>
    </Card>
  ) : (
    <ComplianceScore...>
  )}
  ```

- [x] 5.3 Dacă nu există, adaugă această logica (sau verifică că a fost adăugată în schimbarea anterioară)

---

## 6. Testare și verificare

### 6.1 Testează butonul Menu pe desktop
- [x] 6.1.1 Pe ecran mare (>1024px), ar trebui să vezi butonul [Menu] în stânga Logo-ului/breadcrumb-ului
- [x] 6.1.2 Butonul ar trebui să deschidă Sheet-ul (la fel ca pe mobil)
- [x] 6.1.3 Sidebar-ul din stânga rămâne așa cum e (pentru acest change)

### 6.2 Testează Layout DUAL când `!hasData`
- [x] 6.2.1 Șterge localStorage sau "Clear All" din History
- [x] 6.2.2 Reîncarcă pagina
- [x] 6.2.3 **NU** ar trebui să vezi:
  - Niciun EmptyState cu "No Analysis Data"
  - Niciun buton "Upload Logs" inutil
  - Niciun tab
  - Niciun titlu "Analysis Hub" dublu
- [x] 6.2.4 **AR TREBUI** să vezi:
  - Un header simplu: Logo + Notifications
  - Un titlu: "Upload files to start compliance analysis"
  - **FileUploadZone LA TOP, fără scroll necesar**
  - Butonul de upload este IMEDIAT vizibil

### 6.3 Testează butoanele EmptyState din celelalte tab-uri
- [x] 6.3.1 Când AI date, dar mergi pe un tab care nu are date (ex: Temperature tab dacă ai încărcat doar o imagine fără date de temperatură)
- [x] 6.3.2 Butonul "Go to Overview" ar trebui să TE DUCĂ pe tab-ul Overview (nu să facă refresh sau link către aceeași pagină)
- [x] 6.3.3 Verifică pentru Temperature, Violations, History

### 6.4 Testează flow-ul complet
- [x] 6.4.1 Pornire cu `!hasData`: vezi DOAR Upload Zone
- [x] 6.4.2 Uploadează un fișier: vezi loading clar ("Analyzing your files...")
- [x] 6.4.3 După terminare: pagina se actualizează automat la layout-ul NORMAL (cu tabs, scor, etc.)
- [x] 6.4.4 Overview tab afișează scorul
- [x] 6.4.5 Butonul [Menu] funcționează pe desktop

---

## Rezumat Task-uri

**Ordine recomandată:**
1. **Task 1** (Layout.tsx): Butonul Menu pe toate ecranele - cel mai simplu
2. **Task 2** (Dashboard.tsx): Modificăm EmptyStateCard pentru a accepta onClick
3. **Task 3** (Dashboard.tsx): Actualizăm folosirile din celelalte tab-uri
4. **Task 4** (Dashboard.tsx): Layout DUAL - cel mai important, schimbă complet experiența când `!hasData`
5. **Task 5**: Verificare loading state
6. **Task 6**: Testare completă

**Modificările făcute vor rezolva:**
- ✅ Sidebar toggle pe toate ecranele (doar butonul, sidebar rămâne permanent)
- ✅ Zero informație redundantă când `!hasData`
- ✅ Butonul de upload vizibil IMEDIAT, fără scroll
- ✅ Butoanele din celelalte tab-uri acum funcționează (te duc pe Overview)
- ✅ Layout simplu și clar când nu ai date
