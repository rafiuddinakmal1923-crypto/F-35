---
title: VoltGuard user guide - reading zones, scores and reasons
version: 0.1
owner: Team F-35
date: 2026-10-27
approved: true
role_scope: [inspector, analyst, supervisor, manager]
---

## 1. What a flagged zone means

A zone is all premises supplied by one distribution transformer. VoltGuard compares the energy the
transformer meter recorded with the energy recorded by customers' meters, plus an engineering
estimate of technical loss in the transformer and cables. When the unexplained gap stays above the
flag threshold plus an uncertainty margin for seven days in a row, the zone is flagged. A flag says
that energy is going somewhere it is not being metered; it does not say which premise or why.

## 2. Flat 24/7 gap

When the hourly gap profile is nearly constant across the day (flatness below 0.2), the hidden load
runs around the clock. Constant loads of this kind are typical of cryptocurrency mining rigs. For such
cases the dispatch suggestion recommends a joint operation with police rather than a lone inspector.

## 3. Risk scores and reasons

Each premise in a flagged zone gets a risk score from 0 to 100. The score ranks how strongly the
evidence matches patterns seen with theft; it is not a probability and never a finding that anyone
stole electricity. The premise page lists the three largest reasons plus an "other" line, and the
lines add up to the score. Legitimate patterns such as EV charging, rooftop solar or a vacant home
appear as negative reasons that lower the score.

## 4. Voltage evidence

A hidden load draws current that the meters do not record, which pulls down the voltage of meters on
the same phase and feeder branch, most strongly near the tap. The neighbour voltage strip shows the
unexplained drop along each branch and the estimated position of the hidden load. Meters on other
phases are barely affected.

## 5. Routine meter checks

Some visits are random routine meter checks drawn from all premises in flagged zones. They measure the
base rate of theft without bias and are recorded with the same outcome form.

## 6. Recording outcomes

Choose one outcome: Confirmed theft, False alarm, Inconclusive or No access. No access returns the case
for a revisit and is not used to train the model. Notes are scrubbed of names, IC numbers, phone
numbers and addresses before any agent or search sees them, but write only what the case needs.
