# Paid Tools — Phase 2: Curation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut the `tools` app from ~852 free tools to the 20 curated paid tools, 301-redirect every removed URL to the home page, and attach `freeLimit` metadata to each surviving tool (data only; Phase 3 enforces it).

**Architecture:** All work lands in the **`tools`** repo (separate nested git repo with its own Vercel deploy). Tools register in three places — `lib/tools.ts` (data array), `components/tools/<Name>.tsx` (component), `components/tools/index.ts` (slug→component map). Everything else (route, sitemap, OG images, search, categories) derives from the `tools` array. Removal is driven by deterministic Node scripts (no hand-editing the 19,150-line `tools.ts`), guarded by a drift-check script and verified by `tsc --noEmit` + `next build` going green. Redirects use a single edge `middleware.ts` that 301s any non-curated slug to `/`.

**Tech Stack:** Next.js 16.2.6, React 19, TypeScript (strict). No test runner in this repo (and `AGENTS.md` favors minimal deps), so verification is: zero-dependency Node check scripts + `npx tsc --noEmit` + `npx next build` + a manual dev spot-check.

## Global Constraints

- All commands run from the `tools/` directory. Stage paths relative to that repo (no `tools/` prefix).
- The 20 curated slugs are the single source of truth in `pro/lib/catalog/paid-tools.ts` (`PAID_TOOLS`). The canonical list, verbatim:
  `pdf-to-word, pdf-merger, pdf-splitter, images-to-pdf, pdf-watermark, pdf-extract-text, pdf-extract-images, pdf-page-numbers, image-compressor, image-converter, image-resizer, image-watermark, favicon-generator, video-compressor, video-trimmer, video-to-gif, video-audio-extractor, audio-converter, audio-trimmer, audio-merger`.
- The route `app/[slug]/page.tsx` uses `export const dynamicParams = false`; once a slug leaves `tools.ts` it 404s unless redirected.
- **Commit style for the `tools` repo (from `tools/AGENTS.md`):** commit messages read as the owner wrote them. **No `Co-Authored-By: Claude` trailer, no "Generated with Claude Code" footer.** (This differs from the outer repo. The outer-repo design/plan docs keep their normal trailers; `tools`-repo commits do not.)
- **Copy voice (from `tools/AGENTS.md`):** no em dashes, no marketing-speak ("seamless", "unlock", "robust", etc.), plain spoken English. Applies to any on-screen copy this plan adds (homepage `why` lines, `freeLimit.note`).
- This phase adds `freeLimit` **data only**. No enforcement, no auth, no checkout — those are Phase 3.

## File Structure

- `scripts/check-curated.mjs` — **new.** Standing drift guard: asserts `lib/tools.ts` contains exactly the 20 expected slugs. Zero deps.
- `scripts/curate.mjs` — **new.** One-shot transformer: trims the `tools` array in `lib/tools.ts` to the 20, trims `components/tools/index.ts` to the 20 imports + map entries, and deletes the ~832 orphaned `components/tools/*.tsx` files.
- `scripts/add-freelimits.mjs` — **new.** One-shot: injects a `freeLimit` object into each of the 20 surviving `tools.ts` entries.
- `lib/tools.ts` — **modify.** Trimmed to 20 entries (by `curate.mjs`); `Tool` type gains a required `freeLimit` field + a `FreeLimit` type; each entry gets a `freeLimit` (by `add-freelimits.mjs`).
- `components/tools/index.ts` — **modify.** Trimmed to 20 imports + 20 map entries (by `curate.mjs`).
- `components/tools/*.tsx` — **delete** ~832 orphaned files (by `curate.mjs`); keep the 20 surviving components and the shared `components/ui/`.
- `middleware.ts` — **new.** 301-redirects any non-curated, non-system path to `/`.
- `app/page.tsx` — **modify.** Repoint the "A few to try first" featured list to curated slugs.

---

### Task 0: Commit in-flight security WIP, then branch

**Files:** none created; commits existing working-tree changes on `tools/main`.

