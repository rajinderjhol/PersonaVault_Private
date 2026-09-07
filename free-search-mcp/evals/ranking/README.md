# Ranking evaluation

A/B the result-merging algorithm against real engine output.

Ranking changes are easy to argue for and hard to be right about. This harness
exists so a change to `aggregator._merge` has to earn its place: capture what
the engines actually return, then replay those same results through candidate
configurations offline. Isolating the merge from the network is the point —
otherwise every comparison is contaminated by whichever engine happened to
answer that minute.

## Running it

```bash
# 1. Capture. Hits the network; takes a few minutes. Do this once.
SEARCH_MCP_FETCH_STRATEGY=http uv run python evals/ranking/capture.py

# 2. Replay. Offline, instant, repeatable.
uv run python evals/ranking/replay.py
```

`capture.py` writes `buckets.json` next to itself. It is gitignored: it is a
snapshot of a moving web, not a fixture, and a stale one would quietly make
every later measurement wrong.

## What it measures

Each case names a query, an optional `category`, and a substring identifying
the one result a knowledgeable person would call correct. From the merged list:

- **hit@1** / **hit@3** — was it first, or in the top three
- **MRR** — 1/rank of it, averaged over cases (0 when absent entirely)

A candidate has to improve the aggregate AND regress no individual query.
`replay.py --detail` prints the per-query before/after table that shows this.

## What this set has already settled

| change | verdict |
|---|---|
| Native-category weight 1.0 → 2.0 | **adopted.** hit@1 6→8, hit@3 9→13, MRR 0.605→0.747; 6 improved, 0 regressed |
| RRF damping constant `k`, 60 → 5…30 | **rejected.** MRR moves < 0.01 at any value; ranks are already correlated across engines |
| Lexical query/title overlap bonus | **rejected.** Worse at every weight tried (0.747 → 0.645) |
| Stripping tracking parameters before the RRF key | **rejected on this evidence.** 81 of 393 results carry one, but zero of them collided with a clean copy of the same URL, so no merge changes |

## Caveats worth keeping in mind

Fourteen queries is small. It is enough to catch a change that breaks something
obvious and to reject the two ideas above, and not enough to justify a constant
tuned to three decimal places — which is why `_NATIVE_CATEGORY_WEIGHT` is 2.0,
the value with a statable meaning ("one native hit ties two general engines
agreeing"), rather than the 2.25 that scored marginally higher here.

The expected-result substrings encode a judgement about what "correct" means.
Two of them were wrong on the first pass and were corrected once the output was
read: a `paper.biomed` case demanded Europe PMC when PubMed is equally right,
and it was measuring an engine outage rather than a ranking failure.
