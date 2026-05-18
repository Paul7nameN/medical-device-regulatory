## Context

Acest design se bazeaza pe explorarea codului din 18 Mai 2026.

### Descoperiri cheie in timpul explorarii

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SITUATIA ACTUALA A DOCUMENTATIEI                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Ce avem ACTUAL in proiect:                                            │
│                                                                         │
│  📄 README.md (radacina)                                               │
│     • 255 de linii                                                     │
│     • Contine: Quick Start (cu si fara Docker), structura proiectului,│
│       variabile mediu, troubleshooting                                 │
│     • PRO: foarte detaliat                                             │
│     • CONTRA: PREA LUNG pentru un README din radacina                  │
│                                                                         │
│  📁 docs/                                                               │
│     ├── 📄 database-schema-module.md (~80 linii)                       │
│     ├── 📄 regulatory-engine.md (~50 linii)                            │
│     ├── 📄 log-parser.md (~60 linii)                                   │
│     ├── 📄 ai-analysis-module.md (~100 linii)                          │
│     ├── 📄 compliance-report-module.md (~40 linii)                     │
│     └── 📁 client/                                                      │
│         ├── 📄 Medical Device Regulatory Constraints.md                 │
│         ├── 📄 Super Basic & Generic Client Request.txt                │
│         ├── 📄 Complex Enterprise-Level Client Request.txt             │
│         ├── 📄 medical_device_logs_1000.txt                           │
│         └── 🖼️ noncompliant_temperature_profile.png                   │
│         └── 🖼️ compliant_temperature_profile.png                       │
│                                                                         │
│  Ce LIPSESTE complet:                                                   │
│  ❌ Nu exista un INDEX (docs/index.md)                                  │
│  ❌ Nu exista un CHANGELOG.md                                            │
│  ❌ Nu exista un ghid structurat pentru UTILIZATORI                    │
│  ❌ Nu exista un overview arhitectural cu diagrame                     │
│  ❌ Nu exista un roadmap cu extinderi viitoare                          │
│                                                                         │
│  Ce este DEZORDONAT:                                                    │
│  • Fisierele `-module.md` nu sunt grupate pe tipul de audienta        │
│  • Nu este clar cine citeste ce: utilizator sau dezvoltator?          │
│  • `docs/client/` contine cereri de la client si exemple -             │
│    probabil ar trebui sa stea in `docs/user-guide/examples/`          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Goals / Non-Goals

**Goals:**
1. ✅ Structura profesionala conform best practices
2. ✅ Index principal (`docs/index.md`)
3. ✅ Separatia pe audiente: getting-started, user-guide, developer-guide
4. ✅ Integrarea continutului existent din fisierele `-module.md`
5. ✅ Adaugarea sectiunilor lipsa: architecture/overview, roadmap
6. ✅ Reducerea `README.md` din radacina la un overview scurt

**Non-Goals:**
1. ❌ Nu scriem continut NOU detaliat (doar structura si ceea ce avem deja)
2. ❌ Nu cream diagrame complexe (doar ASCII simple)
3. ❌ Nu modificam continutul tehnic al documentatiei existente
4. ❌ Nu facem refactorizari majore ale textului

---

## Decizii

### Decizia 1: Ce structura folosim?

**Optiuni considerate:**

| Structura | Descriere | Pro | Contra |
|-----------|-----------|-----|--------|
| **A: Pe componente** | `docs/log-parser/`, `docs/regulatory-engine/`, etc. | Logica pentru dezvoltatori | Nu este usor de urmat pentru utilizatori |
| **B: Pe audiente** | `docs/getting-started/`, `docs/user-guide/`, `docs/developer-guide/` | Standard in industria, usor de navigat | Trebuie sa mutam continutul existent |
| **C: Mix** | Atat pe componente cat si pe audiente | Flexibil | Confuz, structura dubla |

**Decizie: OPȚIUNEA B (Pe audiente)**

**Rationale:**
Aceasta este structura standard folosita in majoritatea proiectelor open-source profesionale:
- **Next.js**, **React**, **Vue**, **FastAPI** - toate folosesc o structura similara
- Este cea mai usoara de navigat pentru orice tip de utilizator
- Separa clar: "ce trebuie sa stiu eu ca incepator?" vs "ce trebuie sa stiu eu ca dezvoltator?"

