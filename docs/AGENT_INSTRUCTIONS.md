# Cloud agent instructions — resume evo autoresearch run

You're picking up a stalled `evo` optimization run on the QuitTxt RAG
data-generation pipeline. Everything you need is in this repo. Follow the
steps in order — don't skip the state-snapshot restore, or evo will not know
about the 24 experiments that already ran.

## 1. Clone

```bash
git clone https://github.com/anudeepadi/gemini-protocol.git
cd gemini-protocol
```

This repo also carries 19 `evo/run_0000/exp_NNNN` branches — those are the
actual code diffs for each past experiment. Leave them alone; evo manages
them.

## 2. Python environment

Python 3.13 required (ragas 0.4.3 is pinned and version-sensitive — see
comment at the top of `requirements.txt`, do not upgrade it).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Install evo

Installed via `uv` as a standalone tool (not a repo dependency):

```bash
# install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh
exec $SHELL   # reload PATH

uv tool install evo-hq-cli
evo --version   # confirm it runs
```

This installs three commands: `evo`, `evo-dashboard`, `evo-drain`.

## 4. API key

```bash
# code/.env is gitignored — did NOT come across in the clone
echo "OPENAI_API_KEY=sk-..." > code/.env
```

evo reads the key via `evo env` (configured in
`.evo/run_0000/config.json` → `runtime_env.dotenv`), and injects it into
each experiment worktree; the worktrees don't read the file directly.

## 5. Restore evo's orchestrator state

The `.evo/` directory itself is git-excluded on the source machine (local
`.git/info/exclude`), so its metadata — experiment scores, the decision
graph, verifier annotations — was packaged separately into
`evo_state_snapshot/` and IS in this repo. Move it into place:

```bash
mkdir -p .evo
cp -R evo_state_snapshot/run_0000 .evo/run_0000
cp evo_state_snapshot/meta.json evo_state_snapshot/project.md .evo/
rm -rf evo_state_snapshot   # optional cleanup, already committed to history
```

This snapshot excludes `worktrees/` (evo regenerates those on demand from
the `evo/run_0000/exp_*` branches you already have) and pid/lock/log files
(stale from the source machine — evo will recreate them).

## 6. Confirm state matches expectations

```bash
evo status
```

Expected: `epoch=4 experiments=29 committed=11 evaluated=0 discarded=10
failed=0 active=0 best=0.8347`.

Then check the run isn't mid-experiment:

```bash
ls .evo/run_0000/experiments/exp_0028/
```

Expected: **empty directory**. That's the known stall point — an
orchestrator run was launched and interrupted before exp_0028 got a
`result.json`. This is safe to resume from; it's not a corrupted experiment,
just an incomplete one.

## 7. Resume the run

```bash
evo run
```

This is epoch-4 (dev/test split frozen, deterministic refusal scoring,
full-source parity — see `.evo/project.md` for full methodology). Current
epoch-4 scores (exp_0025/26/27: 0.8201–0.8227) are all within the measured
noise floor (sd≈0.012) of each other — there's no confirmed improvement yet.
The point of resuming is to get enough experiments to tell signal from
noise.

Stop condition: no committed improvement over ~4-5 more rounds, or a
result that clears the noise floor (>0.03 delta, then re-run once to
confirm before trusting it — see "Benchmark determinism" in
`.evo/project.md`).

## 8. Push results back

Same pattern as the initial push — code changes land as `evo/run_0000/exp_*`
branches, orchestrator metadata needs a manual snapshot:

```bash
git push origin master
git for-each-ref --format='%(refname:short)' refs/heads/evo | xargs git push origin

# snapshot updated evo state for the next machine
rsync -a --exclude='worktrees' --exclude='*.log' --exclude='*.pid' \
  --exclude='*.lock' --exclude='*.port' \
  .evo/run_0000/ evo_state_snapshot/run_0000/
cp .evo/meta.json .evo/project.md evo_state_snapshot/
git add evo_state_snapshot
git commit -m "chore: snapshot evo orchestrator state after resumed run"
git push origin master
```

## Context: why this run exists

A reviewer (Ebrahim) flagged that the same 150-question test set was used
both to select the winning generation config AND to report the final parity
number — classic benchmark overfitting. Epoch 4 is the fix: dev/test split
frozen (`674b763`), plus completeness/refusal metric additions. This run
needs to reach a real verdict — committed but unconfirmed scores don't
resolve the reviewer objection. Full methodology, gaming-risk log, and prior
epoch history: `.evo/project.md`. Prior findings write-up (pre-fix, will
need updating once this run concludes): `docs/evo_autoresearch_findings.md`.

## Do NOT

- Don't touch `run_data_gen_experiment.py`, `data_gen_prepare.py`, or
  anything under `datasets/` — protected by the `harness_integrity` gate,
  and touching them breaks comparability with the prior 24 experiments.
- Don't change `RAG_TEMPLATE` without checking the human-baseline score
  moves in lockstep — see "Benchmark gaming risks" in `.evo/project.md`.
- Don't promote a single-run result under ~0.03 delta as a win — re-run to
  confirm first.
