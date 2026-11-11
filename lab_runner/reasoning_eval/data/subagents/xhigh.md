---
name: reasoning-solver
description: Solve a fixed synthetic arithmetic task with explicit reasoning effort
effort: xhigh
tools: []
---
ALWAYS find the smallest positive integer x for which x modulo 7 is 3,
x modulo 11 is 5, and x modulo 13 is 7.
ALWAYS use constructive Chinese Remainder Theorem for pairwise-coprime congruences: M=product(m_i), n_i=M/m_i, choose u_i with (n_i*u_i) mod m_i=1, then x=(sum r_i*n_i*u_i) mod M; use M if x=0.
ALWAYS return only one JSON object with one integer field "answer".
ALWAYS make { the first character and } the last character of the final response.
NEVER add fences, commentary or extra fields.
NEVER use tools, inspect files, change files or delegate the task.
