## Why

Acest change rezolvă un **UX problemă majoră** în flow-ul de upload:

### Flow-ul actual (problematic)
```
HOME (fără date)
    ↓ click "Upload Logs"
UPLOAD PAGE (pagina separată)
    ↓ upload fișiere
    ↓ așteaptă 3 secunde
HOME (cu date) ← se întoarce unde a început
```

### Probleme identificate:
1. **Navigare inutilă**: Utilizatorul pleacă de acasă → merge pe upload → se întoarce acasă. De ce?
2. **Lipsă de context**: Pe pagina `/upload` utilizatorul NU vede unde va apărea rezultatul
3. **Dezorientare**: Butonul din EmptyState zice "Upload Logs" dar te duce PE ALTA PAGINĂ, nu acționează acolo
4. **Redirecționare forțată**: După upload, utilizatorul așteaptă 3s fără motiv

### Soluția (simplă și intuitivă)
```
HOME (fără date)
    ┌─────────────────────────────────────┐
    │                                     │
    │  📁 DRAG & DROP FILES HERE          │
    │      sau click to browse            │
    │                                     │
    │  [Uploading: device_log.txt]        │
    │  [==========--------] 60%           │
    │                                     │
    └─────────────────────────────────────┘
    ↓ upload terminat
HOME (cu date) ← ACELAȘI CONTEXT, ACEEAȘI PAGINĂ
```

## What Changes

### 1. Sidebar: Elimină "Upload"
- ✂️ Șterge item-ul "Upload" din `baseNavItems` din `Layout.tsx`
- Sidebar va avea DOAR "Home" (simplu, clar)

### 2. Dashboard: Empty State cu Upload Inline
- ✅ Înlocuiește `EmptyStateCard` (care are doar un buton) cu `FileUploadZone` COMPLETĂ
- Cand `!hasData` (nu sunt analize), afișează zona de upload DIRECT în pagina
- Cand upload se termină, contextul se actualizează automat (grăție `useAnalysis`)
- Nu este nevoie de nicio redirecționare!

### 3. (Opțional) Ruta `/upload` ca fallback
- ✅ Păstrăm ruta `/upload` dar o redirecționăm către `/` (Home)
- Astfel, link-urile vechi sau bookmark-urile nu se rup
- Sau o ștergem complet (decizie în design)

### 4. Pagina Upload.tsx - Deprecată?
- ⚠️ Pagina `Upload.tsx` nu va mai fi accesibilă din navigare
- O putem:
  - a) Șterge complet
  - b) Păstra ca fallback pentru API-uri externe
  - c) Redirecționa către Home

## Capabilities

### Modified Capabilities
- `file-upload`: Flow-ul de upload acum funcționează inline în Dashboard, fără navigare
- `dashboard-layout`: Acum are două stări clare:
  - Empty state: afișează zona de upload
  - Data state: afișează analizele și tab-urile

## Impact

| Component | Impact | Tip |
|-----------|--------|-----|
| `frontend/src/components/Layout.tsx` | Elimină "Upload" din sidebar nav items | Ștergere |
| `frontend/src/pages/Dashboard.tsx` | Înlocuiește `EmptyStateCard` cu `FileUploadZone` în toate locurile unde apare | Modificare |
| `frontend/src/pages/Upload.tsx` | Deprecată sau ștearsă | Opțional |
| `frontend/src/App.tsx` | Eventual modificare rute (redirect `/upload` → `/`) | Opțional |
| `frontend/src/components/FileUploadZone.tsx` | Verificăm că funcționează independent de pagină | Verificare |

## Beneficii după schimbare

1. **Zero navigări**: Utilizatorul rămâne întotdeauna pe Home
2. **Context clar**: Vezi unde apar rezultatele ÎNAINTE să uploadezi
3. **UX intuitiv**: "Dacă nu am date, aici încarc date"
4. **Fără redirecționări**: După upload, pagina se actualizează automat
5. **Sidebar mai simplu**: Doar "Home" - nimic de confuzat
