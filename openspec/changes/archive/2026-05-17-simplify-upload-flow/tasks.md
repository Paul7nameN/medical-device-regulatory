## 1. Sidebar Cleanup - Elimină "Upload" din navigație

- [x] 1.1 Deschide `frontend/src/components/Layout.tsx`
- [x] 1.2 Găsește array-ul `baseNavItems` (liniile ~29-42)
- [x] 1.3 Identifică elementul cu `id: 'upload'`:
  ```typescript
  {
    id: 'upload',
    label: 'Upload',
    icon: <Upload className="h-5 w-5" />,
    path: '/upload',
  },
  ```
- [x] 1.4 ȘTERGE acest element din array
- [x] 1.5 Verifică că `baseNavItems` are doar elementul cu `id: 'dashboard'`
- [x] 1.6 Verifică în browser că sidebar afișează DOAR "Home"

---

## 2. Dashboard - Înlocuiește EmptyState din Overview cu FileUploadZone

- [x] 2.1 Deschide `frontend/src/pages/Dashboard.tsx`
- [x] 2.2 Adaugă importul pentru `FileUploadZone` (în zona de importuri):
  ```typescript
  import { FileUploadZone } from '@/components/FileUploadZone'
  ```
- [x] 2.3 Găsește `TabsContent` cu `value="overview"` (liniile ~353+)
- [x] 2.4 Identifică secțiunea unde este `EmptyStateCard` pentru `!complianceScore`:
  ```typescript
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
  ```
- [x] 2.5 **ÎNLOCUIEște** `EmptyStateCard` cu un `Card` care conține `FileUploadZone`:

  ```typescript
  {showLoading ? (
    <ComplianceScoreSkeleton />
  ) : !complianceScore ? (
    <Card className="border-dashed border-slate-300 bg-slate-50/50">
      <CardContent className="p-8">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-2">
            No compliance data available
          </h3>
          <p className="text-sm text-slate-500">
            Upload device log files or chart images to generate a compliance analysis.
          </p>
        </div>
        <FileUploadZone
          onUploadComplete={() => {
            // Contextul se actualizeaza automat, nu e nevoie de actiune suplimentara
            // Daca vrem sa facem ceva dupa (ex: scroll, toast), adaugam aici
          }}
          maxFiles={10}
          maxSize={50 * 1024 * 1024}
        />
      </CardContent>
    </Card>
  ) : (
    <ComplianceScore
      score={complianceScore.score}
      totalRules={complianceScore.total}
      passedRules={complianceScore.passed}
      failedRules={complianceScore.failed}
    />
  )}
  ```

- [x] 2.6 Asigură-te că ai importurile necesare: `Card`, `CardContent` (deja ar trebui să fie)
- [x] 2.7 Verifică că atunci când nu sunt date (`!hasData`), se afișează `FileUploadZone` în Overview tab

---

## 3. Dashboard - Actualizează celelalte EmptyState-uri

Acestea rămân cu buton, dar acum duc către acasă (nu la `/upload`).

- [x] 3.1 Găsește `EmptyStateCard` din **Temperature** tab:
  - Locație: `TabsContent value="temperature"`, când `!temperatureData`
  - Are `actionTo="/upload"`
- [x] 3.2 Schimbă `actionTo="/upload"` în `actionTo="/"`
- [x] 3.3 (Opțional) Schimbă `actionLabel="Upload Files"` în `actionLabel="Go to Overview"` sau lasă așa

- [x] 3.4 Găsește `EmptyStateCard` din **Violations** tab:
  - Locație: `TabsContent value="violations"`, când `!violations`
  - Are `actionTo="/upload"`
- [x] 3.5 Schimbă `actionTo="/upload"` în `actionTo="/"`

- [x] 3.6 Găsește `EmptyStateCard` din **History** tab:
  - Locație: `TabsContent value="history"`, când `analysisHistory.length === 0`
  - Are `actionTo="/upload"`
- [x] 3.7 Schimbă `actionTo="/upload"` în `actionTo="/"`

---

## 4. Rute - Redirecționează `/upload` către `/` (Home)

- [x] 4.1 Deschide `frontend/src/App.tsx`
- [x] 4.2 Găsește rutele:
  ```typescript
  <Routes>
    <Route path="/" element={<DashboardPage />} />
    <Route path="/upload" element={<UploadPage />} />  // ← aceasta
    ...
  </Routes>
  ```
- [x] 4.3 **ÎNLOCUIEște** ruta `/upload`:

  ```typescript
  // ÎNAINTE:
  <Route path="/upload" element={<UploadPage />} />

  // DUPĂ:
  <Route path="/upload" element={<Navigate to="/" replace />} />
  ```

- [x] 4.4 Verifică că `Navigate` este importat din `react-router-dom` (deja există în importuri)
- [x] 4.5 (Opțional, pentru curățenie) Poți șterge importul pentru `UploadPage` dacă nu îl folosești altundeva:
  ```typescript
  // Sterge linia asta daca nu mai ai nevoie:
  import { UploadPage } from '@/pages/Upload'
  ```

---

## 5. Testare și Verificare Finală

### 5.1 Teste vizuale rapide
- [ ] 5.1.1 Deschide aplicația → Sidebar arată DOAR "Home" (nu și "Upload")
- [ ] 5.1.2 Navighează manual la `/upload` → ar trebui să te redirecționeze IMEDIAT la `/`
- [ ] 5.1.3 Când nu sunt date → Overview tab afișează `FileUploadZone` (nu doar un buton)
- [ ] 5.1.4 Celelalte taburi (Temperature, Violations, History) au butoane care duc către `/`

### 5.2 Test funcțional - upload
- [ ] 5.2.1 Asigură-te că nu ai date (șterge istoricul dacă este nevoie)
- [ ] 5.2.2 Uploadează un fișier (.txt sau .png) DIRECT din Dashboard
- [ ] 5.2.3 Observă progress bar-ul în Dashboard
- [ ] 5.2.4 După upload terminat:
  - Verifică că pagina se actualizează AUTOMAT
  - Verifică că `hasData` devine true
  - Verifică că acum vezi scorul, tab-urile au date, etc.
  - **NU ar trebui să fie nicio redirecționare, nici așteptare de 3 secunde**

### 5.3 Test cu date existente
- [ ] 5.3.1 Dacă ai deja analize încărcate:
  - Overview tab arată scorul (NU afișează upload zone)
  - Upload zone este VIZIBILĂ DOAR când `!hasData`

---

## Rezumat Schimbărilor

| Fișier | Ce se întâmplă |
|-------|----------------|
| `frontend/src/components/Layout.tsx` | Eliminat item-ul "Upload" din sidebar |
| `frontend/src/pages/Dashboard.tsx` | 1. Adăugat import `FileUploadZone`<br>2. Înlocuit `EmptyStateCard` din Overview cu `FileUploadZone`<br>3. Actualizate `actionTo` din celelalte EmptyState-uri (`/upload` → `/`) |
| `frontend/src/App.tsx` | Redirecționat `/upload` → `/` folosind `Navigate` |

## Opțional (nu este obligatoriu pentru acest change)

- Dacă vrei să ștergi complet `Upload.tsx`:
  - Șterge fișierul: `frontend/src/pages/Upload.tsx`
  - Șterge orice referință la el în alte fișiere

- Dacă vrei să adaugi și informațiile suplimentare (ce tipuri de fișiere, tips) peste `FileUploadZone` în Dashboard:
  - Copiază secțiunile relevante din `Upload.tsx` (cards cu info, tips)
  - Adaugă-le în Dashboard, deasupra sau dedesubtul `FileUploadZone`
