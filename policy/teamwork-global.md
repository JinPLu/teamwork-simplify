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

- Clear work finishes natively. Name a Skill only when the request matches
  its description's trigger. Delegation carries five fields:
  objective, owned scope, settled constraints, available evidence, requested
  return. A missing optional role does not block native work. After the user
  accepts a reusable semantic result — a plan, decision, diagnosis,
  conclusion, or verdict — apply the matching Persistence even without
  explicit invocation; persistence follows the visible result and does not
  replace the next real action.
