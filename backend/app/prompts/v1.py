"""Prompt v1 — matches strategies A (single-pass) and C (two-pass) from the build plan.

Strategy A runs for short meetings. Strategy C (extract, then structure) runs
whenever the meeting went through chunked ASR — the same length signal that
triggered chunking also means the transcript benefits from separating
extraction from formatting, which measurably reduces missed decisions/action
items on long or messy transcripts.
"""

VERSION_SINGLE_PASS = "v1-single"
VERSION_TWO_PASS = "v1-two-pass"

STRUCTURE_SYSTEM = """You are a meeting-notes analyst. You read a transcript and extract only \
what was actually said — never invent names, dates, or commitments that \
aren't in the text. If the transcript doesn't contain a clear decision or \
action item, leave those arrays empty rather than guessing."""

SINGLE_PASS_USER = """Transcript:
\"\"\"
{transcript}
\"\"\"

Return a JSON object matching this schema:
- overview: 3-5 sentence summary of what the meeting covered
- key_decisions: array of strings, each a single decision that was made
- action_items: array of objects: {{ description, owner (or null if \
unclear), due_date (ISO date or null), priority: "low"|"medium"|"high" }}

Respond with JSON only, no markdown fences and no commentary outside the \
JSON object."""

EXTRACT_SYSTEM = """You are a meeting-notes analyst. You read a transcript and pull out only \
lines that state a decision or a commitment someone made — quoted \
verbatim, no interpretation, no formatting."""

EXTRACT_USER = """Transcript:
\"\"\"
{transcript}
\"\"\"

List every line in this transcript that states a decision or a commitment \
someone made. For each one, quote it verbatim INCLUDING the speaker's name \
and enough of the surrounding sentence that the commitment, its owner, and \
what it refers to are all still clear on their own — for example \
"Sam: I'll get the migration doc to legal by Friday." rather than just \
"I'll get that to legal by Friday." One per line. If none, respond with \
"NONE"."""

STRUCTURE_FROM_CANDIDATES_USER = """Candidate decisions/commitments quoted from the meeting:
\"\"\"
{candidates}
\"\"\"

Turn these into a JSON object matching this schema:
- overview: 3-5 sentence summary of what the meeting covered, inferred from \
the candidates above
- key_decisions: array of strings, each a single decision that was made
- action_items: array of objects: {{ description, owner (or null if \
unclear), due_date (ISO date or null), priority: "low"|"medium"|"high" }}

Respond with JSON only, no markdown fences and no commentary outside the \
JSON object."""

RETRY_SUFFIX = "\n\nYour previous response was not valid JSON. Respond with ONLY the JSON object — no markdown fences, no leading or trailing text."
