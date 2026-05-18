## 1. Preparare și Extragere Componente

- [x] 1.1 Identifică toate componentele reutilizabile din Temperature și Violations
- [x] 1.2 Extrage componentele în fișiere separate (deja separate: TemperatureChart, ViolationsTable)
- [x] 1.3 Verifică că toate componentele sunt independente de contextul paginii

## 2. Extinde Dashboard cu Tab-uri

- [x] 2.1 Adaugă stare pentru tab activ în DashboardPage
- [x] 2.2 Adaugă UI pentru tab-uri (sau butoane segmentate)
- [x] 2.3 Integrează componentele de Temperature ca tab separață
- [x] 2.4 Integrează componentele de Violations ca tab separață
- [x] 2.5 Adaugă tab "History" cu lista analizelor anterioare

## 3. Simplificare Sidebar

- [x] 3.1 Modifică `baseNavItems` în Layout.tsx pentru a păstra doar "Home" și "Upload"
- [x] 3.2 (Opțional) Adaugă "History" dacă vrem acces rapid
- [x] 3.3 Testează că navigarea funcționează corect pe mobile și desktop

## 4. Redirecționare Rute Vechi

- [x] 4.1 Adaugă redirecționări în App.tsx: `/violations` → `/`, `/temperature` → `/`, `/reports` → `/`
- [x] 4.2 Păstrează rutele vechi temporar pentru bookmarks (folosind Navigate cu replace)
- [x] 4.3 Testează că redirecționările funcționează

## 5. Testare și Curățare

- [x] 5.1 Testează fluxul complet: Upload → Vezi toate datele în Hub
- [x] 5.2 Testează comutarea între tab-uri
- [x] 5.3 Testează responsive design pe mobile
- [x] 5.4 Șterge paginile vechi (Temperature.tsx, Violations.tsx, Reports.tsx) dacă nu sunt necesare
- [x] 5.5 Adaugă redirect automat pe Dashboard după upload

## 6. (Opțional) Îmbunătățiri UI

- [x] 6.1 Adaugă indicator vizibil pentru tab activ (Tabs component are deja)
- [x] 6.2 Adaugă tranziții între tab-uri
- [x] 6.3 Asigură că toate butoanele (Export, Reset Zoom, etc.) sunt accesibile
