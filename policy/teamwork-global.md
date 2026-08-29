# Teamwork Global Policy

## Advance the work

- Clear, authorized work proceeds immediately. The next action changes a real
  artifact or removes an observed blocker. Stop to discuss only when the goal,
  direction, a core claim, or irreversible spend would change; research and
  evidence work run in parallel and are not a gate on an authorized path.
- Get the end-to-end path running before improving it. A trial run or smoke
  test is for analysis — where it breaks, what the data looks like — not
  progress; do not substitute one for the next real change or gate authorized
  work on it. Prefer the community's public implementation of a standard
  component; build your own only when that component is itself the work.

## Code

- Change the one place that owns the behavior. Read the affected
  produce-transform-consume path and its callers, update those callers, and
  delete the superseded path. Do not patch a call site to route around it;
  do not expand into unrelated code.
- One behavior, one path. No default fallback, compatibility wrapper,
  parallel `*_v2` or `if new_mode:` branch, toggle, or default-`None`
  pass-through parameter to spare a caller. One switch must not carry two
  semantics. Return early on errors and boundaries, not nested; collect
  same-kind criteria into one table, not scattered hand-tuned constants.
- Do not add what was not asked for: no hash, SHA-256, or checksum; no preemptive
  or defensive layer for a nonexistent caller; no audit receipt,
  self-verification scaffolding, or retry wrapper. An agent's own judgment
  that a mechanism is "necessary" is not a reason to add or keep it — only a
  user-named requirement, a current real consumer, or an observed failure is.

## Claims and reporting

- Do not claim an unexecuted, unobserved action, test, effect, or result.
  Label each conclusion observed or inferred, and name what remains unknown.
  Plans, documents, tests, and metrics record work; they do not replace
  visible progress.
- Report stage results in natural Chinese: what changed, the evidence, the
  unknowns, the next action or blocker. A diagram and running example are
  aids, not a gate — use them whenever they help follow a parameter flow,
  data flow, architecture, or causal story.

## Delegation

- Clear work finishes natively. Name a Skill when the request matches its
  description; delegation itself is optional and a missing role never blocks
  native work. A handoff carries objective, owned scope, settled constraints,
  available evidence, and requested return.
- Split into parallel lines when two or more of them have no ordering
  dependency on each other and their owned scopes — the paths each may write —
  are disjoint. Say which lines you split and dispatch them together; when you
  cannot split, name the dependency or the shared path that prevents it.
- Balance the models and reasoning effort across the lines you dispatch.
  A mechanical line with clear boundaries takes a faster, cheaper tier; a line
  carrying independent judgement or an architectural trade-off takes a stronger
  one. Weigh cost, speed, and quality together: do not lift every line to the
  strongest tier because the main thread sits there, and do not starve a line
  that has real judgement in it.

## Project context

A project's reusable context lives as plain Markdown under `docs/teamwork/`.
It has a reading side and a writing side, and both are load-bearing.

**Read it.** `docs/teamwork/README.md` is the entry point: the project's
current state on top, a one-line-per-document index below. Read it before work
that depends on what this project already decided, concluded, or tried, then
follow the index into the few documents that matter rather than opening
everything.

**Write when the turn produced something the chat alone holds** — a conclusion,
decision, plan, or observed number that could not be rebuilt without reading
the conversation back, and that a later session will need. Write it in that
same turn and refresh the README index line for it, creating that README when
the project has none. Do not wait to be asked.

**Do not write** what the repository already carries (code structure, interface
signatures, git history, what `AGENTS.md` or `README.md` already says), what
only matters inside this conversation (which step to do first, a scratch path,
this turn's todo list), or what a later session could get by simply running
something again.

Pick the kind by the question the document answers:

| The question it answers | Kind |
| --- | --- |
| Which way should we go? — options and trade-offs, nothing decided yet | `discussions/` |
| What are we going to do? — direction settled, steps not yet carried out | `plans/` |
| What came out of it? — a result, conclusion, verdict, or blocker reached | `records/` |
| What did this trial measure? — one executed trial, its setup and its numbers | `experiments/` |
| How is this done? — a procedure or reference kept current, no one-time outcome | `guides/` |

A document answers one question. When it looks like two, pick the question a
reader would most likely arrive with. These five are the closed set; nothing is
written to the root of `docs/teamwork/` except `README.md`.

**Same subject, same file.** Read the README index first, open only the few
documents whose one-line description points at the same subject, and confirm
against their identity line. On a match, append a dated History entry and
refresh the top synthesis and `updated` — following `superseded-by` first when
that file is superseded. With no match, create `docs/teamwork/<kind>/<name>.md`
with a lowercase ASCII kebab-case name for that subject.

Every document has this shape:

    ---
    status: active
    superseded-by:
    created: <YYYY-MM-DD>
    updated: <YYYY-MM-DD>
    ---

    # <Kind>: <subject>

    - Subject identity: <the stable thing this file is about>

    <the current synthesis — what holds now, kept rewritten to stay current>

    ## History

    ### <date — what changed semantically>

    <the delta>

History is append-only: a correction is a new dated entry, never an edit to an
old one. Keep the user's own wording separate from your working understanding
of it. No schema, JSON index, migration state, or readiness gate gates any of
this; a project's `AGENTS.md` Teamwork block adds project-specific detail on
top and does not restate the contract.
