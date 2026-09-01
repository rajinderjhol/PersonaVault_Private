# UI Improvement Plan: Cognitive Narrative Stream

## Objective
Transform the raw, technical "Thought Stream" feed into a high-level, human-readable "Cognitive Narrative" stream by filtering out noise, aggregating orchestration steps, and cleaning up content.

## Background & Motivation
The current feed is an unfiltered dump of backend orchestration events. It is repetitive, technical, and contains system-level noise (e.g., "insight", internal status updates) that obscures the core reasoning process. Humans need to see *intent* and *results*, not every internal event.

## Proposed Solution
1.  **Event Filtering:** Define a whitelist of meaningful event types (e.g., "Planner", "Generator", "Judge") and ignore low-level technical events (e.g., "insight").
2.  **Phase Aggregation:** Aggregate related steps into logical cognitive phases:
    *   **Analysis & Retrieval**: Planner, Router, Empathy, Retriever.
    *   **Generation & Evaluation**: Generator, Judge.
    *   **Finalization**: Episodic, Semantic.
3.  **Content Sanitization:** Implement regex cleaning to remove technical prompts (e.g., "DRAFT DOCUMENT:", "INSTRUCTIONS:").
4.  **Visual Grouping:** Use layout and styling to clearly distinguish between 'Phase Start', 'Insight', and 'Result'.

## Implementation Steps
1.  **Refactor `appendThought` in `base.html`**: Update the thought feed rendering logic to implement the whitelist filter, phase-based aggregation, and regex sanitization.
2.  **State Management**: Introduce a basic state machine within the JavaScript to track if a new phase has begun, reducing duplicate logs of the same action.
3.  **Styling Enhancements**: Apply cleaner, more readable CSS to differentiate the synthesized events.

## Verification
*   **Visual Test:** Trigger swarm queries and verify the feed is concise, shows only high-level cognitive steps, and lacks system prompts or redundant technical status updates.
*   **Readability:** Confirm that a human can easily follow the narrative flow without technical distractions.
