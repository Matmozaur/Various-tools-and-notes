import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # Exploring `TourFlow` with Metaflow's Runner + Client APIs

    This notebook **launches** runs of [`tour_flow.py`](tour_flow.py) programmatically
    (`metaflow.Runner`) and then **inspects** everything Metaflow recorded
    (`metaflow.Flow / Run / Step / Task`, `metaflow.cards.get_cards`).

    Uses the shared `ML_related_tools` uv environment. Metaflow needs a POSIX OS
    (it imports `fcntl`), so on Windows run it from WSL/Linux, inside this directory:

    ```bash
    uv run marimo edit explore_tour.py
    ```
    """)
    return


@app.cell
def _():
    import os
    from pathlib import Path

    # The local metadata/datastore lives in ./.metaflow - the Client finds it by walking
    # up from the working directory, so pin cwd to this folder before importing metaflow.
    HERE = Path(__file__).resolve().parent
    os.chdir(HERE)

    import marimo as mo
    import matplotlib.pyplot as plt
    import polars as pl
    from metaflow import Flow, Runner, namespace
    from metaflow.cards import get_cards

    # Runs are tagged with `user:<name>` and the default namespace only shows yours.
    # namespace(None) = global namespace, see everything in this datastore.
    namespace(None)
    FLOW_FILE = str(HERE / "tour_flow.py")

    # Bumped by the launch/resume cells; every cell reading it re-runs -> fresh run list.
    get_runs_version, set_runs_version = mo.state(0)
    return (
        FLOW_FILE, Flow, Runner, get_cards, get_runs_version, mo, pl, plt, set_runs_version,
    )


@app.cell
def _(mo):
    mo.md(r"""
    ## 1. Launch a run

    Every widget maps to a `Parameter` of the flow. *Crash in train_final* sets the
    `TOUR_CRASH=1` env var, so the run fails in `train_final` and you can **resume** it
    below: finished tasks are cloned from the failed run, only `train_final` onward runs again.
    """)
    return


@app.cell
def _(mo):
    seed = mo.ui.number(start=0, stop=10_000, value=42, label="seed")
    min_accuracy = mo.ui.slider(0.90, 1.0, step=0.005, value=0.95, label="min_accuracy", show_value=True)
    flaky = mo.ui.checkbox(value=True, label="flaky (show @retry)")
    broken = mo.ui.checkbox(value=True, label="inject_broken_model (show @catch)")
    crash = mo.ui.checkbox(value=False, label="crash in train_final (show resume)")
    tag = mo.ui.text(value="from-notebook", label="extra tag")
    launch = mo.ui.run_button(label="Run TourFlow")
    mo.vstack([mo.hstack([seed, min_accuracy, tag]), mo.hstack([flaky, broken, crash]), launch])
    return broken, crash, flaky, launch, min_accuracy, seed, tag


@app.cell
def _(
    FLOW_FILE, Runner, broken, crash, flaky, launch, min_accuracy, mo, seed, set_runs_version, tag,
):
    mo.stop(not launch.value, mo.md("*Press **Run TourFlow** to start a run (~1 min).*"))

    env = {"TOUR_CRASH": "1"} if crash.value else {}
    with mo.status.spinner(title="Running TourFlow..."):
        # Runner(...) takes top-level CLI options, .run(...) takes `run` options + Parameters.
        with Runner(FLOW_FILE, show_output=False, env=env) as runner:
            result = runner.run(
                seed=int(seed.value),
                min_accuracy=float(min_accuracy.value),
                flaky=flaky.value,
                inject_broken_model=broken.value,
                tags=[t for t in [tag.value.strip()] if t],
            )
    set_runs_version(lambda v: v + 1)
    mo.md(f"**{result.status}** - run `{result.run.pathspec}` (return code {result.returncode})")
    return


@app.cell
def _(mo):
    resume_btn = mo.ui.run_button(label="Resume latest failed run from train_final")
    resume_btn
    return (resume_btn,)


@app.cell
def _(FLOW_FILE, Flow, Runner, mo, resume_btn, set_runs_version):
    mo.stop(not resume_btn.value)

    failed = next((r for r in Flow("TourFlow") if r.finished and not r.successful), None)
    mo.stop(failed is None, mo.md("No failed run to resume."))
    with mo.status.spinner(title=f"Resuming {failed.pathspec}..."):
        with Runner(FLOW_FILE, show_output=False) as resumer:
            resumed = resumer.resume(step_to_rerun="train_final", origin_run_id=failed.id)
    set_runs_version(lambda v: v + 1)
    mo.md(f"**{resumed.status}** - resumed `{failed.id}` as `{resumed.run.pathspec}` "
          f"(`origin-run-id` metadata links them)")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 2. All runs of the flow
    """)
    return


