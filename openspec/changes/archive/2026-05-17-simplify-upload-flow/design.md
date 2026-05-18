## Context

Acest change se bazează pe o problemă UX identificate în timpul explorării:

### Flow-ul curent și problemele lui

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLOW ACTUAL (PROBLEMATIC)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Utilizatorul deschide aplicația                            │
│     ↓                                                           │
│  2. Este pe HOME, vede:                                        │
│     ┌─────────────────────────────────────────────────────┐   │
│     │  📊 No compliance data available                     │   │
│     │  Upload device log files to generate analysis.      │   │
│     │                                                     │   │
│     │  [ Upload Logs ] ← BUTON, NU ZONĂ DE UPLOAD       │   │
│     └─────────────────────────────────────────────────────┘   │
│     ↓ click buton                                               │
│  3. Este REDIRECȚIONAT pe /upload (PAGINĂ NOUĂ)              │
│     ↓                                                           │
│  4. Uploadează fișiere pe pagina separată                      │
│     ↓                                                           │
│  5. Upload terminat → așteaptă 3 SECUNDE                      │
│     ↓                                                           │
│  6. Este REDIRECȚIONAT ÎNAPOI pe HOME                          │
│                                                                 │
│  🔴 PROBLEME:                                                   │
│  - De ce trebuie să PLECE de acasă ca să adauge date ÎN CASĂ?│
│  - Nu există NICIO legătură vizuală între EmptyState și       │
│    rezultatul care va apărea                                    │
│  - 2 redirecționări pentru o acțiune simplă                    │
│  - Pe pagina /upload, utilizatorul NU știe ce se întâmplă     │
│    cu datele după upload                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Unde sunt componentele acum

| Component | Locație | Funcție |
|-----------|---------|---------|
| `Sidebar` | `Layout.tsx` lines 29-42 | Are: Home, Upload |
| `EmptyStateCard` | `Dashboard.tsx` lines 47-79 | Card cu icon, text, și UN BUTON către `/upload` |
| `FileUploadZone` | `components/FileUploadZone.tsx` | Zona completă de drag&drop cu progress, etc. |
| `UploadPage` | `pages/Upload.tsx` | Pagina separată cu FileUploadZone + info |
| `useAnalysis` | `context/AnalysisContext.tsx` | State global: are `hasData`, `isAnalyzing`, etc. |

---

## Goals / Non-Goals

**Goals (ce vom face):**
1. ✅ Eliminăm "Upload" din sidebar (rămâne doar "Home")
2. ✅ Înlocuim `EmptyStateCard` din Dashboard cu `FileUploadZone` COMPLETĂ
3. ✅ Asigurăm că după upload, pagina se actualizează AUTOMAT (fără redirecționări)
4. ✅ Ruta `/upload` devine un redirect către `/` (pentru compatibilitate)
5. ✅ Toate tab-urile care aveau EmptyState acum afișează aceeași zonă de upload

**Non-Goals (ce NU vom face):**
1. ❌ NU rescriem `FileUploadZone` (este deja funcțională)
2. ❌ NU schimbăm logica de upload din backend sau din context
3. ❌ NU ștergem obligatoriu `Upload.tsx` (îl putem lăsa ca fallback)
4. ❌ NU adăugăm funcționalități noi de upload (doar mutăm unde apare)
5. ❌ NU modificăm flow-ul când avem deja date (doar cand `!hasData`)

---

## Decisions

### Decizia 1: Unde afișăm zona de upload în Dashboard?

**Context:**
Dashboard are **5 taburi**, fiecare cu propriul `EmptyStateCard`:
1. **Overview** - `ComplianceScore` empty → afișează buton
2. **Temperature** - `TemperatureChart` empty → afișează buton
3. **Violations** - `ViolationsTable` empty → afișează buton
4. **History** - `analysisHistory.length === 0` → afișează buton
5. **Rules** - NU are empty state (mereu afișează regulile)

**Opțiuni considerate:**

