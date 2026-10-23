---
name: invoice-sql
description: Repair an overdue-invoice aggregation query.
tools: write
---
Read packet.json and report.sql. Repair report.sql to implement the documented overdue-invoice report in SQLite. Handle invoices with no payments, multiple partial payments, full payment and overpayment. Include only OPEN invoices whose due date is strictly before the supplied asOf date. Outstanding balance per invoice is max(total_cents minus all payments, zero). Exclude zero balances. Count overdue invoices and sum positive outstanding cents per customer.

Return exactly the columns customer_id, overdue_count and outstanding_cents, ordered by customer_id. The file must contain one read-only SQL query, with optional common table expressions. Do not change packet.json, create other files, or fetch external data. Briefly confirm completion when the query is saved. The grader supplies separate data fixtures, so implement the general rule rather than hardcoding sample results.
