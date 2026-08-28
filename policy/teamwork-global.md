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

## Teamwork bridge

- Clear work finishes natively; name a Skill only when the request matches its
  description's trigger. Delegation carries objective, owned scope, settled
  constraints, available evidence, requested return; a missing optional role does
  not block native work. A project's `AGENTS.md` Teamwork block adds
  project-specific detail on top of this contract and does not restate it.
- Persistence fires when the user accepts a reusable semantic result, Skill named
  or not, and is written in that same response cycle. An ordinary next action is
  not a checkpoint; chat, host plans, and todos are not memory.
- Kind is the first match in this order. `experiments/`: one executed trial with
  its command or config and observed numbers — identity is the claim under test
  plus that setup. `plans/`: ordered steps toward a selected outcome, not yet
  carried out — identity is that outcome. `records/`: an outcome already reached
  — a result, conclusion, verdict, or blocker — identity is the continuing
  objective. `discussions/`: an option space, recommendation, or open-question
  batch still undecided — identity is the final goal plus the subject.
- Same identity, same path: list `docs/teamwork/<kind>/` and read each file's
  frontmatter and identity lines. On a match append a dated History entry and
  refresh the top synthesis and `updated`, following `superseded-by` first when
  that file is superseded; with no match create `docs/teamwork/<kind>/<slug>.md`,
  `<slug>` being the identity in lowercase ASCII kebab-case.
- Shape: frontmatter `status`, `superseded-by`, `created`, `updated`; current
  synthesis on top; append-only dated History at the bottom, a correction being a
  new entry and never a rewrite; the user's original wording kept separate from
  your working understanding.