| Opțiune | Descriere | Pro | Contra |
|---------|-----------|-----|--------|
| **A** | Doar tab-ul **Overview** are `FileUploadZone` completă | Centralizat, ușor de întreținut | Alte taburi încă au butoane |
| **B** | Toate tab-urile cu EmptyState au **același** `FileUploadZone` | Consistență | Cod duplicat sau componentă complexă |
| **C** | Doar Overview are upload zone, restul redirectează/conțin link | Echilibru | Puțin inconsistenta |

**Decizie: Opțiunea A (cu modificare)**

**Rationale:**
1. **Overview** este primul tab, cel pe care aterizează utilizatorul
2. Dacă `!hasData`, celelalte taburi nu au sens să fie "active" într-un fel
3. Simplu și clar: "Dacă nu ai date, aici (pe prima pagină) încarci"

**Detalii implementare:**
- Tab **Overview**: Înlocuiește `EmptyStateCard` cu `FileUploadZone`
- Tab-urile **Temperature**, **Violations**, **History**: Păstrează `EmptyStateCard` dar:
  - Fie `actionTo="/"` (merge acasă unde este upload)
  - Sau afișează un text mai clar: "Go to Overview to upload files"

### Decizia 2: Ce facem cu pagina `Upload.tsx` și ruta `/upload`?

**Opțiuni:**

| Opțiune | Descriere | Pro | Contra |
|---------|-----------|-----|--------|
| **A** | Ștergem complet `Upload.tsx` și ruta | Curat, nimic de întreținut | Rumpe link-urile vechi, bookmark-urile |
| **B** | Redirecționăm `/upload` → `/` (Home) | Compatibilitate maximă | Puțin cod "mort" |
| **C** | Păstrăm pagina dar o ascundem din navigare | Fallback pentru API-uri | Dezordine, posibila confuzie |

**Decizie: Opțiunea B**

**Rationale:**
- Aplicația există de ceva timp, poate există link-uri sau bookmark-uri
- Redirecționarea este neinvazivă și intuitivă
- Viitor: dacă suntem siguri că nimeni nu o folosește, o ștergem

**Implementare în `App.tsx`:**
```typescript
// INLOCUIESTE:
<Route path="/upload" element={<UploadPage />} />

// CU:
<Route path="/upload" element={<Navigate to="/" replace />} />
```

### Decizia 3: Cum gestionăm starea de uploading în Dashboard?

**Context:**
`FileUploadZone` primește un callback `onUploadComplete`.
`useAnalysis` are:
- `hasData` - boolean
- `isAnalyzing` - boolean
- `latestAnalysis` - datele

**Flux dorit:**
```
!hasData
    ↓
afișează FileUploadZone
    ↓
utilizatorul uploadează
    ↓
onUploadComplete este apelat
    ↓
AnalysisContext se actualizează AUTOMAT
    ↓
hasData devine true
    ↓
Dashboard re-randează cu DATELE (nu mai afișează upload)
```

**Decizie:**
Nu avem nevoie de logică suplimentară!
- `FileUploadZone` folosește aceeași logică (apelează aceleași funcții din context)
- După upload, `hasData` devine `true`
- Componenta se re-randează automat

**Doar trebuie să ne asigurăm:**
Când `isAnalyzing === true` (upload în progres), să NU afișăm din nou EmptyState. Sau să afișăm un loading state.

---

## Architecture / Component Diagram

### DUPĂ SCHIMBARE