@app.cell
def _(Flow, pl):
    def list_runs():
        rows = []
        for r in Flow("TourFlow"):  # newest first
            summary = r.data.summary if r.successful else {}
            rows.append({
                "run_id": r.id,
                "created": r.created_at,
                "finished": r.finished,
                "successful": r.successful,
                "decision": summary.get("decision"),
                "best_model": summary.get("best_model"),
                "test_acc": summary.get("test_accuracy"),
                "user_tags": ", ".join(sorted(r.user_tags)),
                # set on runs created by `resume`
                "origin_run": r["start"].task.metadata_dict.get("origin-run-id") if "start" in r else None,
            })
        return pl.DataFrame(rows)
    return (list_runs,)


@app.cell
def _(get_runs_version, list_runs, mo):
    get_runs_version()  # re-run this cell whenever a run is launched/resumed
    runs_df = list_runs()
    mo.ui.table(runs_df, selection=None)
    return (runs_df,)


@app.cell
def _(mo, runs_df):
    ok_ids = runs_df.filter("successful")["run_id"].to_list()
    run_picker = mo.ui.dropdown(
        options=runs_df["run_id"].to_list(),
        value=ok_ids[0] if ok_ids else (runs_df["run_id"][0] if len(runs_df) else None),
        label="Inspect run",
    )
    run_picker
    return (run_picker,)


@app.cell
def _(Flow, mo, run_picker):
    mo.stop(run_picker.value is None, mo.md("No runs yet - launch one above."))
    run = Flow("TourFlow")[run_picker.value]
    mo.md(f"""
    ## 3. Anatomy of run `{run.pathspec}`

    successful: **{run.successful}** · tags: `{sorted(run.tags)}`
    """)
    return (run,)


@app.cell
def _(pl, run):
    # Walk the Run -> Step -> Task hierarchy. Every task is one process (one attempt succeeded).
    task_rows = []
    for _step in run:
        for _task in _step:
            task_rows.append({
                "step": _step.id,
                "task_id": _task.id,
                "pathspec": _task.pathspec,
                "foreach_index": _task.index,
                "attempts": _task.current_attempt + 1,
                "successful": _task.successful,
                "caught_error": str(_task["fit_error"].data) if "fit_error" in _task and _task["fit_error"].data else None,
                "start": _task.created_at,
                "end": _task.finished_at,
            })
    tasks_df = (
        pl.DataFrame(task_rows)
        .with_columns(seconds=(pl.col("end") - pl.col("start")).dt.total_milliseconds() / 1000)
        .sort("start")
    )
    tasks_df.select(pl.exclude("pathspec"))
    return (tasks_df,)


