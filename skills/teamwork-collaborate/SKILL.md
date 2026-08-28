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
   work by dependency, naming what each step produces. The first executable
   step must change the target artifact or remove an observed blocker.
   Benchmarks, appendices, probes, and extra documents are not prerequisites
   just because they would help explain something.
6. Split parallel lines only when they are genuinely independent with
   non-overlapping owned scope. Give each line one Worker handoff carrying
   the delegation fields the global policy defines, where this line's owned
   scope is a set of paths disjoint from every other line's. Do not split
   work that is not independent.
7. Root integrates each Worker's return, verifies it on the real path, and
   then reports. A Worker's return is not itself verification.
8. End with the decision, the unresolved points, and the next authorized
   action. When the direction is decided and the user authorizes execution,
   the discussion ends at that real action; do not open a new evidence gate
   or a new planning gate.

## Persistence

When a listed checkpoint fires, write in the same response cycle. If
separate stable identities each cross a checkpoint, write each to its own
path. Keep the user's original wording separate from the working
understanding. An ordinary next action by itself does not fire a checkpoint.
Root writes the checkpoint from the template below; an optional Writer may
carry out that write when doing so does not delay it, and never decides
document identity or what counts as material.

- `docs/teamwork/discussions/<slug>.md`, from `references/discussion.md`.
  Identity: the same final goal plus the same subject. Checkpoint: a
  decision, recommendation, or unresolved-question batch that will change
  later work.
- `docs/teamwork/plans/<slug>.md`, from `references/plan.md`. Identity: the
  same selected outcome. Checkpoint: the direction and scope are accepted,
  the first executable plan is accepted, or a material replan is accepted.
  Later edits reuse the same path; an added acceptance check or parallel
  concern does not open a new plan.
- `docs/teamwork/records/<slug>.md`, from `references/record.md`. Identity:
  the same continuing objective. Checkpoint: a result, conclusion, or
  blocker that later sessions can reuse.
- `docs/teamwork/experiments/<slug>.md`, from `references/experiment.md`.
  Identity: the same experiment. Checkpoint: the experiment has a result or
  a conclusion.
