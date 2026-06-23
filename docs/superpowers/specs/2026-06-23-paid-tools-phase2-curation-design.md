# Paid Tools — Phase 2: Curation — Design

**Date:** 2026-06-23
**Status:** Approved
**Parent spec:** `docs/superpowers/specs/2026-06-22-paid-tools-design.md`
**Phase 1 plan:** `docs/superpowers/plans/2026-06-22-paid-tools-phase1-billing.md` (DONE)

## Goal

Cut tools.pratyushsaxena.com from ~852 free, client-side utilities down to the 20
curated paid tools defined in `pro`'s catalog. Remove the other ~832 tools, 301-redirect
their URLs to the tools home so link equity is preserved and nothing 404s, and attach
`freeLimit` metadata to each surviving tool so Phase 3 can enforce the free-preview tier.

This phase is **curation + metadata only**. No auth, no checkout, no paywall enforcement —
those are Phase 3.

## Repo facts (carried from Phase 1)

- `pro/` and `tools/` are separate nested git repos, each with its own Vercel deploy. All
  Phase 2 work lands in the **`tools`** repo. Run git/npm inside `tools/`; stage with paths
  relative to that repo.
- The 20 curated slugs are the single source of truth in `pro/lib/catalog/paid-tools.ts`
  (`PAID_TOOLS`). All 20 are verified to exist in `tools/lib/tools.ts`.
- The `tools` app registers each tool in **three** places (per `tools/AGENTS.md`):
  1. `lib/tools.ts` — an entry in the `tools` array (metadata).
  2. `components/tools/<Name>.tsx` — the interactive component.
  3. `components/tools/index.ts` — an import + a `toolComponents` map entry keyed by slug.
  Everything else (route `app/[slug]/page.tsx`, `sitemap.ts`, OG images, FAQ JSON-LD,
  search index, category pages) derives from the `tools` array and updates automatically.
- The route uses `export const dynamicParams = false` and `generateStaticParams()` from the
  `tools` array, so once a slug leaves `tools.ts` it stops being generated and would 404
  without an explicit redirect.

## The 20 curated tools (by category)

- **PDF (8):** pdf-to-word, pdf-merger, pdf-splitter, images-to-pdf, pdf-watermark,
  pdf-extract-text, pdf-extract-images, pdf-page-numbers
- **Image (5):** image-compressor, image-converter, image-resizer, image-watermark,
  favicon-generator
- **Video (4):** video-compressor, video-trimmer, video-to-gif, video-audio-extractor
- **Audio (3):** audio-converter, audio-trimmer, audio-merger

## Pre-work: commit the in-flight security WIP

`tools/main` currently has uncommitted, unrelated security-hardening work. It is committed
**first**, as its own commit (authored in the owner's voice, no AI co-author trailer), so the
curation branch starts from a clean tree. The WIP covers:

- new `lib/rate-limit.ts` (best-effort in-memory limiter);
- rate limiting wired into `/api/pdf-to-word`, `/api/report-bug`, `/api/request-tool`;
- `/api/pdf-to-word` in-flight concurrency cap + max-pages bound;
- `/api/count` CORS scoped to the marketing origin (+ `Vary: Origin`);
- PII log redaction in `report-bug` / `request-tool` when `RESEND_API_KEY` is unset in prod;
- JSON-LD `<` escaping in `app/[slug]/page.tsx`;
- CSP header in `next.config.ts`;
- `sanitizeHtml` on the `EmailSignature` preview.

Then cut branch `paid-tools-curation` from the clean `tools/main`.

## Work items

### 1. Trim the catalog to 20 (the three registration points)

Drive removal from the canonical 20-slug list:

- `lib/tools.ts` — keep only the 20 matching entries in the `tools` array.
- `components/tools/index.ts` — keep only the 20 imports and the 20 `toolComponents` entries.
- `components/tools/*.tsx` — delete the ~832 orphaned component files; keep the 20 surviving
  components and the shared `components/ui/` primitives.

**Safety net:** `tsc --noEmit` + `next build` must both go green. The build fails loudly if
`index.ts` imports a deleted file, or if a surviving `tools.ts` entry has no component. A
small guard test asserts that the set of slugs in `tools.ts` exactly equals the 20 expected
slugs, so future drift from `pro`'s catalog is caught.

### 2. `freeLimit` metadata (add only; enforced in Phase 3)

Add a required field to the `Tool` type so `tsc` forces every surviving tool to define it:

```ts
export type FreeLimit = {
  maxFiles?: number;    // input file-count cap in the free tier
  maxPages?: number;    // PDF page cap
  maxBytes?: number;    // per-file size cap (images)
  maxSeconds?: number;  // media duration cap (video/audio)
  note: string;         // human-readable free-tier description for the paywall UI
};

// on Tool:
freeLimit: FreeLimit;
```

Per-category defaults (tunable per tool):

- **PDF:** `{ maxFiles: 1, maxPages: 5 }`. Exceptions where one file is meaningless:
  `pdf-merger` and `images-to-pdf` use `{ maxFiles: 2 }`.
- **Image:** `{ maxFiles: 1, maxBytes: 2097152 }` (2 MB).
- **Video / Audio:** `{ maxFiles: 1, maxSeconds: 30 }`.

Each `note` states the free tier in plain English (e.g. "Free: 1 PDF up to 5 pages.").

No enforcement logic this phase — only well-typed data the Phase 3 gating UI will read.

### 3. Redirects — middleware catch-all

Add `tools/middleware.ts`. Any request for `/<slug>` whose slug is **not** in the curated
set 301-redirects to `/`. The curated set is imported from `lib/tools.ts` (single source,
can't drift). The matcher + an in-handler guard exclude system paths so they pass through
untouched: `/api/*`, `/report`, `/request`, `/_next/*`, static assets (`robots.txt`,
`sitemap.xml`, favicon/icon/OG image routes), and `/` itself.

Chosen over an enumerated ~832-entry `next.config.ts` redirect list because it is
self-maintaining: changing the catalog needs no regenerated redirect table.

### 4. Minimal homepage fix

`app/page.tsx` hardcodes a featured-tools list (most of which are removed) and renders
`tools.length`. Phase 2 repoints the featured list to curated slugs only and removes dead
links; the count stays accurate (now 20). **Full pricing/paywall messaging is Phase 3** —
this fix only stops the homepage from linking to removed tools.

## Verification

- `npx tsc --noEmit` clean.
- `npx next build` green: exactly the 20 static tool pages generate; no broken `index.ts`
  references; sitemap/search reflect 20 tools.
- Guard test passes (curated set === expected 20 slugs).
- Manual spot-check in `npm run dev`: 3 removed slugs 301 to `/`; 3 curated tools still
  render and run their free path; `/report` and `/request` still load; `/api/count` still
  responds.
- Merge `paid-tools-curation` → `tools/main`.

## Out of scope / follow-up flags

- **Marketing site count.** `/api/count` feeds pratyushsaxena.com a tool count that drops
  from ~852 to 20, and that site's "800+ free tools" copy lives in the outer Flask repo.
  Flag for a follow-up; not part of Phase 2.
- **Paywall enforcement, Clerk, checkout/portal, pricing UI** — all Phase 3.

## Phase boundary

Phase 2 ships a curated, still-free-to-use 20-tool site with `freeLimit` metadata in place
and all removed URLs redirecting. Phase 3 then adds Clerk, entitlement reads, the gating UI,
and free-preview enforcement on top of this metadata.
