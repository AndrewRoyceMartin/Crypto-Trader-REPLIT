# UI Audit Report - Signals & ML Page

## Summary
- **Timestamp**: 2025-09-11T07:42:56.673Z
- **URL**: http://127.0.0.1:5000/signals-ml
- **Errors**: 2
- **Warnings**: 2
- **KPIs Found**: 7
- **Tables Found**: 0

## Issues Found

### Critical Errors (2)

**Potential hardcoded price fallbacks detected**
- Type: ERROR
- Details: Code should only use authentic OKX data
- Fix: Remove any hardcoded price fallbacks, throw errors for missing OKX data


**Missing stable data attributes**
- Type: ERROR
- Details: UI elements lack data-* attributes for reliable testing
- Fix: Add data-metric, data-table, data-value attributes to key elements


### Warnings (2)

**Loading skeletons may persist after data load**
- Details: hideLoadingSkeletons() function may not be called properly
- Fix: Ensure hideLoadingSkeletons() is called in all success paths


**Number parsing may be inconsistent**
- Details: Ad-hoc string manipulation for numbers
- Fix: Use centralized parseNumber/fmtCurrency utilities


## KPI Elements

- **Hybrid Signal Score** (hybridScore)
  - Found: ✅
  - Type: KPI
  - Has Loading State: ✅


- **Traditional Analysis Score** (traditionalScore)
  - Found: ✅
  - Type: KPI
  - Has Loading State: ✅


- **ML Prediction Score** (mlScore)
  - Found: ✅
  - Type: KPI
  - Has Loading State: ✅


- **ML Success Probability** (mlProbability)
  - Found: ✅
  - Type: KPI
  - Has Loading State: ✅


- **Signal History Table** (signalHistoryTable)
  - Found: ✅
  - Type: TABLE
  - Has Loading State: ✅


- **RSI Value** (rsiValue)
  - Found: ✅
  - Type: INDICATOR
  - Has Loading State: ✅


- **Volatility Value** (volatilityValue)
  - Found: ✅
  - Type: INDICATOR
  - Has Loading State: ✅


## Recommendations
1. Add stable data attributes to all KPI and table elements
2. Implement proper error handling for missing OKX data
3. Use centralized number parsing utilities
4. Ensure loading states are properly managed
5. Test with real data flows to verify accuracy