The `tools` working tree has an unrelated, self-contained security-hardening pass (new `lib/rate-limit.ts`; rate limiting on the API routes; pdf-to-word in-flight/page caps; `/api/count` CORS scoping; PII log redaction; JSON-LD escaping; CSP header; sanitized EmailSignature preview). Commit it first so curation starts from a clean tree.

- [ ] **Step 1: Confirm the working tree matches expectations**

Run: `cd tools && git status --short`
Expected: modified `app/[slug]/page.tsx`, `app/api/count/route.ts`, `app/api/pdf-to-word/route.ts`, `app/api/report-bug/route.ts`, `app/api/request-tool/route.ts`, `components/tools/EmailSignature.tsx`, `next.config.ts`; untracked `lib/rate-limit.ts`. Nothing else.

- [ ] **Step 2: Stage exactly those paths and commit (owner voice, no AI trailer)**

```bash
cd tools
git add app/[slug]/page.tsx app/api/count/route.ts app/api/pdf-to-word/route.ts \
        app/api/report-bug/route.ts app/api/request-tool/route.ts \
        components/tools/EmailSignature.tsx next.config.ts lib/rate-limit.ts
git commit -m "Harden public endpoints: rate limiting, CSP, CORS scoping, PII redaction"
```

- [ ] **Step 3: Verify the tree is clean, then branch**

```bash
cd tools
git status --short        # expect: empty
git checkout -b paid-tools-curation
```
Expected: on a clean branch `paid-tools-curation` off `main`.

---

### Task 1: Drift-guard check script (red first)

**Files:**
- Create: `scripts/check-curated.mjs`

**Interfaces:**
- Produces: a runnable guard `node scripts/check-curated.mjs` that exits `0` iff `lib/tools.ts` defines exactly the 20 expected slugs, else prints the diff and exits `1`.

- [ ] **Step 1: Write the check script**

