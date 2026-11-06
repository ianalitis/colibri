# Development fork

This is fork-maintenance documentation, not an upstream contribution or a new
inference runner. Keep upstream fixes separate from this setup.

## Repository layout

| Name | Role |
| --- | --- |
| `origin` | Personal fork, `https://github.com/ianalitis/colibri.git` |
| `upstream` | Original project, `https://github.com/JustVugg/colibri.git` |
| `main` | Local stable mirror of `upstream/main`, tracking `origin/main` |
| `fork/development` | Local integration branch carrying these fork tools |
| `upstream/dev` | Upstream PR target, per [CONTRIBUTING.md](../CONTRIBUTING.md) |

This matches the sibling mlx-serve checkout's remote naming. Push defaults point
at `origin`, but that is not a push authorization or a technical block on upstream
writes. Do not push upstream. Do not commit fork tooling or issue fixes on `main`.
The development branch is local until its exact publication is approved.

For another clone, add `upstream` with the URL above and fetch both `main` and
`dev`. A shallow or single-branch clone needs its fetch coverage/history completed
before ancestry checks or contribution work. Preserve existing clone configuration
unless changing it is part of the approved setup.

## Sync without losing development work

From the checkout root:

```sh
bash scripts/fork-sync.sh status     # offline, cached ahead/behind counts
bash scripts/fork-sync.sh fetch      # refresh both remotes, no integration
bash scripts/fork-sync.sh sync-main  # clean fork/development only, local main FF
python3 scripts/test_fork_sync.py -v
```

Acquire the repository's write lease before fetching or changing refs, including
when another checkout/worktree shares the Git common directory. The script does
not implement a lock. It never pushes, resets, stashes, switches branches, or
merges development work. `sync-main` refuses dirty/staged/untracked work, a wrong
branch, non-fast-forward `main`, or `main` checked out in another worktree.
Ignored build/model outputs do not make the tree dirty. Fetch failures stop it.

To integrate a reviewed stable update into the development branch, first refresh
refs, record their full SHAs, inspect the incoming diff and upstream contribution
rules, and obtain approval for that integration. With a clean leased checkout on
`fork/development`, prepare the ancestry-preserving merge:

```sh
git merge --no-ff --no-commit upstream/main
make check
python3 scripts/test_fork_sync.py -v
```

Inspect the result and commit the passing merge normally, preserving both parents.
Stop on conflicts or failed gates. Do not reset or rebase fork history to make an
ahead/behind count disappear. Publishing `main` or `fork/development` to `origin`
is a separate, explicitly approved push of the named refs. There is deliberately
no scheduled push, automatic merge, release action, or unattended issue/PR bot.

## Upstream issue and PR work

1. Pin current `upstream/dev`, read the current contribution rules, templates and
   full discussion. Check open, closed and merged PRs for overlapping work. Respect
   any maintainer restrictions. Reproduce on current code before proposing a fix.
2. After approval for the named branch/isolation, start one focused issue branch
   from `upstream/dev`, not from `fork/development`. Keep fork-only documentation,
   scripts, generated models and local agent instructions out of the patch.
3. Use one writer and a bounded Jcode task: exact refs, permitted files, expected
   observable behavior, targeted regression command, iteration cap and stop rules.
   Jcode owns task lifecycle and verification. Do not add a second runner or
   silently change model/provider settings. Review delegated output independently.
4. Run the targeted regression and `make check`. Engine changes additionally need
   the strict oracle commands in CONTRIBUTING. Missing fixture dependencies or
   unavailable hardware are blockers, not passes. Performance claims require the
   upstream experiment manifest and raw evidence.
5. Prepare a local receipt under `docs/upstream-feedback/` with tested/current SHAs,
   reproduction, duplicate check, changed paths, actual checks and limitations.
   Recheck upstream HEAD/discussion immediately before any external effect. Get
   approval for the exact repository, branch, patch and submission text. Public
   agent-posted issue/PR prose ends `Agent on behalf of @ianalitis.` Run the
   operator's contribution preflight before sending. No bulk PR generation.

## Local inference beside mlx-serve

Keep the existing mlx-serve service on `127.0.0.1:11234` untouched. Use Colibri's
existing [CLI/API](api.md) on a separate loopback port, for example `18000`.
Do not use `coli setup`, `web` or `start` as a development smoke command: they can
download/build, persist setup state, start services or open a browser.

With an already approved, complete Colibri-format model and sufficient free
memory, run from the checkout root:

```sh
python3 c/coli doctor --model /path/to/colibri-model --deep
python3 c/coli serve --model /path/to/colibri-model \
  --host 127.0.0.1 --port 18000 --model-id colibri-local \
  --ram 8 --ctx 2048 --ngen 128 --gpu none --temp 0
```

