# Cum analizezi rezultatele

---

## Dupa upload, vei vedea

### Compliance Score

Scorul de conformitate (0-100%):
- **90-100%** - Foarte bun
- **70-89%** - Acceptabil
- **Sub 70%** - Necesita atentie

Calculat ca:
```
Score = (Reguli Trecute / Total Reguli) × 100
```

### Categorii

Pe ce categorii sunt probleme:
- **TEMP** - Controlul temperaturii
- **SENS** - Senzori
- **ALARM** - Alarme
- **DATA** - Date
- **POWER** - Alimentare
- **COOL** - Răcire
- **INS** - Insulatie
- **OPS** - Operatiuni

### Violations

Detalii despre fiecare violare:

| Severitate | Actiune necesara |
|------------|------------------|
| **CRITICAL** | Actiune imediata (24 ore) |
| **HIGH** | Prioritate mare (72 ore) |
| **MEDIUM** | Urmatoarea intretinere |
| **LOW** | Monitorizeaza |

### Temperature Chart

Evolutia temperaturilor in timp:
- **Linie albastra** - Sensor A (primar)
- **Linie mov** - Sensor B (secundar)
- **Banda verde** - Interval sigur (2-8°C)
- **Rosu/Portocaliu** - Excursii in afara intervalului

**Functionalitati:**
- Drag pentru a zoom-a pe anumite intervale
- Click pe legenda pentru a arata/ascunde senzori
- Hover pe puncte pentru a vedea valoarea exacta
