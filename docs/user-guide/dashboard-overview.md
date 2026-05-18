# Overview al Dashboard-ului

Dashboard-ul are 5 tab-uri principale:

---

## 1. Overview

Rezumat general al analizei:
- **Compliance Score** - Scorul de conformitate
- **Severity Counts** - Numarul de violari pe severitate
- **Compliance by Category** - Rezumat pe categorii
- **AI Analysis** - Daca AI este activat, vei vedea si insights-urile AI

---

## 2. Temperature

Graficul temperaturilor:
- **Sensor A** - Temperatura senzorul primar
- **Sensor B** - Temperatura senzorul secundar (daca exista)
- **Safe Range** - Banda verde indica intervalul sigur (2-8°C)
- **Exemplare** - In rosu/portocaliu cand temperatura este in afara intervalului

### Carduri Info:
- **Sensor A (Avg)** - Temperatura medie a senzorului primar
- **Sensor B (Avg)** - Temperatura medie a senzorului secundar
- **Safe Range** - Intervalul sigur (2-8°C)
- **Status** - Numarul de probleme detectate

---

## 3. Violations

Tabelul cu toate violarile:
- **Severitate** - Critical, High, Medium, Low
- **Cod Regula** - De ex: REG-TEMP-1
- **Descriere** - Descrierea violarii
- **Detectat La** - Cand a fost detectata
- **Status** - Open, Acknowledged, Resolved

### Carduri de Sus:
- **Critical** - Violari critice (actiune imediata)
- **Open** - Violari deschise
- **Acknowledged** - Violari recunoscute
- **Resolved** - Violari rezolvate

---

## 4. Rules

Referinta la toate regulile MED-THERM-2026:
- Categoria
- Codul regulii
- Descrierea
- Severitatea implicita

---

## 5. History

Istoricul analizelor:
- Numarul analizei
- Device
- Analyzed At
- Score
- Violations
- Status
- Actiuni: Load, Remove

Poti:
- **Load** - Incarca o analiza anterioara
- **Remove** - Sterge o analiza din istoric
- **Clear All** - Sterge toate analizele (cu confirmare)
