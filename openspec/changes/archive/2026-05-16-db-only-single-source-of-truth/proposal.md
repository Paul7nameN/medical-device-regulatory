## Why

**Problema actuală:** Există un **complex inutil** în fluxul de date pentru istoricul de analize:

```
┌─────────────────────────────────────────────────────────────────────────┐
│         FLUX COMPLEX ȘI CU ERORI (CURRENT)                            │
└─────────────────────────────────────────────────────────────────────────┘

  LocalStorage          Merge/Deduplic/Sync          Baza de date
  ┌──────────────┐                          ┌──────────────┐
  │              │                          │              │
  │  Istoric     │◄─────── Probleme ───────►│  Istoric     │
  │              │   • Dubluri             │              │
  │              │   • Timestamp-uri       │              │
  │              │     diferite            │              │
  │              │   • Structuri           │              │
  │              │     diferite            │              │
  │              │   • Conflicte           │              │
  │              │                          │              │
  └──────────────┘                          └──────────────┘
         │                                       │
         ▼                                       ▼
    La pornire:                         La pornire:
    • Citește din localStorage           • GET /api/analysis
    • Apoi citește din DB             
    • Face merge
    • Face deduplicare
    • Salvează înapoi în localStorage
```

**De ce este o problemă:**
1. **Complexitate inutilă** - Două surse de adevăr = sincronizare = bug-uri
2. **Dubluri în istoric** - Din cauza diferențelor de timestamp
3. **Conflicte** - Ce se întâmplă dacă aceleași date sunt în ambele locuri?
4. **Necorespunță structurilor** - DB are un format, localStorage altul
5. **Pentru sisteme medicale/regulatorii** - Ar trebui să existe o SURSA UNICĂ DE ADEVĂR

---

## What Changes

**Arhitectura nouă: SURSĂ UNICĂ DE ADEVĂR = DOAR BAZA DE DATE**

```
┌─────────────────────────────────────────────────────────────────────────┐
│         FLUX SIMPLU ȘI FĂRĂ ERORI (NOU)                              │
└─────────────────────────────────────────────────────────────────────────┘

                            SURSA UNICĂ DE ADEVĂR
                            ┌──────────────┐
                            │  Baza de date │
                            │              │
                            │  PostgreSQL  │
                            └───────┬──────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
           ▼                        ▼                        ▼
    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
    │ La pornire   │         │ După upload  │         │ Orice altă   │
    │              │         │              │         │ operațiune    │
    │              │         │              │         │              │
    │ DOAR:        │         │ DOAR:        │         │ DOAR:        │
    │ GET /api/    │         │ refresh:     │         │ refresh:     │
    │ analysis     │         │ GET /api/    │         │ GET /api/    │
    │              │         │ analysis     │         │ analysis     │
    └──────────────┘         └──────────────┘         └──────────────┘
           │
           ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │  localStorage:                                                    │
    │  • Opțiunea A: Devine DOAR un cache OFFLINE (fallback)         │
    │  • Opțiunea B: Este ELIMINAT complet (simplu, dar dependent    │
    │                  de backend)                                      │
    └──────────────────────────────────────────────────────────────────┘
```

---

## Changes Detaliate

### 1. Frontend: `AnalysisContext.tsx`

**Ce se schimbă:**

| Componentă | Înainte | Acum |
|------------|---------|------|
| La pornire (`useEffect([])`) | `loadHistoryFromStorage()` → `refreshHistory()` → merge → `saveHistoryToStorage()` | DOAR `refreshHistory()` (doar din DB) |
| `refreshHistory()` | Fetch din DB → compară cu localStorage → merge → salvează în localStorage | DOAR: Fetch din DB → afișează |
| `loadHistoryFromStorage()` | Folosit intens | Opțional: doar ca fallback |
| `saveHistoryToStorage()` | Folosit după fiecare modificare | Poate fi eliminat |

**Punctul de decizie:** Ce facem cu `localStorage`?

**Opțiunea A (Siguranță): localStorage ca FALLBACK**
- La pornire: Încearcă întâi `GET /api/analysis`
- Dacă SUCCES: Folosește DOAR ce vine din DB
- Dacă EȘEC: Folosește ce este în localStorage (dacă există)
- Afișează un mesaj: "Mod offline. Datele din cache."

**Opțiunea B (Maxim Simplu): FĂRĂ localStorage**
- La pornire: DOAR `GET /api/analysis`
- Dacă EȘEC: Afișează "Nu se poate conecta la server. Verifică conexiunea."
- localStorage poate fi eliminat complet (sau lăsat pentru viitor)

---

### 2. Frontend: După upload (`FileUploadZone.tsx`)

**Înainte:**
```typescript
// După upload cu succes:
addAnalysis({
  validationResult: ...,
  rawLogs: ...,
  ...
})  // ← Adaugă direct în context + salvează în localStorage

// Plus: contextul are un useEffect care salvează automat în localStorage
```

**Acum:**
```typescript
// După upload cu succes:
// NU mai adăugăm nimic în context sau localStorage

// DOAR:
refreshHistory()  // ← Fetch din baza de date

// Contextul va afișa DOAR ce vine din baza de date
```

---

### 3. Consecințe pozitive

| Avantaj | Descriere |
|---------|-----------|
| **Fără duble** | Nu există surse multiple → nu există ce să deduplice |
| **Fără conflicte** | O singură sursă = nimic de sincronizat |
| **Simplu** | Mult mai puțin cod de întreținut |
| **Auditabil** | Toate datele sunt în baza de date (pentru sisteme medicale) |
| **Consistent** | Toți utilizatorii văd aceleași date |

---

## Capabilities

### Modified Capabilities
- `analysis-sessions`: De la "sync între DB și localStorage" la "doar DB"
- `log-storage`: Simplificat - fără nevoie de cache în browser

### Removed Capabilities (opțional)
- `localStorage cache`: poate fi eliminat sau transformat în fallback

---

## Impact

### Frontend
- **`AnalysisContext.tsx`**: Simplificare majoră
  - `refreshHistory()` devine simplu (doar fetch din DB)
  - `loadHistoryFromStorage()` și `saveHistoryToStorage()` devin opționale
  - Elimină logica de merge și deduplicare

- **`FileUploadZone.tsx`**: După upload, DOAR refresh
  - Nu mai folosește `addAnalysis()` direct
  - Doar un apel la `refreshHistory()`

- **Alte componente**: Nicio modificare!
  - Ele folosesc `useAnalysis()` care va conține date din DB
  - Interfața rămâne același

### Backend
- **NICI O MODIFICARE!**
  - Endpoint-urile există deja: `GET /api/analysis`, `POST /api/reports/generate`
  - Salvarea în DB există deja
  - Doar frontendul se simplifică

---

## Open Questions

1. **Ce facem cu localStorage?**
   - Opțiunea A: Lăsăm ca fallback offline (sigur, dar puțin mai complex)
   - Opțiunea B: Eliminăm complet (maxim simplu, dar dependent de backend)

2. **Vrem să lăsăm o cale de migrare pentru localStorage existent?**
   - La prima rulare după deploy, putem oferi opțiunea: "Ai X analize locale. Vrei să le salvezi în DB?"

3. **Ce despre performanță?**
   - La pornire, va face mereu un `GET /api/analysis`
   - Dar acesta este un request rapid (doar listare)
   - Dacă dorim, putem adăuga un cache cu TTL (dar nu recomand pentru început)