```js
// scripts/check-curated.mjs
// Drift guard: lib/tools.ts must define exactly the 20 curated slugs that
// pro/lib/catalog/paid-tools.ts (PAID_TOOLS) sells. Run after any catalog edit.
//   node scripts/check-curated.mjs
import { readFile } from "node:fs/promises";

const EXPECTED = [
  "pdf-to-word", "pdf-merger", "pdf-splitter", "images-to-pdf", "pdf-watermark",
  "pdf-extract-text", "pdf-extract-images", "pdf-page-numbers",
  "image-compressor", "image-converter", "image-resizer", "image-watermark",
  "favicon-generator",
  "video-compressor", "video-trimmer", "video-to-gif", "video-audio-extractor",
  "audio-converter", "audio-trimmer", "audio-merger",
].sort();

const src = await readFile(new URL("../lib/tools.ts", import.meta.url), "utf8");
const slugs = [...src.matchAll(/slug:\s*["'`]([^"'`]+)["'`]/g)]
  .map((m) => m[1])
  .sort();

const expectedSet = new Set(EXPECTED);
const actualSet = new Set(slugs);
const missing = EXPECTED.filter((s) => !actualSet.has(s));
const extra = slugs.filter((s) => !expectedSet.has(s));

if (slugs.length !== EXPECTED.length || missing.length || extra.length) {
  console.error(
    `Curated set mismatch.\n  count: ${slugs.length} (expected ${EXPECTED.length})\n` +
      `  missing: ${missing.join(", ") || "(none)"}\n` +
      `  extra (${extra.length}): ${extra.slice(0, 10).join(", ")}${extra.length > 10 ? " ..." : ""}`
  );
  process.exit(1);
}
console.log(`Curated set OK: ${slugs.length} tools match the pro catalog.`);
```

- [ ] **Step 2: Run it against the un-trimmed catalog to confirm it fails**

Run: `cd tools && node scripts/check-curated.mjs`
Expected: FAIL (exit 1) — `count: 852 (expected 20)` and a long `extra` list. This is the intended red state before curation.

- [ ] **Step 3: Commit**

```bash
cd tools
git add scripts/check-curated.mjs
git commit -m "Add curated-catalog drift guard script"
```

---

### Task 2: Curate — trim to 20 and delete orphaned components

**Files:**
- Create: `scripts/curate.mjs`
- Modify (by running the script): `lib/tools.ts`, `components/tools/index.ts`
- Delete (by running the script): ~832 `components/tools/*.tsx`

**Interfaces:**
- Consumes: the same 20-slug list as Task 1.
- Produces: a `tools` array of exactly 20 entries; an `index.ts` with exactly 20 imports + 20 map entries; only the 20 surviving component files remain in `components/tools/` (plus `index.ts`).

- [ ] **Step 1: Write the curation script**

```js
// scripts/curate.mjs
// One-shot curation. Trims lib/tools.ts to the 20 curated entries, trims
// components/tools/index.ts to the matching imports + map entries, and deletes
// every orphaned components/tools/*.tsx. Deterministic and idempotent (a second
// run is a no-op). Verify afterward with: node scripts/check-curated.mjs,
// npx tsc --noEmit, npx next build.
import { readFile, writeFile, readdir, unlink } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const KEEP = new Set([
  "pdf-to-word", "pdf-merger", "pdf-splitter", "images-to-pdf", "pdf-watermark",
  "pdf-extract-text", "pdf-extract-images", "pdf-page-numbers",
  "image-compressor", "image-converter", "image-resizer", "image-watermark",
  "favicon-generator",
  "video-compressor", "video-trimmer", "video-to-gif", "video-audio-extractor",
  "audio-converter", "audio-trimmer", "audio-merger",
]);

// --- String/comment-aware splitter for the top-level `tools` array entries. ---
function splitToolsArray(src) {
  const marker = "export const tools: Tool[] = [";
  const start = src.indexOf(marker);
  if (start < 0) throw new Error("tools array marker not found");
  const open = start + marker.length - 1; // index of '['
  let i = open + 1;
  let depth = 1;
  let str = null, esc = false, line = false, block = false;
  const entries = [];
  let cur = "";
  while (i < src.length) {
    const c = src[i];
    const n = src[i + 1];
    if (line) { cur += c; if (c === "\n") line = false; i++; continue; }
    if (block) { cur += c; if (c === "*" && n === "/") { cur += n; i += 2; block = false; continue; } i++; continue; }
    if (str) {
      cur += c;
      if (esc) { esc = false; i++; continue; }
      if (c === "\\") { esc = true; i++; continue; }
      if (c === str) str = null;
      i++; continue;
    }
    if (c === "/" && n === "/") { line = true; cur += c; i++; continue; }
    if (c === "/" && n === "*") { block = true; cur += c; i++; continue; }
    if (c === '"' || c === "'" || c === "`") { str = c; cur += c; i++; continue; }
    if (c === "{" || c === "[" || c === "(") { depth++; cur += c; i++; continue; }
    if (c === "}" || c === ")") { depth--; cur += c; i++; continue; }
    if (c === "]") {
      if (depth === 1) { if (cur.trim()) entries.push(cur); return { open, close: i, entries }; }
      depth--; cur += c; i++; continue;
    }
    if (c === "," && depth === 1) { entries.push(cur); cur = ""; i++; continue; }
    cur += c; i++;
  }
  throw new Error("tools array not closed");
}

const slugOf = (entry) => {
  const m = entry.match(/slug:\s*["'`]([^"'`]+)["'`]/);
  return m ? m[1] : null;
};

async function curateToolsTs() {
  const file = path.join(ROOT, "lib/tools.ts");
  const src = await readFile(file, "utf8");
  const { open, close, entries } = splitToolsArray(src);
  const kept = entries.filter((e) => KEEP.has(slugOf(e)));
  const keptSlugs = new Set(kept.map(slugOf));
  for (const s of KEEP) if (!keptSlugs.has(s)) throw new Error(`missing curated slug in tools.ts: ${s}`);
  if (kept.length !== KEEP.size) throw new Error(`expected ${KEEP.size} kept, got ${kept.length}`);
  const head = src.slice(0, open + 1); // through '['
  const tail = src.slice(close); // from ']' onward (toolsBySlug, getTool, ...)
  const body = "\n  " + kept.map((e) => e.trim()).join(",\n  ") + ",\n";
  await writeFile(file, head + body + tail);
  console.log(`tools.ts: kept ${kept.length} entries (removed ${entries.length - kept.length}).`);
}

async function curateIndexTs() {
  const file = path.join(ROOT, "components/tools/index.ts");
  const lines = (await readFile(file, "utf8")).split("\n");
  // slug -> component, from map lines like:  "slug": Component,
  const slugComp = {};
  for (const l of lines) {
    const m = l.match(/^\s*"([^"]+)":\s*([A-Za-z0-9_]+),?\s*$/);
    if (m) slugComp[m[1]] = m[2];
  }
  const keepComp = new Set(
    Object.entries(slugComp).filter(([s]) => KEEP.has(s)).map(([, c]) => c)
  );
  const out = [];
  for (const l of lines) {
    const imp = l.match(/^import\s*\{\s*([A-Za-z0-9_]+)\s*\}\s*from\s*"\.\/[^"]+";\s*$/);
    if (imp) { if (keepComp.has(imp[1])) out.push(l); continue; }
    const mp = l.match(/^\s*"([^"]+)":\s*[A-Za-z0-9_]+,?\s*$/);
    if (mp) { if (KEEP.has(mp[1])) out.push(l); continue; }
    out.push(l);
  }
  await writeFile(file, out.join("\n"));
  console.log(`index.ts: kept ${keepComp.size} component imports + map entries.`);
  return keepComp;
}

async function deleteOrphans(file) {
  // Determine kept files from the (already trimmed) index.ts import paths.
  const src = await readFile(path.join(ROOT, "components/tools/index.ts"), "utf8");
  const keepFiles = new Set(
    [...src.matchAll(/from\s*"\.\/([^"]+)";/g)].map((m) => `${m[1]}.tsx`)
  );
  const dir = path.join(ROOT, "components/tools");
  const all = await readdir(dir);
  let removed = 0;
  for (const f of all) {
    if (!f.endsWith(".tsx")) continue; // never touches index.ts
    if (keepFiles.has(f)) continue;
    await unlink(path.join(dir, f));
    removed++;
  }
  console.log(`components/tools: kept ${keepFiles.size} files, deleted ${removed}.`);
}

await curateToolsTs();
await curateIndexTs();
await deleteOrphans();
console.log("Curation complete.");
```

- [ ] **Step 2: Run the curation script**

Run: `cd tools && node scripts/curate.mjs`
Expected: logs `tools.ts: kept 20 entries (removed 832).`, `index.ts: kept 20 component imports + map entries.`, `components/tools: kept 20 files, deleted 832.`, `Curation complete.` (No throw.)

- [ ] **Step 3: Run the drift guard — now green**

Run: `cd tools && node scripts/check-curated.mjs`
Expected: PASS — `Curated set OK: 20 tools match the pro catalog.`

- [ ] **Step 4: Type-check**

Run: `cd tools && npx tsc --noEmit`
Expected: no errors. (Catches any kept component that imported a now-deleted sibling, or any `index.ts` reference to a deleted file.)

- [ ] **Step 5: Build**

Run: `cd tools && npx next build`
Expected: build succeeds; the static export generates exactly 20 `/[slug]` pages plus the home/report/request pages. No "module not found" for `components/tools/*`.

- [ ] **Step 6: Commit**

```bash
cd tools
git add -A
git commit -m "Curate to the 20 paid tools; remove the rest"
```
(`git add -A` stages the 832 deletions, the trimmed `tools.ts`/`index.ts`, and `scripts/curate.mjs`.)

---

### Task 3: Add `freeLimit` metadata to the 20 tools

**Files:**
- Modify: `lib/tools.ts` (add `FreeLimit` type + required field on `Tool`)
- Create: `scripts/add-freelimits.mjs`

**Interfaces:**
- Produces: `export type FreeLimit` and a required `freeLimit: FreeLimit` on `Tool`; every one of the 20 entries carries a `freeLimit`.

- [ ] **Step 1: Add the `FreeLimit` type and the required field**

In `lib/tools.ts`, immediately before `export type Tool = {` (currently line ~19), insert:

```ts
export type FreeLimit = {
  maxFiles?: number; // input file-count cap in the free tier
  maxPages?: number; // PDF page cap
  maxBytes?: number; // per-file size cap (images)
  maxSeconds?: number; // media duration cap (video/audio)
  note: string; // plain-English free-tier line for the Phase 3 paywall UI
};
```

Then inside `export type Tool = { ... }`, add this line after `howTo: string[];`:

```ts
  freeLimit: FreeLimit;
```

- [ ] **Step 2: Confirm tsc now fails (field required, values missing)**

Run: `cd tools && npx tsc --noEmit`
Expected: FAIL — 20 errors, one per tool entry, "Property 'freeLimit' is missing". This confirms the field is required and every entry must define it.

- [ ] **Step 3: Write the injector script**

```js
// scripts/add-freelimits.mjs
// One-shot: inserts a `freeLimit` object into each of the 20 curated tools.ts
// entries, right after that entry's `slug:` line. Run once (a second run would
// duplicate the key and break tsc). Verify with: npx tsc --noEmit.
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const FL = {
  // PDF: 1 file, <=5 pages. Merger/images-to-pdf need >1 file to be useful.
  "pdf-to-word": { maxFiles: 1, maxPages: 5, note: "Free: 1 PDF up to 5 pages." },
  "pdf-merger": { maxFiles: 2, note: "Free: merge up to 2 PDFs." },
  "pdf-splitter": { maxFiles: 1, maxPages: 5, note: "Free: split a PDF up to 5 pages." },
  "images-to-pdf": { maxFiles: 2, note: "Free: up to 2 images." },
  "pdf-watermark": { maxFiles: 1, maxPages: 5, note: "Free: 1 PDF up to 5 pages." },
  "pdf-extract-text": { maxFiles: 1, maxPages: 5, note: "Free: 1 PDF up to 5 pages." },
  "pdf-extract-images": { maxFiles: 1, maxPages: 5, note: "Free: 1 PDF up to 5 pages." },
  "pdf-page-numbers": { maxFiles: 1, maxPages: 5, note: "Free: 1 PDF up to 5 pages." },
  // Image: 1 file, <=2 MB (2 * 1024 * 1024).
  "image-compressor": { maxFiles: 1, maxBytes: 2097152, note: "Free: 1 image up to 2 MB." },
  "image-converter": { maxFiles: 1, maxBytes: 2097152, note: "Free: 1 image up to 2 MB." },
  "image-resizer": { maxFiles: 1, maxBytes: 2097152, note: "Free: 1 image up to 2 MB." },
  "image-watermark": { maxFiles: 1, maxBytes: 2097152, note: "Free: 1 image up to 2 MB." },
  "favicon-generator": { maxFiles: 1, maxBytes: 2097152, note: "Free: 1 image up to 2 MB." },
  // Video/Audio: 1 file, <=30 s.
  "video-compressor": { maxFiles: 1, maxSeconds: 30, note: "Free: clips up to 30 seconds." },
  "video-trimmer": { maxFiles: 1, maxSeconds: 30, note: "Free: clips up to 30 seconds." },
  "video-to-gif": { maxFiles: 1, maxSeconds: 30, note: "Free: clips up to 30 seconds." },
  "video-audio-extractor": { maxFiles: 1, maxSeconds: 30, note: "Free: clips up to 30 seconds." },
  "audio-converter": { maxFiles: 1, maxSeconds: 30, note: "Free: clips up to 30 seconds." },
  "audio-trimmer": { maxFiles: 1, maxSeconds: 30, note: "Free: clips up to 30 seconds." },
  "audio-merger": { maxFiles: 2, maxSeconds: 30, note: "Free: up to 2 clips, 30 seconds each." },
};

const file = path.join(ROOT, "lib/tools.ts");
let src = await readFile(file, "utf8");
if (/freeLimit:/.test(src)) throw new Error("freeLimit already present; refusing to double-insert");

for (const [slug, fl] of Object.entries(FL)) {
  const re = new RegExp(`(\\n(\\s*)slug:\\s*"${slug}",\\n)`);
  const m = src.match(re);
  if (!m) throw new Error(`slug line not found: ${slug}`);
  const indent = m[2];
  const inject = `${indent}freeLimit: ${JSON.stringify(fl)},\n`;
  src = src.replace(re, `$1${inject}`);
}
await writeFile(file, src);
console.log(`Injected freeLimit into ${Object.keys(FL).length} tools.`);
```

- [ ] **Step 4: Run the injector**

Run: `cd tools && node scripts/add-freelimits.mjs`
Expected: `Injected freeLimit into 20 tools.`

- [ ] **Step 5: Type-check — now green**

Run: `cd tools && npx tsc --noEmit`
Expected: no errors (all 20 entries now have `freeLimit`).

- [ ] **Step 6: Commit**

```bash
cd tools
git add lib/tools.ts scripts/add-freelimits.mjs
git commit -m "Add free-tier limits to each paid tool"
```

---

### Task 4: Redirect removed URLs (edge middleware)

**Files:**
- Create: `middleware.ts`

**Interfaces:**
- Consumes: `toolsBySlug` from `@/lib/tools` (pure data; safe in the edge runtime).
- Produces: a 301 redirect to `/` for any single-segment path whose slug is not curated; system paths and curated tools pass through.

- [ ] **Step 1: Write the middleware**

```ts
// middleware.ts
// Removed-tool URLs 301-redirect to home so old links keep their value instead
// of 404ing. Any /<slug> that is not one of the curated tools redirects to "/".
// The matcher excludes API, Next internals, the report/request pages, and any
// path with a file extension, so only top-level page slugs reach this code.
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { toolsBySlug } from "@/lib/tools";

export function middleware(req: NextRequest) {
  const slug = req.nextUrl.pathname.slice(1); // drop leading "/"
  if (slug && !Object.prototype.hasOwnProperty.call(toolsBySlug, slug)) {
    const url = req.nextUrl.clone();
    url.pathname = "/";
    url.search = "";
    return NextResponse.redirect(url, 301);
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!api|_next|report|request|favicon.ico|icon.svg|robots.txt|sitemap.xml|opengraph-image|.*\\.).*)",
  ],
};
```

- [ ] **Step 2: Type-check + build**

Run: `cd tools && npx tsc --noEmit && npx next build`
Expected: both succeed; build output lists `middleware` (ƒ Middleware).

- [ ] **Step 3: Manually verify redirect + pass-through in dev**

Run in one terminal: `cd tools && npm run dev`
Then in another:
```bash
# Removed tool -> 301 to home:
curl -sI http://localhost:3000/tip-percentage | grep -iE "HTTP/|location"
# Curated tool -> 200 (no redirect):
curl -sI http://localhost:3000/pdf-merger | grep -iE "HTTP/|location"
# System pages still load:
curl -sI http://localhost:3000/request | grep -iE "HTTP/"
curl -sI http://localhost:3000/api/count | grep -iE "HTTP/"
```
Expected: `tip-percentage` → `308`/`301` with `location: http://localhost:3000/` (Next dev may report 307/308 for redirects; production honors the 301 we set — confirm `location` points to `/`); `pdf-merger` → `200`; `/request` → `200`; `/api/count` → `200`. Stop the dev server when done.

- [ ] **Step 4: Commit**

```bash
cd tools
git add middleware.ts
git commit -m "Redirect removed tool URLs to home"
```

---

### Task 5: Fix the homepage featured list

**Files:**
- Modify: `app/page.tsx` (the "A few to try first" list, currently lines ~112-147)

**Interfaces:**
- Produces: a featured list referencing only curated slugs (no dead links).

- [ ] **Step 1: Replace the featured array**

In `app/page.tsx`, replace the array literal passed to `.map` in the "A few to try first" section (the seven `{ slug, name, why }` objects) with these six curated entries:

```tsx
            {[
              {
                slug: "image-compressor",
                name: "Image compressor",
                why: "for forms that cap uploads at 2 MB",
              },
              {
                slug: "pdf-to-word",
                name: "PDF to Word",
                why: "for editing a document you were only sent as a PDF",
              },
              {
                slug: "pdf-merger",
                name: "PDF merger",
                why: "for combining a few PDFs into one before you send it",
              },
              {
                slug: "video-compressor",
                name: "Video compressor",
                why: "for getting a clip under an upload limit",
              },
              {
                slug: "image-converter",
                name: "Image converter",
                why: "for turning a HEIC photo into a JPG that opens anywhere",
              },
              {
                slug: "favicon-generator",
                name: "Favicon generator",
                why: "for making the little browser-tab icon for a site",
              },
            ].map((t) => (
```

(Leave the surrounding `<ul>`/`<li>`/`<Link>` markup unchanged.)

- [ ] **Step 2: Type-check + build**

Run: `cd tools && npx tsc --noEmit && npx next build`
Expected: both succeed.

- [ ] **Step 3: Manually confirm the featured links resolve**

Run: `cd tools && npm run dev`, open `http://localhost:3000/`, click each of the six links.
Expected: each opens its curated tool page (200, no redirect to home). Stop the dev server.

- [ ] **Step 4: Commit**

```bash
cd tools
git add app/page.tsx
git commit -m "Point homepage picks at the curated tools"
```

---

### Task 6: Final verification and merge

**Files:** none (verification + merge only).

- [ ] **Step 1: Full clean verification**

Run:
```bash
cd tools
node scripts/check-curated.mjs   # Curated set OK: 20 tools ...
npx tsc --noEmit                 # no errors
npx next build                   # 20 tool pages, middleware present
```
Expected: all three pass.

- [ ] **Step 2: Manual acceptance matrix (dev)**

Run `cd tools && npm run dev`, then confirm:
- 3 removed slugs (`tip-percentage`, `json-formatter`, `sleep-calculator`) each redirect to `/`.
- 3 curated tools across categories (`pdf-merger`, `video-to-gif`, `audio-converter`) load and run their free path on a small input.
- `/report` and `/request` load; `/api/count` returns `{ "count": 20 }`.
- The homepage featured links all resolve.

Stop the dev server when done.

- [ ] **Step 3: Merge to `main`**

```bash
cd tools
git checkout main
git merge --no-ff paid-tools-curation -m "Curate tools to the 20 paid tools (Phase 2)"
```
Expected: fast, clean merge. Do **not** push unless the owner asks (Phase 3 follows; deploy is a deliberate, separately-gated step).

- [ ] **Step 4: Update the progress ledger**

Append Phase 2 task outcomes to `.superpowers/sdd/progress.md` in the outer repo (mirroring the Phase 1 format) and note that Phase 2 is complete on `tools` branch `main`.

---

## Self-Review Notes

- **Spec coverage:** commit WIP + branch (Task 0); trim to 20 across all three registration points + delete components (Task 2, guarded by Task 1 + build); `freeLimit` data with per-category defaults and per-tool exceptions (Task 3); 301 middleware redirects with system-path excludes (Task 4); minimal homepage fix (Task 5); verification + merge (Task 6). The marketing-site count and full pricing UI are explicitly out of scope per the design.
- **No test runner:** the repo has neither vitest nor jest and `AGENTS.md` discourages new deps, so the drift guard is a zero-dependency Node script (Task 1, red→green at Task 2) and correctness is enforced by `tsc --noEmit` + `next build` + the manual matrix, rather than unit tests. Phase 2 contains no pure business logic that would warrant a unit harness.
- **Idempotency / safety:** `curate.mjs` is a no-op on a second run (already-trimmed); `add-freelimits.mjs` refuses to run twice (guards on an existing `freeLimit:`); `git add -A` in Task 2 is scoped to the `tools` repo only.
- **Type consistency:** `FreeLimit` (Task 3) is referenced by `Tool.freeLimit` and the `add-freelimits.mjs` objects use exactly its fields (`maxFiles`, `maxPages`, `maxBytes`, `maxSeconds`, `note`). `toolsBySlug` (Task 4) is the existing export in `lib/tools.ts:19150`.
- **Drift risk:** the curated 20 in `tools` and in `pro/lib/catalog/paid-tools.ts` are kept in sync manually; `check-curated.mjs` alarms if `tools.ts` ever diverges from the hardcoded 20.
