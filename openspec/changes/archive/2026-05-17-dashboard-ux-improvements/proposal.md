## Why

Acest change rezolvă **probleme UX majore** identificate în timpul explorării:

### Problema 1: Informație REDUNDANTĂ când `!hasData`

```
CURRENT LAYOUT (când nu ai date):
┌─────────────────────────────────────────────────────────────────────┐
│  Home (breadcrumb)                                                  │  Header
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  📊 No Analysis Data  ←-- PRIMUL titlu                        │   │
│  │  Upload device log files...                                   │   │  EmptyStateCard
│  │  [Upload Logs] ←-- buton cu actionTo="/" = LINK CATRE ACEEASI PAGINA!
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Analysis Hub  ←-- TITLUL PAGINII (DUPA un EmptyState!)          │
│  MED-THERM compliance overview...                                   │
│                                                                     │
│  [Overview] ████  [Temp]  [Viol]  [Hist]  [Rules]  ←-- TABS INUTILE
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  No compliance data available  ←-- AL DOILEA titlu!         │   │
│  │  Upload device log files...  ←-- ACEEAȘI descriere!         │   │
│  │                                                                 │   │
│  │  📁 DRAG & DROP ZONE                                           │   │
│  │  (userul trebuie sa SCROLL in jos pentru a vedea butonul!)   │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Probleme identificate:**
1. ❌ **Două titluri IDENTICE**: "No Analysis Data" + "No compliance data"
2. ❌ **Buton INUTIL** deasupra tab-urilor: `[Upload Logs]` cu `actionTo="/"` = link către aceeași pagină!
3. ❌ **Ordinea GREȘITĂ**: Titlul paginii ("Analysis Hub") vine DUPĂ un EmptyState
4. ❌ **Tab-uri INUTILE** când nu ai date
5. ❌ **Butonul de upload** este PREA JOS (utilizatorul trebuie să dea scroll)
6. ❌ **Sidebar mereu DESCHIS** pe desktop (utilizatorul vrea să fie închis by default)

### Problema 2: Sidebar nu are toggle pe desktop

- Pe **mobil**: Exists un buton `[Menu]` care deschide un Sheet
- Pe **desktop**: Sidebar-ul este mereu deschis (256px)
- Utilizatorul vrea: **toggle pe toate ecranele**, sidebar-ul închis by default

### Problema 3: Butoanele EmptyState din celelalte taburi nu funcționează corect

- Temperature tab: `actionTo="/"` = link către aceeași pagină
- Violations tab: `actionTo="/"` = link către aceeași pagină
- History tab: `actionTo="/"` = link către aceeași pagină

Aceste butoane ar trebui:
- Ori să schimbe tab-ul activ pe "Overview"
- Ori să dispară complet

---

## What Changes

### 1. Layout DUAL pentru Dashboard

**Când `!hasData` (nu ai date):**
- Nu afișăm tab-uri
- Nu afișăm EmptyStateCard redundant
- Afișăm DOAR: Logo + Upload Zone (LA TOP!)
- Butonul de upload este IMEDIAT vizibil, fără scroll

**Când `hasData` (ai date):**
- Layout-ul rămâne CA ACUM
- Dar cu sidebar = Sheet (toggle pe toate ecranele)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYOUT DUAL PROPUSE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CÂND NU AI DATE:                                                   │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  🛡️ MED-THERM                          [Menu] [Notifications]│   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                             │   │
│  │       📁 UPLOAD ZONE (LA TOP, FARA SCROLL!)               │   │
│  │                                                             │   │
│  │  Title: "Upload files to start compliance analysis"        │   │
│  │                                                             │   │
│  │  [ DRAG & DROP cu butoane vizibile imediat ]              │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  (NICIUN TAB, NICIUN EmptyState, NICIUN text dublu)              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CÂND AI DATE:                                                      │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                     │
│  (Layout CA ACUM, dar cu sidebar = Sheet)                         │
│                                                                     │
│  Butonul [Menu] este PE TOATE ECRANELE (nu doar mobil)           │
│  Sidebar-ul se deschide ca un Sheet (drawer din stânga)          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Sidebar = Sheet pe TOATE ecranele

**Modificări în Layout.tsx:**
- Eliminăm `hidden lg:flex` de la sidebar (sau îl înlocuim cu o stare colapsată)
- Sau MAI BINE: Folosim DOAR Sheet-ul (ca pe mobil) pentru TOATE ecranele
- Butonul `[Menu]` devine vizibil și pe desktop (`lg:hidden` → `visible`)
- Header-ul afișează Logo + Title în loc de breadcrumb

### 3. Butoanele EmptyState din celelalte taburi

În loc de `Link to="/"` (care nu face nimic util), folosim:
```typescript
onClick={() => setActiveTab('overview')}
```

Sau, și mai bine: când `!hasData`, nu afișăm deloc celelalte tab-uri (deoarece utilizatorul nu poate vedea nimic acolo).

---

## Capabilities

### Modified Capabilities
- `dashboard-layout`: Layout dual - comportament diferit când ai date vs când nu ai date
- `file-upload`: Upload zone este acum la TOP când nu ai date, vizibil imediat
- `unified-navigation-hub`: Sidebar devine Sheet pe toate ecranele, toggle cu Menu

## Impact

| Component | Impact | Tip |
|-----------|--------|-----|
| `frontend/src/components/Layout.tsx` | Butonul Menu devine vizibil pe toate ecranele. Header-ul afișează Logo + Title în loc de breadcrumb. Sidebar devine optional/Sheet. | Modificare majoră |
| `frontend/src/pages/Dashboard.tsx` | Layout dual: când !hasData, afișează DOAR Upload Zone (fără tab-uri, fără EmptyState redundant). Când ai date, layout normal dar cu actualizări. | Modificare majoră |
| `frontend/src/components/FileUploadZone.tsx` | Opțional: Posibile ajustări mici pentru a arăta mai bine când este singurul element pe pagină. | Mică |

---

## Beneficii după schimbare

1. **Zero informație redundantă**: Un singur titlu, un singur upload zone
2. **Butonul de upload vizibil imediat**: Fără scroll necesar
3. **Sidebar consistent**: Toggle pe toate ecranele, închis by default
4. **UX intuitiv**: 
   - "Dacă nu am date, văd DOAR ce trebuie să fac (upload)"
   - "Dacă am date, văd tot ce am nevoie (tab-uri, scor, etc.)"
5. **Curățenie**: Fără tab-uri inutile, fără butoane care nu funcționează corect