```
┌─────────────────────────────────────────────────────────────────────┐
│                           LAYOUT                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐                                                    │
│  │   SIDEBAR    │                                                    │
│  ├──────────────┤                                                    │
│  │              │                                                    │
│  │  ◉ Home      │  ← DOAR ACUM (Upload a dispărut)                 │
│  │              │                                                    │
│  └──────────────┘                                                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         DASHBOARD                                    │
│                                                                     │
│  Stări posibile:                                                     │
│                                                                     │
│  ═══════════════════════════════════════════════════════════════   │
│  STARE 1: !hasData && !isAnalyzing                                  │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                     │
│  Tab: Overview ████  Temp  Viol  Hist  Rules                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │   📁 DRAG & DROP FILES HERE sau click to browse            │   │
│  │                                                             │   │
│  │   ┌─────────────────────────────────────────────────────┐ │   │
│  │   │                                                     │ │   │
│  │   │  .txt  .log  .csv  .png  .jpg  .pdf              │ │   │
│  │   │                                                     │ │   │
│  │   └─────────────────────────────────────────────────────┘ │   │
│  │                                                             │   │
│  │   (FileUploadZone COMPLETĂ, nu doar un buton)             │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ═══════════════════════════════════════════════════════════════   │
│  STARE 2: isAnalyzing (upload în progres)                          │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │   ⏳ Analyzing...                                            │   │
│  │   [Uploading: device_log.txt]                               │   │
│  │   [========================----------] 72%                  │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ═══════════════════════════════════════════════════════════════   │
│  STARE 3: hasData (avem analize)                                   │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                     │
│  (CA ACUM - toate tab-urile cu date, score, charts, etc.)         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  COMPLIANCE SCORE: 92%                                      │   │
│  │  ████████████████████░░░░  15 passed, 2 failed             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Risks / Trade-offs

### Riscul 1: Ce se întâmplă dacă upload eșuează?

**Descriere:**
În pagina `Upload.tsx`, există logica de afișare a rezultatelor (succes/eroare).
În Dashboard, `EmptyState` dispare când `hasData` devine true. Dar dacă upload eșuează?

**Analiză:**
- `useAnalysis` are `error` și `clearError`
- `Dashboard.tsx` deja afișează un `ErrorState` când `error` există
- Deci această caz este DEJA acoperit!

**Mitigare:**
Nicio acțiune necesară. Flow-ul existent:
```
upload esueaza
    ↓
context seteaza error
    ↓
Dashboard afiseaza ErrorState in loc de continut
    ↓
utilizatorul da click "Clear Error"
    ↓
revinem la EmptyState cu FileUploadZone
```

### Riscul 2: Utilizatorii care obișnuiau cu `/upload`

**Descriere:**
Veteranii aplicației s-au obișnuit cu: "Home → buton → Upload page".
Acum vor vedea doar Home cu upload zone.

**Mitigare:**
1. Ruta `/upload` redirecționează către `/` - deci niciun link nu se rupe
2. Schimbarea este DE FAURĂ BINE: "acum pot uploada direct acolo unde trebuie"
3. Dacă cineva se plânge, putem explica beneficiile

### Trade-off: Upload zone mare în față vs buton mic

**Buton mic (cum era):**
- ✅ Pagina arată "curată"
- ❌ Trebuie să dai click pentru a descoperi că poți uploada
- ❌ Navigare extra

**Upload zone mare (cum va fi):**
- ✅ Clar: "aici încarci date"
- ✅ Fără click-uri extra
- ⚠️ Ocupă mai mult spațiu pe ecran

**Decizie:** Upload zone mare este CEA MAI BUNĂ alegere pentru acest caz.
- Este o aplicație de tip "upload → vezi rezultate"
- Primul lucru pe care utilizatorul îl face este să uploadeze
- Când are date, upload zone dispare COMPLET

---

## Migration Plan

### Pas 1: Elimină "Upload" din Sidebar

**Fișier:** `frontend/src/components/Layout.tsx`

**Locație:** `baseNavItems` array (liniile ~29-42)

**Acțiune:**
Șterge elementul care are `id: 'upload'`:

```typescript
// ÎNAINTE:
const baseNavItems: NavItem[] = [
  { id: 'dashboard', label: 'Home', ... },
  { id: 'upload', label: 'Upload', ... },  // ← ȘTERGE ASTA
]

// DUPĂ:
const baseNavItems: NavItem[] = [
  { id: 'dashboard', label: 'Home', ... },
]
```

### Pas 2: Modifică Dashboard - Overview tab

**Fișier:** `frontend/src/pages/Dashboard.tsx`

**Locație:** `EmptyStateCard` din TabsContent "overview" (liniile ~359-365)

**Acțiune:**
1. Importă `FileUploadZone`:
```typescript
import { FileUploadZone } from '@/components/FileUploadZone'
```

2. Înlocuiește `EmptyStateCard` cu `FileUploadZone`:

```typescript
// ÎNAINTE:
{showLoading ? (
  <ComplianceScoreSkeleton />
) : !complianceScore ? (
  <EmptyStateCard
    icon={BarChart3}
    title="No compliance data available"
    description="Upload device log files..."
    actionLabel="Upload Logs"
    actionTo="/upload"
  />
) : (
  <ComplianceScore ... />
)}

