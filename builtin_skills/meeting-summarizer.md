---
name: meeting-summarizer
title: Meeting Summarizer
category: Meetings and follow-up
source: Adapted from the open-source summarize-meeting and lark-minutes-tasks skills
triggers: Meeting summary, minutes, decisions, action items, owners, deadlines, follow-up, transcript
description: Turn meeting notes or a transcript into decisions, actions, owners, deadlines, open questions, and follow-up items.
---
# Meeting Summarizer

**Invocation rule:** Apply this skill only when the student explicitly invokes it or asks for meeting minutes, a decision summary, action items, or follow-up from a meeting. Do not auto-apply it to every discussion.

## Purpose

Create a reliable record of what a meeting decided and what happens next. The skill separates discussion from decision and ensures every action has an owner and a date.

## Inputs

Gather:

- the meeting purpose, date, and attendees (roles are enough),
- the notes or transcript,
- the decisions and approvals,
- the action items,
- the open questions,
- the next meeting date.

If the notes do not contain a decision, do not invent one. Mark it as "not decided".

## Procedure

1. **State the purpose.** Summarize why the meeting happened in one sentence.
2. **Capture decisions.** Record each decision, the decision owner or forum, the rationale, and the effective date.
3. **Capture actions.** For each action, record:
   - the action,
   - the accountable owner role,
   - the due date,
   - the dependency,
   - the status.
4. **Capture open questions.** List what remains unresolved and who will resolve it.
5. **Capture risks.** Note any new risk, assumption, or escalation.
6. **Separate discussion from decision.** Do not present an idea as approved.
7. **Set follow-up.** State the next meeting, the review point, and what must be reported.

## Output format

Provide:

- a short meeting summary,
- a decisions table,
- an action table with owner and due date,
- open questions,
- risks and escalations,
- next meeting and follow-up.

## Quality checks

- No decision is invented.
- Every action has an owner and a date, or is marked as unassigned.
- Owners are roles, not invented names.
- Discussion is not misrepresented as agreement.
- Follow-up items are traceable.
- Local Markdown is sufficient; do not assume a Lark, Feishu, Notion, or calendar integration.
