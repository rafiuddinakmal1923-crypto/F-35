# Back-test report (simulated data)

Generated in 57 s by `scripts/backtest.py --source simulated`. Detection was run as of every 1 day(s) from day 14 to day 61, each time seeing only the readings up to that day.
Ranked = the premise's zone was flagged or had no balance, so the pipeline ranked it. Top 5% = within the zone's top 5%.

| Premise | Zone | Case | Theft starts | First day zone flagged | First day in top 5% | Rank on the last day |
| --- | --- | --- | --- | --- | --- | --- |
| P-CEN-001-054 | TX-CEN-001 | full_bypass_mining | 2026-08-01 | 2026-08-14 | 2026-08-14 | 1 |
| P-CEN-001-049 | TX-CEN-001 | partial_bypass | 2026-09-08 | 2026-08-14 | 2026-09-10 | 2 |
| P-CEN-002-029 | TX-CEN-002 | full_bypass_mining | 2026-08-31 | 2026-09-06 | 2026-09-06 | 1 |
| P-CEN-004-032 | TX-CEN-004 | partial_bypass | 2026-08-21 | not flagged | 2026-08-22 | 1 |
| P-NOR-001-012 | TX-NOR-001 | partial_bypass | 2026-08-26 | not flagged | no | - |
| P-NOR-002-035 | TX-NOR-002 | full_bypass_mining | 2026-08-21 | 2026-08-27 | 2026-08-27 | 1 |

5 of 6 known cases reached their zone's top 5% at some point in the period.
On simulated data this rehearses the R1 back-test; it says nothing about TNB data (SRS NFR-10, SDD OI-12).
