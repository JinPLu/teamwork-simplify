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
- Verify the requested behavior with the nearest useful checks. After they
  pass, broaden or repeat testing only for a new change, failure or unresolved
  concern; do not turn scratch checks into permanent test scaffolding.

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
- Do not add what was not asked for: no SHA-256 or other integrity hash; no
  preemptive or defensive layer for a nonexistent caller; no audit receipt,
  self-verification scaffolding, or retry wrapper. An agent's own judgment
  that a mechanism is "necessary" is not a reason to add or keep it — only a
  user-named requirement, a current real consumer, or an observed failure is.

## Claims and reporting

- Do not claim an unexecuted, unobserved action, test, effect, or result.
  Label each conclusion observed or inferred, and name what remains unknown.
  Plans, documents, tests, and metrics record work; they do not replace
  visible progress. A delegated line's own report that it succeeded is not
  verification: check it on the real path before you carry it forward.
- Give brief progress updates at key findings, direction changes and real
  blockers. Report results in natural Chinese: what changed, the evidence, the
  unknowns, the next action or blocker. A diagram and running example are
  aids, not a gate — use them whenever they help follow a parameter flow,
  data flow, architecture, or causal story.

## Native execution

- Clear work finishes natively. Name a Skill when the request matches its
  description. When you hand a slice to another agent, give it the objective,
  the paths it owns, what is already settled, and what to return.
- Balance speed, cost, and quality yourself across the models and reasoning
  effort you can call, and give each line the tier its own character asks for.

## Project context

- Before work that depends on a project's earlier decisions, conclusions or
  attempts, read its `docs/teamwork/README.md` if present, then follow the
  relevant links. An independent clear task needs no context survey.
- Save a result in the same turn when a later session will need it and it
  cannot be reconstructed from the repository without rereading this chat.
  Do not duplicate code structure, git history, reproducible checks or transient
  todos. Respect host write permissions; persist when writing is allowed.
- Reuse the existing file for the same subject and update its current synthesis.
  Keep consequential user goals, decisions, constraints, rejection reasons and
  corrections verbatim, separate from the agent's concise interpretation and
  evidence. Preserve existing history; record the date and reason of important
  decision changes, not every wording edit.
- Keep a short current state and links to still-useful records in the README;
  create it with the first saved result if absent, and update the relevant index
  entry when writing. The index is curated, not an inventory of every file.
  Old metadata does not determine whether a record belongs in it.
- Use plain Markdown and existing project organization. The default folders are
  `discussions/`, `plans/`, `records/`, `experiments/` and `guides/` under
  `docs/teamwork/`; these are conventions, not a closed set. No fixed title,
  frontmatter or History section is required. Keep existing paths; do not
  migrate old records merely to fit a template.
