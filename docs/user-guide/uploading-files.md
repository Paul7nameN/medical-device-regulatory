# Cum uploadezi fisiere

---

## Tipuri de fisiere acceptate

| Tip | Format | Descriere |
|-----|--------|-----------|
| **Log-uri** | `.txt` | Fisiere de log de la dispozitive medicale |
| **Imagini** | `.png`, `.jpg` | Imagini cu chart-uri de temperatura |

---

## Cum uploadezi

1. Intra in pagina **Overview**
2. Da **drag & drop** in zona de upload
3. Sau **click pe zona** pentru a alege fisiere

Multiplu fisiere pot fi uploadate simultan (maxim 10 fisiere, 50MB fiecare).

---

## Ce se intampla dupa upload

1. **Log Parser** parseaza fisierele .txt
2. **AI Image Analysis** analizeaza imaginile .png/.jpg (daca AI este activat)
3. **Regulatory Engine** ruleaza toate regulile
4. **Dashboard** se actualizeaza cu rezultatele

---

## Exemple de log-uri

Vezi exemple practice in `docs/user-guide/examples/`:
- `medical_device_logs_1000.txt` - Exemplu de 1000 de intrari
- `compliant_temperature_profile.png` - Chart conform
- `noncompliant_temperature_profile.png` - Chart neconform
