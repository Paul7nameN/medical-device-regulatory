## 1. Fix Upload.tsx Hardcoded Badges

- [x] 1.1 Analyze `uploadResult` structure from various API responses
- [x] 1.2 Create type guards to detect response type (TXT vs Image)
- [x] 1.3 For TXT uploads: Extract `report.passed_count`, `report.failed_count`, `report.critical_count`
- [x] 1.4 For Image uploads: Calculate from `result.violations.length`
- [x] 1.5 Replace hardcoded badges with dynamic values
- [x] 1.6 Hide badges if structure is unknown (hasData check)

## 2. Fix Reports.tsx Static Sample Data

- [x] 2.1 Import `useAnalysis` hook from `@/lib/context/AnalysisContext`
- [x] 2.2 Access `latestAnalysis` and `severityCountsByCategory` from context
- [x] 2.3 Add empty state check: if no data, show proper empty state card
- [x] 2.4 Replace static `categoryData` array: Build from `severityCountsByCategory`
- [x] 2.5 Replace static `severityData` array: Aggregate from `severityCountsByCategory`
- [x] 2.6 Hide `trendData` chart (weekly trend) - no historical data stored
- [x] 2.7 Remove/hide static `reports` history table
- [x] 2.8 Replace hardcoded `ComplianceScore` props: Calculate from actual data

## 3. Test & Verify

- [ ] 3.1 Upload a .txt file with known violations
- [ ] 3.2 Verify Upload page badges match actual counts from validation
- [ ] 3.3 Verify Reports page shows counts from context, not static data
- [ ] 3.4 Verify empty state appears when no data