@app.cell
def _(pl, plt, tasks_df):
    # Gantt chart: shows the parallelism of the static branch and of the (nested) foreach.
    _t0 = tasks_df["start"].min()
    _steps = tasks_df["step"].unique(maintain_order=True).to_list()
    _fig, _ax = plt.subplots(figsize=(9, 4))
    for _row in tasks_df.with_columns(
        rel=(pl.col("start") - _t0).dt.total_milliseconds() / 1000
    ).iter_rows(named=True):
        _color = "tab:red" if _row["caught_error"] else ("tab:orange" if _row["attempts"] > 1 else "tab:blue")
        _ax.barh(_steps.index(_row["step"]), _row["seconds"], left=_row["rel"], color=_color, alpha=0.6, edgecolor="k")
    _ax.set_yticks(range(len(_steps)), _steps)
    _ax.invert_yaxis()
    _ax.set_xlabel("seconds since run start")
    _ax.set_title("Task timeline (orange = retried, red = @catch'ed)")
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 4. Artifacts

    `run.data` is shorthand for the artifacts of the `end` task. Artifacts of any other
    task are reachable via `run[step].task.data` (or iterate tasks for foreach steps).
    """)
    return


@app.cell
def _(mo, pl, run):
    mo.stop(not run.successful, mo.md("*Run did not finish successfully - pick another run.*"))
    leaderboard = pl.DataFrame(
        [{k: v for k, v in r.items() if k != "params"} | {"params": str(r["params"])}
         for r in run["select_best"].task.data.leaderboard]
    )
    mo.vstack([
        mo.md("**`summary`** (from `finalize`, carried to `end`)"),
        mo.json(run.data.summary),
        mo.md("**`leaderboard`** (built in the `select_best` join)"),
        mo.ui.table(leaderboard, selection=None),
    ])
    return (leaderboard,)


@app.cell
def _(leaderboard, pl, plt, run):
    # Per-fold scores live on the individual fit_fold tasks - aggregate them straight from the Client.
    _folds = pl.DataFrame([
        {"model": t.data.spec_name, "fold": t.data.fold, "score": t.data.score}
        for t in run["fit_fold"] if t.data.score is not None
    ])
    _order = leaderboard.filter(pl.col("status") == "ok")["name"].to_list()
    _fig, _ax = plt.subplots(figsize=(8, 3.5))
    _ax.boxplot([_folds.filter(pl.col("model") == m)["score"].to_list() for m in _order], tick_labels=_order)
    _ax.axhline(run.data.min_accuracy, ls="--", c="gray", label="min_accuracy")
    _ax.axhline(run.data.test_accuracy, ls=":", c="green", label=f"final test acc ({run.data.best_spec['name']})")
    _ax.set_ylabel("CV fold accuracy")
    _ax.legend(loc="lower left")
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 5. Logs and cards of a single task
    """)
    return


@app.cell
def _(mo, pl, tasks_df):
    # Default to train_final - it has the richest custom card.
    _final = tasks_df.filter(pl.col("step") == "train_final")["pathspec"]
    task_picker = mo.ui.dropdown(
        options=tasks_df["pathspec"].to_list(),
        value=_final[0] if len(_final) else tasks_df["pathspec"][0],
        label="task",
        searchable=True,
    )
    task_picker
    return (task_picker,)


@app.cell
def _(get_cards, mo, task_picker):
    from metaflow import Task

    _task = Task(task_picker.value)
    _cards = list(get_cards(_task))
    mo.ui.tabs({
        "stdout": mo.plain_text(_task.stdout or "(empty)"),
        "stderr": mo.plain_text(_task.stderr or "(empty)"),
        "artifacts": mo.json({a.id: repr(a.data)[:200] for a in _task}),
        # Cards are self-contained HTML pages - embed them as iframes.
        **{f"card: {c.id or c.type}": mo.iframe(c.get(), height="600px") for c in _cards},
    })
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 6. Across runs: tags as a query language

    `Flow(...).runs("promoted")` filters by tag - `promote` / `reject` steps add these tags
    from inside the flow, `--tag` / `tags=[...]` add them at launch.
    """)
    return


@app.cell
def _(Flow, mo, pl):
    _rows = []
    for _tag in ["promoted", "rejected"]:
        for _r in Flow("TourFlow").runs(_tag):
            _rows.append({
                "tag": _tag,
                "run_id": _r.id,
                "seed": _r.data.seed,
                "min_accuracy": _r.data.min_accuracy,
                "best_model": _r.data.best_spec["name"],
                "test_accuracy": _r.data.test_accuracy,
            })
    mo.ui.table(pl.DataFrame(_rows), selection=None) if _rows else mo.md("*No tagged runs yet.*")
    return


if __name__ == "__main__":
    app.run()
