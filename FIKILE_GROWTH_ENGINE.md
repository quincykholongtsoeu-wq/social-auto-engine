# FIKILE Growth Engine

## Mission
Turn Social Auto Engine into a performance-learning content system focused on original, high-quality social content rather than blind posting volume.

## Core loop
RESEARCH -> GENERATE -> SCORE -> HUMAN APPROVAL -> PUBLISH -> MEASURE -> LEARN -> EXPERIMENT

## V1 priorities
1. Facebook-first content workflow; Meta publishing can remain disconnected until developer verification is complete.
2. Preserve the existing approval queue. No autonomous direct writes by default.
3. Optimize for meaningful engagement signals, not spam volume.
4. Generate original content and avoid copied/low-value reposting.
5. Store each content experiment with hypothesis, hook, format, CTA, publish time, and performance outcome.
6. Use winning and losing outcomes to improve future content recommendations.
7. Keep AI providers optional; support free/local execution where possible.

## Growth intelligence modules

### Trend Scout
Collect candidate topics, audience questions, recurring pain points, and timely angles. Output ranked content opportunities with source notes.

### Hook Lab
Generate multiple original hooks for each opportunity. Each hook carries an explicit hypothesis about why the audience may stop, watch, read, comment, share, or click.

### Content Builder
Create platform-native drafts from approved opportunities and brand constraints. Never copy source text as finished content.

### Quality Gate
Score drafts for clarity, originality, relevance, brand fit, usefulness, CTA quality, and risk. Weak drafts are revised or rejected before approval.

### Experiment Manager
Treat every published item as an experiment. Track topic, hook, format, length, CTA, time slot, audience hypothesis, and variant.

### Performance Learner
Compare outcomes across experiments. Promote patterns supported by repeated evidence and downgrade weak patterns. Do not declare a strategy winner from one viral post.

### Strategy Brain
Produce the next content plan from accumulated evidence: what to repeat, what to stop, what to test next, and why.

## Guardrails
- Human approval remains ON for V1.
- SOCIALBLAST_ALLOW_DIRECT_WRITES stays false by default.
- Never commit platform tokens, API keys, passwords, or app secrets.
- Respect platform APIs, rate limits, permissions, and monetization/content policies.
- No fake engagement, engagement farms, mass-comment spam, impersonation, or deceptive interaction.
- Preserve upstream MIT attribution and project-origin notices.

## V1 success criteria
The engine can prepare a ranked Facebook content queue before Meta is connected; record hypotheses and variants; score drafts; preserve approval; and later ingest post-performance data once the Facebook adapter is connected.

## Build strategy
SEARCH -> AUDIT -> REUSE -> INTEGRATE -> TEST -> SHIP.

Do not rebuild capabilities already provided by strong compatible open-source components.