## Context

The MED-THERM Compliance Platform requires a foundational PostgreSQL database schema to support medical device regulatory compliance tracking. This involves:
- Device inventory management
- VLLM analysis session tracking for document/image processing
- High-volume time-series log entry storage
- Regulatory violation detection tracking with REG-* codes
- Compliance report persistence
- Immutable audit logging for regulatory compliance (REG-DATA-1)

**Constraints**:
- PostgreSQL with SQLAlchemy ORM
- Alembic for database migrations
- Must support time-series queries efficiently
- `audit_log` table must be immutable (no UPDATEs, no DELETEs)

## Goals / Non-Goals

**Goals:**
- Define SQLAlchemy models for all 6 tables
- Create Alembic migrations for schema creation
- Optimize `log_entries` table for time-range queries
- Enforce `audit_log` immutability at database level
- Link detected violations to REG-* regulatory codes and severity levels

**Non-Goals:**
- Data migration from existing systems (no legacy data)
- Query layer implementation (beyond indexes)
- API endpoint implementation

## Decisions

### 1. Table Naming Convention
**Decision**: Use snake_case for table and column names (SQL convention)
**Rationale**: PostgreSQL convention, consistent with SQLAlchemy's typical usage
**Alternatives considered**:
- PascalCase - Not standard in SQL databases
- camelCase - Can cause case-sensitivity issues in PostgreSQL

### 2. Primary Key Strategy
**Decision**: Use UUID (UUID v4) as primary keys for all tables
**Rationale**: 
- Better for distributed systems
- Avoids ID enumeration security concerns
- Consistent pattern across all tables
**Alternatives considered**:
- SERIAL/BIGSERIAL auto-increment integers - Simpler but less secure for APIs

### 3. Time-Series Indexing for log_entries
**Decision**: Composite BRIN index on `(device_id, timestamp DESC)` + B-tree on `timestamp`
**Rationale**:
- BRIN indexes are much smaller than B-tree for time-series data
- Devices typically report data in time-order (ideal for BRIN)
- B-tree on `timestamp` alone supports cross-device time-range queries
**Alternatives considered**:
- B-tree only - Larger index size, slower bulk ingest
- Partitioning by time - More complex for initial PoC

### 4. audit_log Immutability
**Decision**: PostgreSQL row-level security policy + REVOKE UPDATE/DELETE on table
**Rationale**:
- Enforced at database level (cannot bypass from application)
- REG-DATA-1 compliance requires immutable audit trails
**Alternatives considered**:
- Application-only enforcement - Can be bypassed

### 5. Regulatory Code Reference
**Decision**: Store `reg_code` as VARCHAR (e.g., "REG-TEMP-1") with a `severity` ENUM
**Rationale**:
- REG-* codes are well-defined and stable in MED-THERM-2026
- Severity levels are standardized (Critical > High > Medium > Low > Info)
**Alternatives considered**:
- Separate lookup table - Over-engineering for PoC

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Log entries table grows very large | BRIN indexes minimize storage overhead; future partitioning possible |
| UUID primary keys have performance impact on INSERTs | Acceptable for PoC; sequential UUID (UUID v1/v7) optimization available later |
| Immutable audit_log complicates debugging | Add detailed context columns; errors go to separate application logs |
| Migration rollback complexity | Alembic supports both upgrade and downgrade paths |

## Migration Plan

1. **Create initial migration**: Alembic revision with all table definitions
2. **Apply indexes**: Include indexes in the same initial migration
3. **Apply security policies**: RLS policies for audit_log in separate migration
4. **Verify**: Inspect schema with psql, run test queries

**Rollback Strategy**: Alembic downgrade drops tables/indexes/policies in reverse order.

## Open Questions

- None at this stage