```
┌─────────────────────────────────────────────────────────────────────────┐
│             STRUCTURA PE AUDIENTE (Best Practice)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Cine citeste?                     Ce gaseste?                          │
│  ════════════                     ════════════                          │
│                                                                         │
│  ┌──────────────┐                                                     │
│  │   Incepator  │────► docs/getting-started/                          │
│  │              │       • Cum instalez?                                │
│  │              │       • Cum configurez?                              │
│  └──────────────┘                                                     │
│                                                                         │
│  ┌──────────────┐                                                     │
│  │  Utilizator  │────► docs/user-guide/                               │
│  │   (Final)    │       • Cum folosesc dashboard-ul?                 │
│  │              │       • Cum uploadez fisiere?                       │
│  │              │       • Cum analizez rezultatele?                   │
│  └──────────────┘                                                     │
│                                                                         │
│  ┌──────────────┐                                                     │
│  │ Dezvoltator  │────► docs/developer-guide/                          │
│  │              │       • Cum rulez testele?                          │
│  │              │       • Cum adaug reguli noi?                       │
│  │              │       • Cum functioneaza log parser-ul?             │
│  └──────────────┘                                                     │
│                                                                         │
│  ┌──────────────┐                                                     │
│  │ Arhitect /   │────► docs/architecture/                             │
│  │   Manager    │       • Overview cu diagrame                        │
│  │              │       • Schema bazei de date                        │
│  │              │       • API endpoints                                │
│  └──────────────┘                                                     │
│                                                                         │
│  ┌──────────────┐                                                     │
│  │   Client /   │────► docs/roadmap/                                  │
│  │   Product    │       • Ce extinderi sunt planificate?              │
│  │              │       • Cat costa fiecare extindere?                │
│  └──────────────┘                                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Decizia 2: Ce facem cu fisierele `-module.md` existente?

**Optiuni:**

| Opțiune | Descriere |
|---------|-----------|
| **A: Le stergem si le rescriem** | Pierdem continutul existent |
| **B: Le mutam direct in noua structura** | Pastram continutul, dar poate fi dezordonat |
| **C: Integrare selectiva** | Mutam continutul relevant, iar restul il ignoram sau mutam in `docs/archive/` |

**Decizie: OPȚIUNEA C (Integrare selectiva)**

**Maparea:**

| Fisier Vechi | Unde merge | Ce facem cu el? |
|--------------|------------|-----------------|
| `docs/database-schema-module.md` | `docs/architecture/database.md` | Mutam continutul integral, adaugam un header nou |
| `docs/regulatory-engine.md` | `docs/architecture/regulatory-engine.md` | Mutam continutul integral |
| `docs/log-parser.md` | `docs/developer-guide/log-parser.md` | Mutam continutul integral |
| `docs/ai-analysis-module.md` | `docs/developer-guide/ai-integration.md` | Mutam continutul integral |
| `docs/compliance-report-module.md` | - | Acest feature nu este complet. Il mutam in `docs/roadmap/` sau il ignoram deocamdata |
| `docs/client/*` | `docs/user-guide/examples/` | Mutam exemplele si cererile clientului aici |

---

### Decizia 3: Ce facem cu `README.md` din radacina?

**Problema:**
- Acesta are 255 de linii
- Contine: Quick Start, Instalare cu si fara Docker, Variabile mediu, Troubleshooting, Structura proiectului

**Decizie:**
- Reducem `README.md` la ~50 de linii: doar un overview scurt + link-uri
- Tot continutul detaliat il mutam in `docs/getting-started/` si `docs/developer-guide/`

**Ce ramane in `README.md` nou:**
1. Titlu + descriere scurta
2. Tehnologii (lista scurta)
3. Quick Start (doar Docker: 3 pasi)
4. Link-uri catre `docs/`:
   - 📖 Documentatie completa: `docs/index.md`
   - 🚀 Ghid de instalare: `docs/getting-started/installation.md`
   - 🎯 Ghid de utilizare: `docs/user-guide/`
   - 🔧 Pentru dezvoltatori: `docs/developer-guide/`

---

## Structura Detaliata a Fisierelor

### 1. `docs/index.md` - Tabel de continut

**Ce include:**
- Welcome la MED-THERM
- Scurta descriere a proiectului
- Link-uri rapide catre toate sectiunile
- Diagrama simpla a "cum navighezi documentatia"

**Structura:**
```markdown
# MED-THERM Compliance Engine - Documentatie

## Descriere
Sistem de validare a conformitatii regulatorii pentru dispozitive medicale...

## Incepe Aici
- [Ghid de Instalare](getting-started/installation.md)
- [Prima Utilizare](getting-started/)

## Pentru Utilizatori
- [Ghid de Utilizare](user-guide/)
- [Exemple Practice](user-guide/examples/)

## Pentru Dezvoltatori
- [Setup Mediu de Dezvoltare](developer-guide/setup.md)
- [Cum Adaug Reguli Noi](developer-guide/adding-rules.md)

## Arhitectura Tehnica
- [Overview Arhitectural](architecture/overview.md)
- [Schema Bazei de Date](architecture/database.md)
- [API Documentation](architecture/api.md)

## Viitorul Proiectului
- [Roadmap](roadmap/)
- [Estimari de Efort](roadmap/effort-estimates.md)

## Istoric Schimbari
- [CHANGELOG.md](CHANGELOG.md)
```

---

### 2. `docs/CHANGELOG.md`

**Format standard:**
```markdown
# CHANGELOG

## [Unreleased]

## [1.0.0] - 2026-05-18

### Added
- Dark Mode complet
- Restructurarea documentatiei conform best practices
- ...

### Fixed
- Fixed category inconsistency between backend/frontend
- ...
```

---

### 3. `docs/getting-started/`

**`getting-started/README.md`:**
- Ce gasesti in acest folder
- Link-uri catre `installation.md` si `configuration.md`

**`getting-started/installation.md`:**
- Tot continutul din `README.md` vechi referitor la instalare cu Docker
- Pasii: Clone, Config, Docker Compose up
- Accesarea aplicatiei

**`getting-started/configuration.md`:**
- Variabile mediu
- `MODELARK_API_KEY` - optional, pentru AI features
- Ce se intampla daca nu ai cheia

---

### 4. `docs/architecture/`

**`architecture/README.md`:**
- Ce gasesti in acest folder
- Link-uri rapide

**`architecture/overview.md` - NOU:**
- **Cel mai important fisier pentru arhitecti**
- Diagrame ASCII ale arhitecturii
- Flow de date
- Componentele cheie
- Tehnologii folosite (cu versiuni)

Continut exemplu:
```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARHITECTURA MED-THERM                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Frontend (React 18 + Vite)                                         │
│       │                                                              │
│       │ HTTP (TanStack Query)                                       │
│       ▼                                                              │
│  Backend (FastAPI + Python 3.12)                                    │
│       │                                                              │
│       ├──► Log Parser                                               │
│       ├──► Regulatory Engine (21 reguli)                            │
│       └──► AI Integration (ModelArk)                                │
│       │                                                              │
│       │ SQLAlchemy ORM                                              │
│       ▼                                                              │
│  PostgreSQL 16                                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**`architecture/database.md`:**
- Din vechiul `database-schema-module.md`
- Diagrama tabelelor
- Descrierea fiecarei tabele
- Relațiile între tabele

**`architecture/api.md` - NOU:**
- Referinta catre `/docs` (Swagger UI)
- Lista endpoint-urilor principale
- Exemple simple de request/response

**`architecture/regulatory-engine.md`:**
- Din vechiul `regulatory-engine.md`
- Cum functioneaza motorul de reguli
- Lista tuturor celor 21 de reguli
- Cum sunt grupate pe categorii

---

### 5. `docs/user-guide/` - NOU

**`user-guide/README.md`:**
- Ce gasesti aici
- Link-uri catre pagini

**`user-guide/dashboard-overview.md`:**
- Ce este Dashboard-ul
- Ce se afla pe fiecare tab
- Overview, Temperature, Violations, Rules, History

**`user-guide/uploading-files.md`:**
- Ce tipuri de fisiere accepta? (.txt, .png, .jpg)
- Cum uploadezi (drag & drop)
- Ce se intampla dupa upload

**`user-guide/analyzing-results.md`:**
- Cum citesti Compliance Score-ul
- Ce inseamna fiecare severity
- Cum folosesti tabelul de violari

**`user-guide/examples/`:**
- Mutam continutul din `docs/client/` aici
- Exemple de log-uri
- Cererile clientilor (ca referinta)

---

### 6. `docs/developer-guide/`

**`developer-guide/README.md`:**
- Ce gasesti aici
- Link-uri rapide

**`developer-guide/setup.md`:**
- Din `README.md` vechi: "Dezvoltare fara Docker"
- Cum rulezi backend si frontend separat
- Cum rulezi migrarile

**`developer-guide/log-parser.md`:**
- Din vechiul `log-parser.md`
- Cum functioneaza parser-ul
- Ce formate accepta

**`developer-guide/ai-integration.md`:**
- Din vechiul `ai-analysis-module.md`
- Cum functioneaza integrarea cu ModelArk
- Ce modele folosim
- Cum functioneaza analiza chart-urilor

**`developer-guide/adding-rules.md` - NOU:**
- Cum creezi o regula noua
- Exemplu simplu
- Cum o inregistrezi in RuleRegistry

**`developer-guide/testing.md` - NOU:**
- Cum rulezi testele pytest
- Ce teste exista
- Structura folderului `backend/tests/`

---

### 7. `docs/roadmap/` - NOU

**`roadmap/README.md`:**
- Ce gasesti aici
- Link-uri catre `future-plans.md` si `effort-estimates.md`

**`roadmap/future-plans.md`:**
- Lista cu toate extinderile propuse
- Scurta descriere pentru fiecare
- Prioritatea fiecareia

**`roadmap/effort-estimates.md`:**
- Acelasi tabel comparativ pe care l-am discutat in explorare
- Extindere | Timp | Resurse | Complexitate | Prioritate

---

## Migration Plan

### Ordinea de executie

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MIGRATION ORDER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PHAZA 1: CREARE STRUCTURA                                          │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                     │
│  1. Creeaza toate folderele                                          │
│  2. Creeaza toate fisierele README.md din fiecare folder            │
│  3. Creeaza docs/index.md                                            │
│  4. Creeaza docs/CHANGELOG.md                                        │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PHAZA 2: INTEGRARE FISIERE VECHI                                  │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                     │
│  5. Mutam docs/database-schema-module.md → architecture/database.md│
│  6. Mutam docs/regulatory-engine.md → architecture/regulatory.md   │
│  7. Mutam docs/log-parser.md → developer-guide/log-parser.md       │
│  8. Mutam docs/ai-analysis-module.md → developer-guide/ai.md        │
│  9. Mutam docs/client/* → user-guide/examples/                      │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PHAZA 3: CREARE FISIERE NOI                                        │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                     │
│  10. Creeaza architecture/overview.md (cu diagrame)                │
│  11. Creeaza architecture/api.md                                    │
│  12. Creeaza toate fisierele din user-guide/                        │
│  13. Creeaza developer-guide/setup.md                               │
│  14. Creeaza developer-guide/adding-rules.md                        │
│  15. Creeaza developer-guide/testing.md                             │
│  16. Creeaza toate fisierele din roadmap/                           │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PHAZA 4: FINALIZARE                                                │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                     │
│  17. Micsoreaza README.md din radacina                              │
│  18. Sterge fisierele vechi `-module.md` (dupa verificare)         │
│  19. Updateaza toate link-urile sa fie corecte                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Risks / Trade-offs

### Riscul 1: Link-uri rumpe

**Descriere:**
- Cand mutam fisierele, orice link-uri interne din documentatie se pot rumpe

**Mitigare:**
1. Verificam toate link-urile dupa migrare
2. Folosim link-uri relative (ex: `../getting-started/installation.md`)
3. Lasam un mesaj in vechile fisiere inainte de a le sterge:
   ```markdown
   > Acest fisier a fost mutat la: [noua-locatie](noua-locatie.md)
   ```

---

### Riscul 2: Continutul este dezordonat dupa integrare

**Descriere:**
- Fisierele vechi `-module.md` au fost scrise in perioade diferite
- Stilul si structura poate fi inconsistent

**Mitigare:**
1. Adaugam un header standard la fiecare fisier integrat
2. Nu modificam continutul tehnic, doar il reorganizam
3. Pentru viitor, definim un template pentru fiecare tip de fisier

---

### Riscul 3: Este multa munca organizationala

**Descriere:**
- ~12 fisiere noi de creat
- 4 fisiere de integrat
- 1 fisier de modificat

**Mitigare:**
1. Impartim pe task-uri mici in tasks.md
2. Incepem cu cele mai importante (index, overview)
3. Fisierele noi pot avea continut minim la inceput, pe care il completam mai tarziu
