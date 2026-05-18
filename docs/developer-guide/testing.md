# Cum Rulezi Testele

Testele sunt in `backend/tests/`.

---

## Cum le rulezi

```bash
cd backend

# Toate testele
pytest -v

# Doar un singur fisier
pytest tests/test_engine.py -v

# Doar un test specific
pytest tests/test_engine.py::test_some_test -v
```

---

## Ce teste exista

| Fisier | Descriere |
|---------|-----------|
| `test_engine.py` | Regulatory engine |
| `test_parser.py` | Log parser |
| `test_ai_api.py` | AI API |
| `test_ai_client.py` | AI client |
| `test_ai_integration.py` | AI integration |
| `test_aggregator.py` | Aggregator |
| `test_image_analyzer.py` | Image analyzer |
| `test_severity_classifier.py` | Severity classifier |
| `test_temporal_analysis.py` | Temporal analysis |
| `test_text_analyzer.py` | Text analyzer |

---

## Structura testelor

Testele folosesc `pytest`.

### Exemplu de test:

```python
def test_temp_reading():
    line = "2026-05-14 14:00:10 TEMP_READING 4.3C"
    entry = parser.parse_line(line)
    assert entry.log_type == LogType.TEMP_READING
    assert entry.parsed_value == 4.3
```

---

## Coverage

Testele acopera:

- **Unit tests**: Toate tipurile de log cu date valide si invalide
- **Edge cases**: Linii goale, spatii, timestamp-uri malformate, tipuri necunoscute
- **Value parsing**: Temperaturi negative, zecimale, valori la limita, variatii de unitati
- **Pattern detection**: Toate cele 5 detectoare de pattern-uri regulatorii
- **Integration**: End-to-end cu fisier de log exemplu
```

