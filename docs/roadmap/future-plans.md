# Proposed Extensions

Future extensions for MED-THERM.

---

## List of Extensions

### 1. Authentication and Authorization

**What it adds**:
- Login/Register
- JWT tokens
- Roles (Admin, User, Viewer)

**Technologies**:
- FastAPI Security, OAuth2, Password Hashing (bcrypt)

**Complexity**: Medium

---

### 2. Automatic Notifications

**What it adds**:
- Email/SMS when critical violations are detected

**Technologies**:
- FastAPI Background Tasks, Celery (for async tasks)

**Complexity**: Low

---

### 3. Real-Time Device Integration

**What it adds**:
- WebSockets to receive real-time data from devices

**Technologies**:
- FastAPI WebSockets, Redis (as message broker)

**Complexity**: Medium

---

### 4. Advanced Reports and Exports

**What it adds**:
- Export to PDF, Excel, CSV
- Scheduled reports

**Technologies**:
- ReportLab, Pandas, APScheduler

**Complexity**: Medium

---

### 5. Multi-Tenant

**What it adds**:
- Support for multiple isolated companies/organizations

**Technologies**:
- SQLAlchemy, FastAPI Dependencies

**Complexity**: High

---

### 6. Mobile Application

**What it adds**:
- Mobile app for iOS and Android

**Technologies**:
- React Native or Flutter

**Complexity**: High

---

### 7. Local AI Model (without ModelArk)

**What it adds**:
- Local AI model for chart and text analysis

**Technologies**:
- PyTorch/TensorFlow, Hugging Face Transformers

**Complexity**: Very High

---

## Priorities

| Priority | Extension |
|----------|-----------|
| High | Authentication and Authorization |
| Medium | Automatic Notifications |
| Medium | Real-Time Device Integration |
| Medium | Advanced Reports |
| Medium | Multi-Tenant |
| Low | Mobile Application |
| Low | Local AI Model |
