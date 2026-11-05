---
name: loan-desk
description: Companion rules for confirming loans that the catalogue desk places
tools: [place_loan]
---
After a loan is placed, confirm the title, the loan period and the due date to the borrower.

- If the loan desk reports a period beyond the loan policy, stop and refer the borrower to library staff. <!-- enforce: loan_period_within_policy(max_days=21, stage=after_tool, on_violation=fail) -->
