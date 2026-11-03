# Research communication contract: conclusion first, evidence attached

This is the Hub-facing authoring and compatibility contract for OpenRA's
existing interaction and reporting skills. It is **not another installable
chat skill**, not an entry manifest and not permission to modify a user's
installed third-party packages. Built-in `ora-*` skills remain bundled in
[OpenRA](https://github.com/HuieL/OpenRA/tree/main/agent-skills), rather than
duplicated in this catalog. Do not create an `ora-chat` alias for the same job.

## Owners and default activation

| Concern | Existing owner |
| --- | --- |
| Agent–human answers, milestones, experimental synthesis, supported rich blocks | `ora-research-ui` |
| Durable reports and project-result summaries | `ora-reports` |
| Inspected run facts, comparability and knowledge-candidate status | `ora-evidence` |
| Manuscripts, author-approved plans, scoped candidates and section-specific writing | `ora-paper` and its existing references |

OpenRA's [session playbook](https://github.com/HuieL/OpenRA/blob/main/SYSTEM_PROMPT.md)
injects a compact conclusion-first communication contract on every turn and
instructs the agent to load enabled `ora-research-ui` at the first user-facing
turn. No user slash command is needed. The existing Local skill set provides
that skill by default; explicit project/session disabling is respected. Full
report/paper procedures stay task-specific. This is a host policy, **not a new
`alwaysLoad` frontmatter field, hook, model/tool permission or catalog API**.
Native materialization, prompt delivery and model obedience are distinct:
source-level checks are not evidence of a live session following a rule.
An already running old OpenRA binary must be updated through the normal build/
release path; changing this repository does not hot-update its embedded prompt.

For external harnesses, install/enable the intended skill explicitly through
the harness's existing mechanism. Do not claim that catalog discovery alone
loads a skill, or that a description forces automatic invocation. Preserve
package hashes, version pins, approval and disabled state. A registry refresh
does not install, enable, publish or grant access to anything.

## Information order, not a rigid response template

**Conclusion → decisive evidence → uncertainty/implication → useful next action.**
Lead with the supported answer, actual result, decision or precise blocker.
A null/negative result or insufficient evidence is a valid conclusion. Put a
qualifier that changes the conclusion in the opening, not only at the bottom.
Then bind each important claim to its decisive inspected evidence and explain
what it means. Add a bounded next action only when a real open decision remains;
do authorized work instead of routinely handing it back to the user.

Match the language, requested format and audience. Short answers need no
compulsory headings. Long explanations retain their full requested detail.
A focused first screen is not a limit on sources, counterexamples or analysis.
Do not manufacture confidence percentages, timing, scientific significance,
causal claims or successful execution to make the answer sound decisive.

## Experimental synthesis and conversational continuity

Group related runs by the research question. Report the current finding, what
new evidence changed it, the remaining gap and the consequence for the next
choice. Do not emit a separate conclusion or report for every tool call or run.
Use the existing report, hypothesis notes, Run/Evidence or knowledge candidate;
never introduce a parallel progress ledger merely for this style rule.

Keep baseline/control, metric/unit/direction, dataset/split, effective budget,
run/seed counts and meaningful exclusions with the result. Check comparability
before pooling observations. Inspected output is different from status or exit
code; operational failure is different from a refuted hypothesis. Partial data
support only a bounded observation about the inspected subset, not a full-batch
verdict. Preserve null/negative results and counterevidence; label an inferred
mechanism as inferred. A summary does not upgrade human review or adoption.
When evidence reverses an earlier conclusion, say so and retain the old sources.

## Reports and paper writing

`ora-reports` replaces Task/Scope/Sources-first presentation with an executive
answer, evidence-bearing findings, material limitations, a useful decision when
needed, and full methods/scope/reproducibility. Each conclusion has a locator;
a source list is not sufficient proof of support. Necessary qualifications stay
next to the headline too. Follow-up outputs revise the existing question-level
synthesis without overwriting already-published artifacts or stable citations.

The paper family receives an **addendum only**. Preserve confirmed author intent,
venue/IMRaD structure, argument-writing and section references, citation rules,
human candidate acceptance and locks. Make the central contribution and scope
easy to find, and open Results paragraphs with their scoped finding where
appropriate. Definitions, proofs, methods and derivations keep their logical
order. Do not paste a chat template into every manuscript section, strengthen
claims during polishing, launch unsolicited experiments or self-accept prose.

## UI, permissions and fallback

Reuse OpenRA's current `research-step` and `openui` schemas. Put a takeaway before
the card when useful; do not invent payload keys or renderer capabilities.
Traceability uses real inspected references. When rich UI is unavailable, readable
plain text must carry the same answer and caveats. Rendering a summary is not
verification, publication approval, permission to share private sources or a
reason to bypass a required user decision. Read only the current authorized
conversation/context; do not combine private member messages to make a group
summary without permission.

## Acceptance scenarios for maintainers

| Scenario | Required behavior |
| --- | --- |
| Three launches, only one inspected completed run | State partial coverage; no aggregate win, no invented pending results |
| New counterexample invalidates a previous headline | Correct the headline, cite both evidence scopes, preserve history |
| Command succeeded but did not measure the target outcome | Report execution success separately; scientific answer remains unknown |
| Long experiment report | Supported answer first; findings bind to evidence; full methods and negative results remain accessible |
| Local manuscript wording request | Requested candidate first; original argument/venue and human acceptance remain unchanged |
| Task complete, no remaining decision | End without a fabricated follow-up or time estimate |
| Rich block or optional skill disabled | No fabricated UI or forced re-enabling; use the permitted plain-text fallback |

These are behavioral evaluation criteria, not a claim that all models or harnesses
have passed them. Tests of source text alone cannot establish model adherence.

## Attribution

Presentation ideas are adapted from Ayoub Ghriss,
[ayghri/i-have-adhd at 1ecea1993b7fce257ffbd686c070948b5e07eda6](https://github.com/ayghri/i-have-adhd/blob/1ecea1993b7fce257ffbd686c070948b5e07eda6/skills/i-have-adhd/SKILL.md).
OpenRA does not infer a diagnosis, require speculative time estimates, hard-cap
important evidence or suppress meaningful uncertainty. Existing research,
evidence and manuscript-writing procedures remain authoritative in their scope.

MIT License — Copyright (c) 2026 Ayoub Ghriss

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
