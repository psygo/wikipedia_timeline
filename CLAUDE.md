# Working in this repository

TimelineRail for Wikipedia: Lua modules (`lua/`), templates and styles (`template/`), a prototype and
userscripts, and Python converters (`tools/`) that write article drafts into `drafts/`. `README.md` lists
every wiki page and the file to paste into it; `lua/README.md` has the step by step.

## Conventions

- Commit messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Push whenever you commit.
- README tables are HTML (`<table>`), because formatters break Markdown tables. Copy an existing `<tr>` to add a row.
- Run the Lua tests with `luajit lua/test/test.lua` before committing changes to `lua/`.
- Every push triggers the GitHub Pages deploy (`.github/workflows/pages.yml`). After each push, check it:
  `gh run list --limit 1` (wait with `gh run watch`). If it failed, read `gh run view <id> --log-failed`: a
  transient GitHub error (HTTP 5xx from `deploy-pages`) gets `gh run rerun <id> --failed`; anything else is
  fixed in a new commit. Do not report a task as done while the latest run is red, and say so if it stays red.
- Drafts in `drafts/` are generated: change the converter in `tools/` and regenerate, do not edit them by hand.

## Audit every 20 commits

Every 20 commits, run a security and efficiency audit. The last audit is recorded by the git tag
`audit-last` (it does not exist yet: before the first audit, count from the first commit).

**When to run it.** At the start of a session, and before committing, check:

```sh
git rev-list --count audit-last..HEAD   # if the tag is missing: git rev-list --count HEAD
```

If the number is 20 or more, do the audit before anything else (or right after the current change is
committed), then move the tag: `git tag -f audit-last && git push -f origin audit-last`.

**What to check**

*Security*
- Lua modules: every value interpolated into HTML is escaped (`esc`, `anchor`); no user-supplied
  attribute or URL reaches the output unescaped; no `mw.html` or `#tag` use that allows script, `style`
  injection or event attributes; nothing built from `frame.args` goes into `href`/`src` unchecked.
- Userscripts and the prototype/shim/React/web-component code: no `innerHTML` with unsanitised
  input, no `eval`, no inline handlers, safe use of `mw.*` APIs, no tokens or credentials committed.
- CSS: only what TemplateStyles allows; no `url()` to external hosts.
- Python tools: network calls only to the wiki APIs, timeouts set, nothing written outside the
  repo, no shell built from fetched text, cached files in `tools/.cache/` ignored by git.
- Dependencies (`react/`, `web-component/`): `npm audit` for known vulnerabilities; GitHub Actions
  workflows with minimal permissions and pinned actions; no secrets in the repository or the history.

*Efficiency*
- Wikipedia limits: post-expand include size (2,097,152 bytes) and Lua time of each draft, checked
  with the parse API (`prop=limitreportdata`); any draft above 70 percent of a limit is reported.
- Lua modules: no repeated work per event (string concatenation in loops, repeated pattern scans,
  rebuilding tables); expensive parser calls (`frame:preprocess`, `mw.title`, `#ifexist`) counted.
- Generated HTML and CSS: size per event, unused rules, selectors that are slow or fragile.
- Converters: repeated fetches that the cache should serve, quadratic loops over events.

**Output.** Write the findings to `docs/audits/YYYY-MM-DD.md` (severity, file and line, what to do),
fix the clear and safe ones in the same session in separate commits, list the rest for the user, and
never apply a risky fix without asking. Then move the tag.
