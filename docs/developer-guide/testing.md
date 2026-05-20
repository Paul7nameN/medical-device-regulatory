# How to Run Tests

Tests are in `backend/tests/`.

---

## How to run

```bash
cd backend

# All tests
pytest -v

# Single file only
pytest tests/test_engine.py -v

# Specific test
pytest tests/test_engine.py::test_some_test -v
```

---

## What tests exist

| File | Description |
|------|-------------|
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

## Test structure

Tests use `pytest`.

### Test example:

```python
def test_temp_reading():
    line = "2026-05-14 14:00:10 TEMP_READING 4.3C"
    entry = parser.parse_line(line)
    assert entry.log_type == LogType.TEMP_READING
    assert entry.parsed_value == 4.3
```

---

## Coverage

Tests cover:

- **Unit tests**: All log types with valid and invalid data

- **Edge cases**: Empty lines, whitespace, malformed timestamps, unknown types

- **Value parsing**: Negative temperatures, decimals, boundary values, unit variations

- **Pattern detection**: All 5 regulatory pattern detectors

- **Integration**: End-to-end with sample log file
