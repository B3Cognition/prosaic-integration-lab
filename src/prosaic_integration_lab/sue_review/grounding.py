"""Generation-only clarification of canonical rules; never an answer validator."""
import hashlib

GROUNDING_GUIDANCE = """Apply these field relationships before returning the object, including on a retry:
- Choose test_result from responseSchema for the current operator and the matching verdict from the canonical rules. Decide from source support; do not choose success merely to continue the dialogue.
- UNKNOWN/SILENT means no source-grounded answer: evidence_lines=[] and evidence=[]. No stated or inferred premises are possible in that branch; premises may be empty, or contain only explicitly disclosed assumptions with evidence_lines=[]. claim=null. Explain the missing support in answer and open_questions. Do not attach contextual quotations to a SILENT answer.
- Every other verdict requires nonempty evidence_lines, exactly one evidence quote for each of those lines, and at least one stated or inferred premise. Every premise's evidence_lines must be a subset of the answer's evidence_lines. Assumptions always have empty evidence_lines.
- Copy each quote as an exact nonempty substring of its numbered source line. A stated premise's statement must itself occur verbatim inside one of its cited quotes. Combining or paraphrasing source sentences is an inference: label it inferred, cite its support and explain the inference in answer.
- groundingContext.sourceLineNumbers identifies source citations. groundingContext.priorTurnNumbers identifies accepted dialogue turns for addresses. These are different namespaces. addresses may contain only unique earlier dialogue turn numbers that this answer explicitly addresses; it is [] when there are no earlier turns.
- During DEFINE, interpret the source commitments relevant to the seed, with a testable proposition and scope. The seed is a question to examine, not an established source quotation; the text need not repeat its exact words. Do not invent a definition or erase unresolved normative choices. Supported/partial DEFINE or REVISE requires a nonempty claim; other operators require claim=null.
- A retry must satisfy all these rules, not merely change the verdict or delete one offending field. Return your own unmodified answer for independent canonical validation. No new tool, source or author assent is supplied by this guidance."""

GROUNDING_SHA256 = hashlib.sha256(GROUNDING_GUIDANCE.encode('utf-8')).hexdigest()
