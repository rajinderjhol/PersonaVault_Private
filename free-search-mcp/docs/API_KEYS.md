# API Keys

API keys are **optional**. search-mcp ships with a set of keyless engines that
work out of the box with no signup, no key, and no configuration:
`duckduckgo`, `mojeek`, `googlenews`, `google`, `bilibili`, `searx`,
`startpage`, `bing`, `baidu`, `serpsearch`, `zhihu`, `sogou`, `so360`,
`wikipedia`, `openlibrary`, the vertical sources (`arxiv`, `openalex`,
`crossref`, `pubmed`, `github`, `stackexchange`, `hackernews`, `gdelt`,
`openverse`, `zenodo`), and the keyless tier of `anysearch`.

Two of these accept an **optional** key that only raises limits: `github`
(a token also unlocks the separate `github_code` engine, since GitHub rejects
anonymous code search) and `stackexchange`.

Adding a key simply **unlocks the corresponding keyed engine** — for example,
setting your Brave key enables the `brave_api` engine. You only need a key for
the specific keyed engine(s) you want to use.

---

## Two ways to set a key

### (a) Admin UI — recommended, simplest

```
uv run search-mcp-admin
```

Then open **http://127.0.0.1:8765** in your browser, paste your key(s) into the
relevant provider fields, and click **Save**. Changes take effect **live, with
no restart** — a running server picks up the new key on its next request.

The Admin UI is **中英双语**: labels, badges, buttons, free-tier notes, and
"How to get a key / 如何获取密钥" steps are shown in English and Chinese. It
also includes the **Network / Proxy / 网络 / 代理** card for proxy settings.

### (b) Environment variables / `.env`

Set the `SEARCH_MCP_<FIELD>` environment variable for each field you want to
configure. The full list of variable names:

| Provider | Environment variable(s) |
| --- | --- |
| Brave Search API | `SEARCH_MCP_BRAVE_API_KEY` |
| Serper (Google) | `SEARCH_MCP_SERPER_API_KEY` |
| Tavily (AI search) | `SEARCH_MCP_TAVILY_API_KEY` |
| Google Custom Search | `SEARCH_MCP_GOOGLE_CSE_API_KEY` and `SEARCH_MCP_GOOGLE_CSE_CX` |
| AnySearch (optional key) | `SEARCH_MCP_ANYSEARCH_API_KEY` |
| Semantic Scholar (optional key) | `SEARCH_MCP_SEMANTICSCHOLAR_API_KEY` |
| GitHub (optional token) | `SEARCH_MCP_GITHUB_TOKEN` |
| Stack Exchange (optional key) | `SEARCH_MCP_STACKEXCHANGE_KEY` |

Environment variables always **win over** values saved in the file, so existing
12-factor / container deployments keep working unchanged.

### Where keys are stored

Keys saved via the Admin UI are written to:

```
~/.config/search-mcp/config.json
```

The file is written atomically with `0600` (owner read/write only) permissions,
and the admin UI binds to localhost only.

---

## Brave Search API

A search API from Brave. **Free tier: 2,000 queries/month free.**

How to get a key:

