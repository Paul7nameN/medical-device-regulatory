## Why

This change unifies the **entire project language to English**. Currently there's a language inconsistency:

### Current Language Audit

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      LANGUAGE DISTRIBUTION IN PROJECT                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ ALREADY IN ENGLISH:                                                │
│  • openspec/project.md       → AI agents need this for context        │
│  • openspec/config.yaml      → Standardized configuration              │
│  • openspec/specs/*          → All capability specs are in English    │
│  • All application code       → Variables, functions, comments        │
│  • .env.example               → Standard environment template          │
│  • docs/roadmap/effort-estimates.md → Just updated today in English  │
│                                                                         │
│  🔴 CURRENTLY IN ROMANIAN:                                             │
│  • docs/index.md            → Main documentation hub                   │
│  • docs/CHANGELOG.md         → Project history                        │
│  • docs/getting-started/*    → Installation & configuration guides    │
│  • docs/user-guide/*         → All end-user documentation             │
│  • docs/developer-guide/*    → All developer documentation            │
│  • docs/architecture/*       → Technical architecture docs            │
│  • docs/roadmap/README.md    → Roadmap overview                       │
│  • docs/roadmap/future-plans.md → Future plans                       │
│  • docker-compose.yml comments → Embedded Romanian comments           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Problems This Creates

1. **Cognitive overhead for developers**: Constant mental context switching between Romanian (docs) and English (code)

2. **Terminology inconsistency**:
   - Romanian: "reguli", "conformitate", "motor regulator"
   - English (in openspec/): "rules", "compliance", "regulatory engine"

3. **AI agent context gap**: Fresh AI agents can read `openspec/` but cannot understand `docs/` - incomplete context

4. **Open-source barrier**: If this project ever receives external contributors, English is the de facto standard

5. **Inconsistent effort-estimates.md**: Just updated this ONE file to English today, creating internal inconsistency within `docs/roadmap/` itself

---

## What Changes

### 1. Translate All Documentation

Translate all `.md` files in `docs/` from Romanian to English:

```
docs/
├── index.md                           ← Translate
├── CHANGELOG.md                        ← Translate
├── getting-started/
│   ├── README.md                       ← Translate
│   ├── installation.md                 ← Translate
│   └── configuration.md                ← Translate
├── user-guide/
│   ├── README.md                       ← Translate
│   ├── dashboard-overview.md           ← Translate
│   ├── uploading-files.md              ← Translate
│   ├── analyzing-results.md            ← Translate
│   └── examples/
│       ├── README.md                   ← Translate
│       └── Medical Device Regulatory Constraints.md ← Already English?
├── developer-guide/
│   ├── README.md                       ← Translate
│   ├── setup.md                        ← Translate
│   ├── testing.md                      ← Translate
│   ├── adding-rules.md                 ← Translate
│   ├── log-parser.md                   ← Translate
│   └── ai-integration.md               ← Translate
├── architecture/
│   ├── README.md                       ← Translate
│   ├── overview.md                     ← Translate
│   ├── database.md                     ← Translate
│   ├── api.md                          ← Translate
│   ├── regulatory-engine.md            ← Translate
│   └── compliance-reports.md           ← Translate
└── roadmap/
    ├── README.md                       ← Translate
    ├── future-plans.md                 ← Translate
    └── effort-estimates.md             ← ⚠️ ALREADY IN ENGLISH (just verify)
```

### 2. Terminology Alignment

Critical: Match terminology in `openspec/project.md`:

| Romanian (in current docs) | English (in openspec/) |
|---------------------------|------------------------|
| `reguli` | `rules` |
| `conformitate` | `compliance` |
| `motor de reguli` | `regulatory engine` |
| `analiza` | `analysis` |
| `sesiune` | `session` |
| `dispozitiv` | `device` |
| `senzor` | `sensor` |
| `alarma` | `alarm` |
| `raport` | `report` |
| `temperatura` | `temperature` |
| `gravitate` | `severity` |
| `MED-THERM-2026` | `MED-THERM-2026` (keep as-is - it's a standard name) |

### 3. Update docker-compose.yml Comments (Optional)

The embedded Romanian comments in `docker-compose.yml` should also be in English for consistency. However, this is LOW priority since code comments are rarely read vs. proper documentation.

---

## Scope

### In Scope

- All `.md` files in `docs/` (29 files to translate, 1 already English)
- Terminology alignment with `openspec/`
- All internal links verified working
- All external links verified working

### Already English (Just Verify)

- `docs/roadmap/effort-estimates.md` - Just updated today in English
- Verify it uses consistent terminology with rest of project

### Out of Scope

- `openspec/` directory (already English, well-structured)
- Application code (already English - no changes)
- Configuration files like `.env.example` (already English)
- Root `README.md` (will check its current language)

---

## Impact

| Change Type | Count | Notes |
|-------------|-------|-------|
| **Files to translate** | 29 files | All `.md` in `docs/` |
| **Files to verify only** | 1 file | effort-estimates.md |
| **Links to verify** | ~50-100 internal links | All cross-references |

### Estimation (AI-Assisted)

| Activity | Estimate |
|----------|----------|
| Batch AI translation (29 files) | ~30 minutes |
| Human review for terminology alignment | 1-2 hours |
| Link verification | ~15 minutes |
| **TOTAL** | **~2 hours** |

---

## Benefits After This Change

### Short-term Benefits

1. **Language consistency**: ENTIRE project is now English
2. **Terminology aligned**: Same terms in `docs/` and `openspec/`
3. **No more context switching**: Developers work in one language

### Long-term Benefits

1. **Open-source ready**: International contributors can participate
2. **AI agent completeness**: Fresh AI agents get FULL context
3. **Professional presentation**: Standard practice in software industry
4. **Future-proof**: Any new documentation will naturally be in English

---

## Risks & Considerations

### Risk 1: Translation Quality

**Mitigation**: 
- AI handles the bulk translation
- Human review focuses on:
  - Technical accuracy
  - Terminology matching `openspec/`
  - Natural English tone (not literal translation artifacts)

### Risk 2: Broken Internal Links

**Mitigation**: Systematic verification after translation. Use relative link checks.

### Risk 3: Team Habits (Future Documentation)

**Mitigation**: Explicit team agreement: "From this point forward, all documentation should be written in English."

---

## Non-Goals

1. ❌ We are NOT re-writing or improving the content (just translating)
2. ❌ We are NOT restructuring the documentation (already well-structured from `2026-05-18-restructure-documentation` change)
3. ❌ We are NOT translating code comments (low ROI, high effort)
