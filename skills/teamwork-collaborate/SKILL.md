---
name: teamwork-collaborate
description: Use when the user wants to think through a direction together, when unclear intent needs guided clarification, or when a settled direction needs an executable plan and a parallel work split; do not use for a single discoverable fact or work that is already clear to execute.
---

# Teamwork Collaborate

Root owns the conversation. Discussion and planning are one continuous
thread here: the goals, constraints, and rejections a discussion settles
carry straight into the executable plan in the same thread, instead of being
re-asked at a handoff into a separate planning step.

## Method

1. Rebuild the decision surface first: the final goal, prior work on this
   question, settled constraints and recorded rejections, and the unknowns
   that would change the goal or the acceptance criteria. Start from facts,
   constraints, and the goal; do not invent an option from nothing.
2. A stage is one layer of user-owned decisions. Ask every independent,
   valuable question for that stage together; defer questions that depend on
   this stage's answer to the next stage. Host UI limits on question count
   are not a limit here.
3. Develop only meaningfully different options. For each, state the main
   benefit, cost, assumption, and consequence. Resolve discoverable facts
   yourself; ask the user only for a preference or an authorization that
   cannot be discovered.
4. Recommend a direction when the evidence distinguishes one, and record the
   user's decision. Recorded rejections and decisions are the mainline:
   research results or a subagent's return must not restate them as a new
   question or reopen a settled dimension. Quote the user's decision; do not
   paraphrase it into a new problem. When the direction rests on one
   load-bearing assumption, an optional Challenger may attack that frozen
   assumption read-only before the decision is recorded; its absence does not
   hold up the decision.
5. Once the direction is settled, produce the executable plan in the same
   thread without re-asking settled constraints: verify project facts and
   observable acceptance, inspect the actual owners, interfaces,
   dependencies, and nearest available verification, and order outcome-sized
   work by dependency, naming what each step produces. Benchmarks,
   appendices, probes, and extra documents are not prerequisites just because
   they would help explain something.
6. State the split verdict for that ordered work, always: whether two or more
   steps have no ordering dependency on each other and owned scopes — sets of
   paths — that are disjoint. When they do, split those lines, carry the
   delegation fields the global policy defines, and dispatch each line through
   this host's own independent-execution surface, named in the host's own
   terms; the optional Worker role is the fallback when the host offers none.
   When they do not, name the dependency or the shared path that prevents it.
   Never leave the verdict unstated, and never split work that is not
   independent.
7. Root integrates each returned line and verifies it on the real path before
   reporting.
8. End with the decision, the unresolved points, and the next authorized
   action. When the direction is decided and the user authorizes execution,
   the discussion ends at that real action.

## Persistence

The global policy's Teamwork bridge owns the persistence contract: when a
checkpoint fires, which of the four kinds it is, how identity is judged, the
path it reuses, and the document shape. Follow it; do not restate or override
it here. `references/discussion.md`, `references/plan.md`,
`references/record.md`, and `references/experiment.md` are fuller skeletons of
that same shape — use the matching one when it is at hand, and write the
document either way. An optional Writer may carry out that write when doing so
does not delay it, and never decides document identity or what counts as
material.