1. Open https://brave.com/search/api/ and click 'Get started'.
2. Sign up / log in and verify your email.
3. Subscribe to the free 'Data for Search' plan (a card may be required, but the free tier isn't charged).
4. Open the dashboard → API Keys → copy your subscription token.

- Sign up: https://brave.com/search/api/
- Docs: https://api-dashboard.search.brave.com/app/documentation
- Environment variable: `SEARCH_MCP_BRAVE_API_KEY`

Use it:

```python
search("...", engines=["brave_api"])
```

---

## Serper (Google)

Google search results via the Serper API. **Free tier: 2,500 free queries
(one-time).**

How to get a key:

1. Open https://serper.dev and sign up (Google login works).
2. You land on the dashboard with 2,500 free credits.
3. Copy the API key shown under 'API Key'.

- Sign up: https://serper.dev
- Docs: https://serper.dev/playground
- Environment variable: `SEARCH_MCP_SERPER_API_KEY`

Use it:

```python
search("...", engines=["serper"])
```

---

## Tavily (AI search)

An AI-oriented search API. **Free tier: 1,000 credits/month free.**

How to get a key:

1. Open https://app.tavily.com and sign up.
2. On the dashboard, find the 'API Keys' section.
3. Copy your key (it starts with 'tvly-').

- Sign up: https://app.tavily.com
- Docs: https://docs.tavily.com
- Environment variable: `SEARCH_MCP_TAVILY_API_KEY`

Use it:

```python
search("...", engines=["tavily"])
```

---

## Google Custom Search

Google's Programmable Search Engine (Custom Search JSON API). **Free tier: 100
queries/day free.**

This provider needs **two** values: the **API key** *and* the **Search engine
ID (cx)**. Set both before using the engine.

How to get a key:

1. Create an API key: https://console.cloud.google.com/apis/credentials → 'Create credentials' → 'API key'.
2. Enable the 'Custom Search API' for that project: https://console.cloud.google.com/apis/library/customsearch.googleapis.com.
3. Create a search engine at https://programmablesearchengine.google.com/ → set it to 'Search the entire web'.
4. Copy the 'Search engine ID' (cx) from its control panel. Paste both the API key and the cx here.

- Sign up: https://programmablesearchengine.google.com/
- Docs: https://developers.google.com/custom-search/v1/overview
- Environment variables: `SEARCH_MCP_GOOGLE_CSE_API_KEY` **and** `SEARCH_MCP_GOOGLE_CSE_CX`

Use it:

```python
search("...", engines=["google_cse"])
```

---

## AnySearch (optional key)

A JSON REST search aggregator. The engine **works keyless** — a key is optional.
**Free tier: works keyless; a key raises the rate limit/quota.**

How to get a key:

1. AnySearch works anonymously with no key (lower limits).
2. For higher limits, sign up at https://anysearch.com and open Console → API Keys.
3. Create a key and paste it here.

- Sign up: https://anysearch.com/console/api-keys
- Docs: https://www.anysearch.com/docs
- Environment variable: `SEARCH_MCP_ANYSEARCH_API_KEY`

Use it (no key required):

```python
search("...", engines=["anysearch"])
```

---

## Semantic Scholar (optional key)

Scholarly search with the richest metadata of the keyless literature sources:
abstracts, citation counts, influential-citation counts and direct open-access
PDF links.

**Free tier: anonymous requests share one saturated pool and are answered with
HTTP 429 in practice; a free key gives 1 request/second.**

That is not a caution — every unauthenticated request made while building this
engine came back 429. So without a key the engine stays out of automatic
`category="paper"` routing (it would spend a slot on a guaranteed empty);
naming it in `engines=["semanticscholar"]` still runs it.

How to get a key:

1. Request one at https://www.semanticscholar.org/product/api#api-key-form
2. Approval is by email and takes a few days.
3. Paste the key here; `category="paper"` will then include it.

- Sign up: https://www.semanticscholar.org/product/api#api-key-form
- Docs: https://api.semanticscholar.org/api-docs/graph
- Environment variable: `SEARCH_MCP_SEMANTICSCHOLAR_API_KEY`

---

## GitHub (optional token)

**Free tier: repo/issue search works keyless (10 req/min); a token raises it to
30 req/min and unlocks the `github_code` engine.**

The `github` engine searches repositories and issues with no token. A token
raises the rate limit and enables `github_code`, because GitHub's code-search
API rejects anonymous requests outright.

How to get a token:

1. Create one at https://github.com/settings/tokens
2. **No scopes are needed** for searching public repositories.
3. Paste it here.

- Sign up: https://github.com/settings/tokens
- Docs: https://docs.github.com/rest/search
- Environment variable: `SEARCH_MCP_GITHUB_TOKEN`

---

## Stack Exchange (optional key)

**Free tier: 300 requests/day per IP keyless; an app key raises the quota.**

How to get a key:

1. Register an app at https://stackapps.com/apps/oauth/register
2. Only the **key** value is needed — not the client secret.
3. Paste it here.

- Sign up: https://stackapps.com/apps/oauth/register
- Docs: https://api.stackexchange.com/docs
- Environment variable: `SEARCH_MCP_STACKEXCHANGE_KEY`

---

## Which should I pick?

| Provider | Free tier | Best for |
| --- | --- | --- |
| Brave Search API | 2,000 queries/month | Independent web index, steady monthly free allowance |
| Serper (Google) | 2,500 queries (one-time) | Google-quality results for a quick trial |
| Tavily (AI search) | 1,000 credits/month | AI / LLM-oriented search workflows |
| Google Custom Search | 100 queries/day | Official Google results; low daily volume (needs API key + cx) |
| AnySearch | Keyless; key raises limits | Zero-setup use; add a key only to lift rate limits |
| Semantic Scholar | Anonymous pool is 429 in practice | Literature search with citation counts and OA PDFs |
| GitHub | Keyless 10/min; token 30/min | Repo and issue search; a token also unlocks code search |
| Stack Exchange | 300/day keyless | Q&A with accepted-answer and score signals |