// DUPĂ:
{showLoading ? (
  <ComplianceScoreSkeleton />
) : !complianceScore ? (
  <div className="space-y-4">
    <Card className="border-dashed border-slate-300 bg-slate-50/50">
      <CardContent className="p-6">
        <h3 className="text-sm font-medium text-slate-900 mb-4">
          No compliance data available
        </h3>
        <p className="text-sm text-slate-500 mb-6">
          Upload device log files or chart images to generate a compliance analysis.
        </p>
        <FileUploadZone
          onUploadComplete={() => {}}  // Contextul se actualizeaza automat
          maxFiles={10}
          maxSize={50 * 1024 * 1024}
        />
      </CardContent>
    </Card>
  </div>
) : (
  <ComplianceScore ... />
)}
```

**Notă:** Verifică cum funcționează `FileUploadZone` - dacă are nevoie de `onUploadComplete` pentru ceva anume, sau dacă contextul se actualizează automat.

### Pas 3: Modifică celelalte EmptyState-uri (Temperature, Violations, History)

**Idee:** Acestea pot rămâne cu un buton care duce spre Overview (sau chiar acțiune care setează tab-ul activ).

De exemplu, `EmptyStateCard` din Temperature:
```typescript
// În loc de actionTo="/upload", putem folosi:
actionTo="/"  // sau
// Nu afișa buton, ci un text: "Go to Overview tab to upload files"
```

**Simplu:** Le putem lăsa așa cum sunt dar cu `actionTo="/"` în loc de `actionTo="/upload"`.

### Pas 4: Redirecționează ruta `/upload`

**Fișier:** `frontend/src/App.tsx`

**Acțiune:**
```typescript
// ÎNAINTE:
<Route path="/upload" element={<UploadPage />} />

// DUPĂ:
<Route path="/upload" element={<Navigate to="/" replace />} />
```

**Notă:** Ai nevoie să importezi `Navigate` din `react-router-dom` (deja există).

### Pas 5: (Opțional) Deprecate `Upload.tsx`

Dacă vrem să fim curățați:
- Putem șterge `frontend/src/pages/Upload.tsx`
- Ștergem importul din `App.tsx`

**Dar pentru început:** Recomand doar redirecționare, nu ștergere.

### Pas 6: Testare

1. **Test fără date:**
   - Deschide Home → vezi FileUploadZone, nu buton
   - Sidebar are doar "Home"

2. **Test compatibilitate:**
   - Navighează manual la `/upload` → ar trebui să te redirecționeze la `/`

3. **Test upload:**
   - Uploadează un fișier DIN Dashboard
   - După terminare, pagina ar trebui să se actualizeze AUTOMAT cu datele
   - Fără redirecționări, fără așteptări

---

## Open Questions

1. **Ar trebui ca și celălalte tab-uri (Temperature, etc.) să aibă upload zone?**
   - Părerea mea: Nu. Doar Overview. Restul pot avea un text simplu.

2. **Ce facem cu `Upload.tsx` pe termen lung?**
   - Să-l șteargim după 1-2 luni când suntem siguri că nimeni nu-l folosește?
   - Sau să-l lăsăm permanent?

3. **Afișăm și titlul+descriere peste FileUploadZone, sau lăsăm componenta pură?**
   - în `Upload.tsx`, FileUploadZone are și informații suplimentare (ce tipuri de fișiere, tips)
   - Vrem să mutăm și astea în Dashboard?
   - Sau lăsăm `FileUploadZone` așa cum este?

**Răspuns provizoriu (până la implementare):**
- În prima fază, mutăm DOAR `FileUploadZone`
- Dacă ni se pare că lipsește ceva, adăugăm și informațiile suplimentare
