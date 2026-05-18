## Why

Acest change **restructureaza intreaga documentatie** a proiectului MED-THERM pentru a respecta **best practices** din industria software.

### Problema identificata in timpul explorarii

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AUDIT DOCUMENTATIE ACTUALA                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ Ce este BINE:                                                       │
│  • Exista un README.md bun cu Quick Start                              │
│  • Exista fisiere de documentatie pe module:                           │
│    - docs/database-schema-module.md                                    │
│    - docs/regulatory-engine.md                                         │
│    - docs/log-parser.md                                                │
│    - docs/ai-analysis-module.md                                        │
│                                                                         │
│  ❌ Ce este RAU (ce trebuie imbunatatit):                              │
│                                                                         │
│  1. NU EXISTA un INDEX PRINCIPAL (docs/index.md)                      │
│     → Utilizatorii nu stiu unde sa inceapa                             │
│                                                                         │
│  2. Structura NU urmeaza best practices:                               │
│     → Nu sunt separate: getting-started, architecture, user-guide,    │
│       developer-guide, roadmap                                          │
│                                                                         │
│  3. Fisierele `-module.md` sunt dezordonate:                          │
│     → Nu este clar cine le citeste: utilizatori sau dezvoltatori?    │
│                                                                         │
│  4. LIPSESTE complet:                                                   │
│     → Ghid de utilizare (User Guide) detaliat                          │
│     → Arhitectura tehnica cu diagrame                                  │
│     → Roadmap cu extinderi viitoare + estimari de efort               │
│     → CHANGELOG.md pentru a urmari schimbarile                         │
│                                                                         │
│  5. README.md din radacina este PREA LUNG:                             │
│     → Trebuie sa fie doar un overview scurt + link-uri                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## What Changes

### 1. Structura Noua (Best Practice)

Vom crea aceasta structura in folderul `docs/`:

```
docs/
├── index.md                 # Tabel de continut PRINCIPAL
├── CHANGELOG.md             # Istoricul schimbarilor (nou)
│
├── getting-started/         # Pentru INCEPATORI
│   ├── README.md
│   ├── installation.md      # Cum instalezi (cu Docker)
│   └── configuration.md     # Variabile mediu
│
├── architecture/            # Arhitectura TEHNICA
│   ├── README.md
│   ├── overview.md          # Overview cu diagrame (nou)
│   ├── database.md          # Schema BD (din vechiul database-schema-module)
│   ├── api.md               # API (nou - se bazeaza pe /docs din FastAPI)
│   └── regulatory-engine.md # Motorul de reguli (din vechiul regulatory-engine.md)
│
├── user-guide/              # GHID DE UTILIZARE (nou)
│   ├── README.md
│   ├── dashboard-overview.md
│   ├── uploading-files.md
│   └── analyzing-results.md
│
├── developer-guide/         # PENTRU DEZVOLTATORI
│   ├── README.md
│   ├── setup.md             # Setup fara Docker (din README vechi)
│   ├── log-parser.md        # (din vechiul log-parser.md)
│   ├── ai-integration.md    # (din vechiul ai-analysis-module.md)
│   ├── adding-rules.md      # Cum adaugi reguli noi (nou)
│   └── testing.md           # Cum rulezi testele (nou)
│
└── roadmap/                 # VIITORUL (nou)
    ├── README.md
    ├── future-plans.md      # Extinderi propuse
    └── effort-estimates.md  # Estimari de timp si resurse
```

### 2. Ce vom INTEGRA din fisierele vechi

| Fisier Vechi | Unde merge in noua structura |
|--------------|-------------------------------|
| `docs/database-schema-module.md` | `docs/architecture/database.md` |
| `docs/regulatory-engine.md` | `docs/architecture/regulatory-engine.md` |
| `docs/log-parser.md` | `docs/developer-guide/log-parser.md` |
| `docs/ai-analysis-module.md` | `docs/developer-guide/ai-integration.md` |
| `docs/compliance-report-module.md` | (va fi ignorat sau mutat in roadmap daca nu e gata) |

### 3. Ce vom MODIFICA

- **`README.md`** din radacina → va fi redus la un overview scurt + link-uri catre `docs/`
- **`CHANGELOG.md`** → nou, pentru a urmari toate schimbarile

---

## Impact

| Component | Tip | Descriere |
|-----------|-----|-----------|
| **NOU: `docs/index.md`** | Creare | Tabel de continut principal |
| **NOU: `docs/CHANGELOG.md`** | Creare | Istoricul schimbarilor |
| **`docs/getting-started/*`** | Creare | 3 fisiere noi |
| **`docs/architecture/*`** | Mixt | 2 fisiere noi + 2 integrate |
| **`docs/user-guide/*`** | Creare | 4 fisiere noi |
| **`docs/developer-guide/*`** | Mixt | 3 fisiere noi + 2 integrate |
| **`docs/roadmap/*`** | Creare | 3 fisiere noi |
| **`README.md` (radacina)** | Modificare | Redus la overview + link-uri |

### Total:
- **Fisiere NOI de creat**: ~12 fisiere
- **Fisiere EXISTENTE de integrat**: 4 fisiere
- **Fisiere de MODIFICAT**: 1 fisier (`README.md`)

---

## Beneficii dupa schimbare

1. **Structura PROFESIONALA**: Urmeaza best practices din open-source
2. **Usor de NAVIGAT**: Utilizatorii stiu exact unde sa gaseasca fiecare informatie
3. **SEMENTAT**: 
   - `getting-started/` → pentru incepatori
   - `architecture/` → pentru arhitecti
   - `user-guide/` → pentru utilizatori finali
   - `developer-guide/` → pentru dezvoltatori
   - `roadmap/` → pentru product managers si clienti
4. **USOR de INTRETINUT**: Fiecare domeniu are propriul sau fisier
5. **Index PRINCIPAL**: `docs/index.md` este punctul de intrare pentru toti

---

## Ce NU include acest change (Non-Goals)

1. ❌ Nu scriem continut NOU detaliat (doar structura si continutul pe care il avem deja)
2. ❌ Nu cream diagrame complexe (doar diagrame ASCII simple in `overview.md`)
3. ❌ Nu modificam continutul existent al documentatiei (doar il mutam in structura noua)