This is a headless foreground command for an owned process, not a launchd service.
RAM is an expert-cache budget, not a hard process-memory ceiling. Check total model
and KV/workspace memory before launch. Never kill, unload, restart or compete with
an active mlx-serve inference session. Run large models sequentially in an approved
idle window. New downloads, installs and global Jcode provider/profile changes
need separate approval. MLX weight packs are not automatically Colibri-compatible.
Metal is opt-in and needs its own build and correctness checks, see [metal.md](metal.md).

An already-cached [Laya](laya.md) checkpoint also works directly, without conversion
or a persistent server: `make -C c laya`, then `c/laya --model /path/to/laya
--records /path/to/records.json`. Records are a JSON array of objects whose
`payload` is the serialized `systemone_decision_record` from `c/openai_server.py`.
Use one short-lived child, a cleared allowlisted environment with Hub offline
switches, bounded threads/time and measured peak RSS below 5 GB. Laya answers
closed-set decisions, not chat: its HTTP route is `/v1/systemone`, not
`/v1/chat/completions`. A passing Laya smoke is not a chat-engine A/B result.

Use upstream's existing HTTP benchmark rather than introducing another harness:

```sh
python3 c/tools/benchmark_http_serving.py \
  --base-url http://127.0.0.1:18000/v1 --model colibri-local \
  --workload /path/to/public-prompts.jsonl --concurrency 1 --repeats 3 \
  --output /path/to/colibri-result.json
```

Repeat against `http://127.0.0.1:11234/v1` with the actual mlx-serve model ID and
a separate output file. Record both source/binary revisions, weights and hashes,
quantization, tokenizer/template, generation and reasoning settings, hardware,
cache state, memory, warmup, commands and raw results. Follow
[benchmarking.md](benchmarking.md) for workload format and interpretation. Different
weight formats/models are a deployment comparison, not an engine speed ranking.
Protocol success and throughput do not establish output quality or oracle parity.
Evaluate quality separately on public/synthetic tasks. Local inference stays
advisory and never gains arbitrary tools, credentials or effect authority.

## Setup receipt, 2026-11-06

- Stable base: `0a5504a1dc64f86fcd0fe7db298b0448c730e7e6`. Fetched integration
  base: `e24cd51afd44b480c1e41ba82e20a28bac76c34f`. Personal fork creation and
  parent relationship verified with GitHub's native `gh` interface. Full clone
  history restored, both upstream branches tracked, and push defaults set to
  `origin` / `simple`. No development commits pushed and no issue/PR submitted.
- Fork tooling: seven real local-Git tests passed, `bash -n` and ShellCheck
  passed, and `sync-main` passed in this checkout without moving development
  HEAD. Main and both remote main refs matched the stable base at that check.
- Project checks on macOS arm64: `make check` completed the clean/portable build
  and entered regression tests, but the tool stopped it after 600 seconds despite
  a requested 1,800-second timeout. This was not a pass. The continuation
  `make -C c test` passed the C suites and the Python suite (2,896 tests,
  439 skipped) against that fresh build. Existing upstream compiler/ResourceWarnings were not
  suppressed or fixed. `make -C c laya` and `make -C c qwen36` also passed.
- Real offline CPU smoke: cached `convaiinnovations/laya`, revision
  `1c5edc17a7acd8701df6fc341c0d179f1c62c982`, passed `coli doctor --deep` and a
  single native `--records` request. State: "The user asks for a refund after a
  duplicate payment." Question: "Which department should handle this request?"
  Ordered choices: billing (payments and refunds), technical (software errors),
  sales (new contracts). Expected and observed argmax: billing. Probabilities:
  `[0.857918719, 0.0970507652, 0.045030516]`, finite and normalized. Engine time
  554.098 ms, total child round trip 1.206 s, measured peak RSS 1,884,667,904 bytes.
  One child, two OMP threads, cleared allowlisted environment, Hub offline
  switches and a 60-second deadline. Child exited, no model download or service
  install, and the original mlx-serve listener was preserved. This is one smoke
  result, not a general quality or performance claim.
- Laya weights SHA-256:
  `891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c`.
  Built Laya binary SHA-256:
  `566cf50bbabf682f818de88568bd99d4ba68ccd6199716b41c38dda0ae5bf4f5`.
  Still unrun: strict generated GLM oracle, Metal/CUDA validation, a production
  Colibri chat-model smoke and a matched chat benchmark against mlx-serve. No
  global Jcode profile or installed inference-service configuration was changed.
