# Extinderi Propuse

Extinderi viitoare pentru MED-THERM.

---

## Lista de extinderi

### 1. Autentificare si Autorizare

**Ce adauga**:
- Login/Register
- JWT tokens
- Roluri (Admin, User, Viewer)

**Tehnologii**:
- FastAPI Security, OAuth2, Password Hashing (bcrypt)

**Complexitate**: Medie

---

### 2. Notificari Automatice

**Ce adauga**:
- Email/SMS cand sunt detectate violari critice

**Tehnologii**:
- FastAPI Background Tasks, Celery (pentru task-uri asincrone)

**Complexitate**: Usoara

---

### 3. Integrare cu Dispozitive in Timp Real

**Ce adauga**:
- Websockets pentru a primi date in timp real de la dispozitive

**Tehnologii**:
- FastAPI WebSockets, Redis (ca message broker)

**Complexitate**: Medie

---

### 4. Rapoarte Avansate si Exporturi

**Ce adauga**:
- Export in PDF, Excel, CSV
- Rapoarte programate

**Tehnologii**:
- ReportLab, Pandas, APScheduler

**Complexitate**: Medie

---

### 5. Multi-Tenant

**Ce adauga**:
- Suport pentru multiple companii/organizatii izolate

**Tehnologii**:
- SQLAlchemy, FastAPI Dependencies

**Complexitate**: Ridicata

---

### 6. Aplicatie Mobila

**Ce adauga**:
- Aplicatie mobila pentru iOS si Android

**Tehnologii**:
- React Native sau Flutter

**Complexitate**: Ridicata

---

### 7. AI Model Local (fara ModelArk)

**Ce adauga**:
- Model AI local pentru analiza chart-urilor si text

**Tehnologii**:
- PyTorch/TensorFlow, Hugging Face Transformers

**Complexitate**: Foarte Ridicata

---

## Prioritati

| Prioritate | Extindere |
|------------|------------|
| Inalta | Autentificare si Autorizare |
| Medie | Notificari Automatice |
| Medie | Integrare cu Dispozitive in Timp Real |
| Medie | Rapoarte Avansate |
| Medie | Multi-Tenant |
| Scazuta | Aplicatie Mobila |
| Scazuta | AI Model Local |

