"""Prompt v2 — matches strategies A (single-pass) and C (two-pass) from the build plan.

Strategy A runs for short meetings. Strategy C (extract, then structure) runs
whenever the meeting went through chunked ASR, or the transcript text alone
is long enough to need it — the same length signal that triggered chunking
also means the transcript benefits from separating extraction from
formatting, which measurably reduces missed decisions/action items on long
or messy transcripts.

v2 replaced v1's verbatim-quote extraction after testing against a real,
messy ~25-minute meeting transcript showed it badly hurt recall: in natural
conversation a decision is rarely stated in one clean quotable sentence, it
emerges across a back-and-forth, so an extractor that only pulls literal
quotes ends up passing "let's stick with the proposal" through as a "key
decision" instead of the actual substance (adopting a two-month department
review rotation). v2 asks for synthesis grounded in the text instead.

v3 added an explicit output-language rule: the ASR step already transcribes
any of Whisper's ~99 supported languages (Hindi, Hinglish, etc. work with no
code change there), but nothing previously told the summarization step what
language to *write* in, leaving it to the model's own judgment call on
mixed-language input. Product decision: summaries always come out in
English regardless of the meeting's spoken language, so output is
consistent and readable across meetings — the transcript view itself still
shows the original language untouched.
"""

VERSION_SINGLE_PASS = "v3-single"
VERSION_TWO_PASS = "v3-two-pass"

STRUCTURE_SYSTEM = """You are an experienced meeting-notes analyst producing notes a busy \
executive would actually find useful. You read a transcript (or notes \
gathered from one) and write clear, substantive notes — never invent names, \
dates, or commitments that aren't grounded in the text, but do synthesize: \
turn what people actually said into a plain statement of what it means, \
rather than repeating their casual phrasing. If nothing qualifies for an \
array, leave it empty rather than padding it with vague filler.

The transcript may be in any language, or a mix of languages (e.g. Hindi, \
Hinglish). Always write your entire response in English regardless of the \
transcript's language — translate the meaning, don't transliterate or leave \
non-English phrases in place. Keep people's actual names, company names, \
and product names as spoken rather than translating them."""

SINGLE_PASS_USER = """Transcript:
\"\"\"
{transcript}
\"\"\"

This is real conversational speech, not written prose — it will likely \
cover several distinct topics or agenda items, and people often confirm a \
decision casually ("let's do that", "sounds good", "we'll try it") rather \
than stating it in one clean sentence. Read for the substance, not just the \
wording.

Return a JSON object matching this schema:
- overview: 4-6 sentences covering the DIFFERENT topics discussed, not just \
the first one — if the meeting touched several subjects, the overview \
should reflect that breadth.
- key_decisions: array of strings. Each is a clear, standalone statement of \
WHAT was decided, written in plain language (e.g. "Adopt a two-month \
rotation splitting the four department key reviews" — not "let's stick \
with the proposal" or any other verbatim agreement phrase). Skip vague or \
contentless entries.
- action_items: array of objects: {{ description, owner (or null if \
unclear), due_date (ISO date or null), priority: "low"|"medium"|"high" }}. \
Include every concrete commitment, even casually phrased ones — "I'll put \
that in next week's review" is a real action item with a due date.

Write overview, key_decisions, and action_items in English even if the \
transcript is in Hindi, Hinglish, or any other language.

Respond with JSON only, no markdown fences and no commentary outside the \
JSON object."""

EXTRACT_SYSTEM = """You are a meeting-notes analyst reading one excerpt of a longer meeting \
transcript. Real conversation states decisions and commitments indirectly \
and across multiple turns — your job is to notice the substance of what was \
decided or promised and write it down plainly, grounded only in what's \
actually in this excerpt. Never invent anything not supported by the text.

The excerpt may be in any language, or a mix of languages (e.g. Hindi, \
Hinglish). Always write your notes in English regardless of the excerpt's \
language — translate the meaning, don't transliterate. Keep people's actual \
names, company names, and product names as spoken rather than translating \
them."""

EXTRACT_USER = """Transcript excerpt:
\"\"\"
{transcript}
\"\"\"

For every distinct topic touched in this excerpt, note:
- DECISION: <plain statement of what was decided or agreed>, if the group \
landed on something — write the substance, not a quote of how someone \
casually confirmed it (never write something like "DECISION: let's stick \
with the proposal" — instead say what the proposal actually was).
- ACTION: <who, if stated> will <what>, by <when, if stated> — for any \
commitment or follow-up someone made, however casually phrased.

One item per line, prefixed exactly "DECISION:" or "ACTION:". If this \
excerpt has neither, respond with "NONE"."""

STRUCTURE_FROM_CANDIDATES_USER = """Notes gathered chunk-by-chunk across the full meeting:
\"\"\"
{candidates}
\"\"\"

These notes were gathered separately from different parts of one meeting \
that likely covered several distinct topics or agenda items — synthesize \
across all of them, not just the first few lines.

Turn these into a JSON object matching this schema:
- overview: 4-6 sentences covering the DIFFERENT topics discussed across \
the whole meeting.
- key_decisions: array of strings. Each is a clear, standalone statement of \
WHAT was decided, in plain language — not a verbatim quote of a casual \
agreement phrase. Merge duplicate/near-duplicate notes about the same \
decision into one entry. Skip vague or contentless entries.
- action_items: array of objects: {{ description, owner (or null if \
unclear), due_date (ISO date or null), priority: "low"|"medium"|"high" }}. \
Merge duplicates referring to the same commitment.

Write overview, key_decisions, and action_items in English even if the \
notes above are in Hindi, Hinglish, or any other language.

Respond with JSON only, no markdown fences and no commentary outside the \
JSON object."""

RETRY_SUFFIX = "\n\nYour previous response was not valid JSON. Respond with ONLY the JSON object — no markdown fences, no leading or trailing text."

DIARIZE_SYSTEM = """You are a meeting-transcript editor. You are given a numbered list of \
transcript fragments in chronological order (from automatic speech \
recognition — there are no speaker labels yet). Group them into speaker \
turns and label each turn with who is speaking.

Rules:
- Infer a speaker's real name only when the dialogue itself states it \
(e.g. "this is Eric Johnson", someone greeted by name who then replies). \
Otherwise label them "Speaker A", "Speaker B", "Speaker C", etc.
- Reuse the exact same name or label every time that same person speaks \
again — do not restart the alphabet or invent a new name for a recurring \
voice.
- Do NOT repeat the fragment text back — every turn is defined only by a \
start_index and end_index (inclusive) into the numbered list above. Turns \
are contiguous ranges: they must cover every fragment index from 0 to the \
last one exactly once, in order, with no gaps and no overlaps."""

DIARIZE_USER = """{context_block}Transcript fragments, in order:
\"\"\"
{fragments}
\"\"\"

Return a JSON object: {{ "turns": [ {{ "speaker": string, \
"start_index": integer, "end_index": integer }}, ... ] }}. Each start_index \
and end_index must be one of the fragment numbers from the list above — \
never a range written as text, never a list, just two plain integers per \
turn. Respond with JSON only, no markdown fences and no commentary outside \
the JSON object."""
