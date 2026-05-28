# Live Transport Monitoring

Monitorizare în timp real al transporturilor medicale cu temperatură controlată.

---

## Ce este Live Transport

Sistemul permite monitorizarea în timp real a datelor de telemetrie:
- Simulare demo cu scenarii predefinite
- Replay din fișiere de log existente
- Reguli de conformitate sunt evaluate la fiecare tick

---

## Caracteristici unice

### ✅ Persistență prin navigare
Transportul **NU se oprește** când părăsești pagina `/live`. Poți naviga la Home, History sau orice altă pagină și transportul continuă să ruleze în fundal.

Când un transport este activ:
- Apare un banner **persistent** în partea superioară a tuturor paginilor
- Iconița din sidebar afișează un puls animat + numărul de alerte
- Toate datele, alertele și scorul sunt păstrate

Click pe banner pentru a reveni direct la transportul activ.

---

## Moduri de funcționare

### 1. Simulare demo
- 3 scenarii predefinite:
  - `Stable transport` - demonstrație fără probleme
  - `Door + temperature excursion` - ușa deschisă + temperatură ieșită din limite
  - `Sensor + power stress` - eșecuri de senzor și probleme de alimentare

### 2. Replay din fișier de log
- Încărcă un fișier `.txt` sau `.log` cu date de telemetrie
- Sistemul re-analizează fiecare linie în ordine
- Viteză de replay ajustabilă: ×1, ×2, ×5, ×10, ×25

---

## Control panel

| Control | Funcție |
|---|---|
| **Device ID** | Identificator unic al dispozitivului |
| **Data source** | `Built-in scenario` sau `Log file replay` |
| **Scenario** | Alege scenariul de simulare |
| **Simulation speed** | Viteză de generare a tick-urilor |

---

## Afișare real-time

### Grafice
- **Temperatură** - senzorul principal, cu interval safe (2-8°C)
- **Fan speed** - viteza ventilatorilor
- **Umiditate** - nivelul de umiditate

### Alerte live
Alertele apar instantanee când o regulă este încălcată:
- 🟥 Critical - acțiune imediată
- 🟧 High - problemă majoră
- 🟨 Medium - problemă medie
- 🟩 Low - problemă minoră
- 🔵 Info - informație

---

## Finalizare
Când transportul se termină (manual sau prin finalizarea log replay):
1. Sistemul generează automat un raport de conformitate
2. Este adăugat automat în `History`
3. Ești redirecționat pe pagina principală cu raportul încărcat
