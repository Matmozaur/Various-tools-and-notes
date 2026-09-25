"""
TourFlow - a single Metaflow flow that deliberately touches as many concepts as possible.

Task: pick the best classifier for a tabular dataset (sklearn breast cancer by default)
with cross-validation, retrain it, then either "promote" or "reject" it.

Graph:

    start
      ├── profile_data ──┐              (static split / join)
      └── split_data ────┴── join_data
                               │
                             plan_grid
                               │ foreach model spec
                             build_model
                               │ foreach CV fold               (nested foreach)
                             fit_fold      @retry @catch @timeout @resources @environment
                               │
                             aggregate_folds                   (join of inner foreach)
                               │
                             select_best                       (join of outer foreach)
                               │
                             train_final   @card(report)
                               │ switch on self.decision       (conditional branch)
                   ┌───────────┴───────────┐
                promote                  reject
                   └───────────┬───────────┘
                            finalize
                               │
                              end          @card(default)

Concepts shown (grep for the tag to jump to it):
  [PARAM]      Parameter (int/float/bool/str), JSONType, deploy-time default (callable)
  [INCLUDE]    IncludeFile - a local file versioned together with the run
  [CONFIG]     Config (config.json), config values inside decorators and defaults
  [PROJECT]    @project - namespacing of runs / branches
  [MUTATOR]    FlowMutator - programmatically adds decorators to every step
  [USERDECO]   user_step_decorator - custom step wrapper
  [CURRENT]    `current` - run/step/task ids, retry count, project info, tags
  [BRANCH]     static split + join with `inputs.<step>` and merge_artifacts
  [FOREACH]    foreach fan-out, nested foreach, self.input / self.index / foreach_stack
  [RETRY]      @retry with a simulated transient failure
  [CATCH]      @catch turning a permanent failure into data
  [RESOURCES]  @resources / @timeout / @environment
  [CARD]       default + custom cards: Markdown, Table, ValueBox, ProgressBar, VegaChart, Image
  [SWITCH]     conditional transition self.next({...}, condition=...)
  [TAGS]       adding tags to the run from inside the flow (Client API)
  [RESUME]     env var TOUR_CRASH=1 makes train_final fail so you can `resume` it
  [PARALLEL]   metaflow.parallel_map for in-task parallelism

Uses the shared ML_related_tools uv env. Linux / macOS / WSL only (Metaflow imports fcntl):
    uv run python tour_flow.py show            # print the graph
    uv run python tour_flow.py run             # run with defaults
    uv run python tour_flow.py run --seed 7 --min_accuracy 0.99 --tag experiment
    TOUR_CRASH=1 uv run python tour_flow.py run && uv run python tour_flow.py resume train_final
    uv run python tour_flow.py card view train_final --id report
"""

import io
import os
import time

from metaflow import (
    Config,
    FlowMutator,
    FlowSpec,
    IncludeFile,
    JSONType,
    Parameter,
    card,
    catch,
    current,
    environment,
    parallel_map,
    project,
    resources,
    retry,
    step,
    timeout,
    user_step_decorator,
)
from metaflow.cards import Image, Markdown, ProgressBar, Table, ValueBox, VegaChart


# --------------------------------------------------------------------------- helpers
# Module-level code is packaged with the flow, so every task (local process, or a
# remote container with --with kubernetes) can use it.


def make_estimator(family, params, seed):
    """Build an sklearn pipeline from a (family, params) model spec."""
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    families = {
        "logreg": lambda p: LogisticRegression(max_iter=2000, random_state=seed, **p),
        "random_forest": lambda p: RandomForestClassifier(random_state=seed, n_jobs=1, **p),
        "gradient_boosting": lambda p: GradientBoostingClassifier(random_state=seed, **p),
        "knn": lambda p: KNeighborsClassifier(**p),
    }
    if family not in families:
        raise ValueError(f"unknown model family {family!r}, expected one of {sorted(families)}")
    return make_pipeline(StandardScaler(), families[family](dict(params)))


# [USERDECO] A custom step decorator is a generator: code before `yield` runs before the
# step body, code after runs once it finished. `attributes` holds the decorator kwargs.
@user_step_decorator
def timed(step_name, flow, inputs=None, attributes=None):
    label = (attributes or {}).get("label", "timed")
    t0 = time.perf_counter()
    try:
        yield
    finally:
        # Goes to the task's stdout - visible later through Task(...).stdout
        print(f"[{label}] step '{step_name}' body took {time.perf_counter() - t0:.3f}s")


# [MUTATOR] A FlowMutator sees the whole flow before it runs and can add parameters or
# decorators. Here: wrap every step in @timed, but only if the config asks for it.
class time_every_step(FlowMutator):
    def pre_mutate(self, mutable_flow):
        cfg = dict(mutable_flow.configs)["config"]
        if not cfg.time_every_step:
            return
        for _, mstep in mutable_flow.steps:
            mstep.add_decorator(timed, deco_kwargs={"label": "auto-timed"})


# --------------------------------------------------------------------------- flow


@time_every_step
@project(name="metaflow_tour")  # [PROJECT]
class TourFlow(FlowSpec):
    # [CONFIG] Read once when the run starts, immutable, usable *inside decorators*
    # (see fit_fold). Override with: `run --config config other.json` or
    # `--config-value config '{"...": ...}'` (options go before `run`).
    cfg = Config("config", default="config.json")

    # [PARAM] Regular typed parameters -> `run --seed 7 --test_size 0.3 ...`
    seed = Parameter("seed", type=int, default=42, help="Random seed for splits and models.")
    test_size = Parameter("test_size", type=float, default=0.25, help="Held-out test fraction.")
    flaky = Parameter(
        "flaky", type=bool, default=True,
        help="Make one fit_fold task fail on its first attempt to show @retry.",
    )
    inject_broken_model = Parameter(
        "inject_broken_model", type=bool, default=True,
        help="Add a model spec that always fails to show @catch.",
    )
    # A Parameter whose default comes from the config file.
    min_accuracy = Parameter(
        "min_accuracy", type=float, default=cfg.promotion.min_accuracy,
        help="Test accuracy needed to promote the final model.",
    )
    # [PARAM] JSONType - structured input from the command line.
    extra_models = Parameter(
        "extra_models", type=JSONType, default="[]",
        help='Extra model specs, e.g. \'[{"name":"knn_5","family":"knn","params":{"n_neighbors":5}}]\'',
    )
    # [PARAM] Deploy-time default: a callable evaluated when the run starts.
    run_label = Parameter(
        "run_label", type=str,
        default=lambda ctx: f"{ctx.user_name}-{ctx.flow_name}-adhoc",
        help="Free-form label, defaults to <user>-<flow>-adhoc.",
    )
    # [INCLUDE] File contents are stored in the datastore as part of the run.
    data_file = IncludeFile(
        "data_file", is_text=True, default=None,
        help="Optional CSV; last column is the target. Defaults to sklearn breast cancer.",
    )

    # ----------------------------------------------------------------- start
    @step
    def start(self):
        import numpy as np

        # [CURRENT] Runtime context of this very task.
        print(f"flow={current.flow_name} run={current.run_id} step={current.step_name} "
              f"task={current.task_id} user={current.username}")
        print(f"pathspec={current.pathspec}")
        print(f"project={current.project_name} branch={current.branch_name} "
              f"project_flow_name={current.project_flow_name}")
        print(f"tags={sorted(current.tags)}  label={self.run_label}")

        if self.data_file:
            import polars as pl

            df = pl.read_csv(io.StringIO(self.data_file))
            self.feature_names = df.columns[:-1]
            self.X = df.select(self.feature_names).to_numpy().astype(float)
            y_raw = df.get_column(df.columns[-1]).to_numpy()
            classes, self.y = np.unique(y_raw, return_inverse=True)
            self.target_names = [str(c) for c in classes]
            self.dataset_name = "data_file"
        else:
            from sklearn.datasets import load_breast_cancer

            ds = load_breast_cancer()
            self.X, self.y = ds.data, ds.target
            self.feature_names = [str(f) for f in ds.feature_names]
            self.target_names = [str(t) for t in ds.target_names]
            self.dataset_name = self.cfg.data.dataset

        print(f"loaded {self.dataset_name}: X={self.X.shape}, classes={self.target_names}")
        # [BRANCH] Static split: both steps run in parallel.
        self.next(self.profile_data, self.split_data)

    # ----------------------------------------------------------------- static branch A
    @card(type="blank", id="profile", refresh_interval=1)  # [CARD] custom, updated live
    @step
    def profile_data(self):
        import numpy as np

        top_k = self.cfg.data.profile_top_k
        cols = list(range(self.X.shape[1]))

        # [CARD] A ProgressBar that refreshes while the task is running.
        progress = ProgressBar(max=len(cols), label="Profiling features", value=0)
        current.card["profile"].append(Markdown(f"# Data profile: `{self.dataset_name}`"))
        current.card["profile"].append(progress)
        current.card["profile"].refresh()

        # [PARALLEL] parallel_map forks worker processes inside this single task.
        def col_stats(j):
            col = self.X[:, j]
            return {
                "feature": self.feature_names[j],
                "mean": float(col.mean()),
                "std": float(col.std()),
                "corr_with_target": float(np.corrcoef(col, self.y)[0, 1]),
            }

        self.feature_stats = []
        for chunk_start in range(0, len(cols), 10):
            chunk = cols[chunk_start:chunk_start + 10]
            self.feature_stats.extend(parallel_map(col_stats, chunk))
            progress.update(len(self.feature_stats))
            current.card["profile"].refresh()

        counts = np.bincount(self.y)
        self.class_balance = {name: int(c) for name, c in zip(self.target_names, counts)}
        top = sorted(self.feature_stats, key=lambda r: -abs(r["corr_with_target"]))[:top_k]

        current.card["profile"].append(Markdown("## Class balance"))
        current.card["profile"].append(VegaChart({
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": [{"class": k, "count": v} for k, v in self.class_balance.items()]},
            "mark": "bar",
            "encoding": {
                "x": {"field": "class", "type": "nominal"},
                "y": {"field": "count", "type": "quantitative"},
            },
        }))
        current.card["profile"].append(Markdown(f"## Top {top_k} features by |corr(target)|"))
        current.card["profile"].append(Table(
            [[r["feature"], f"{r['mean']:.3g}", f"{r['std']:.3g}", f"{r['corr_with_target']:+.3f}"]
             for r in top],
            headers=["feature", "mean", "std", "corr"],
        ))
        self.next(self.join_data)

    # ----------------------------------------------------------------- static branch B
    @step
    def split_data(self):
        from sklearn.model_selection import train_test_split

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=self.test_size, random_state=self.seed, stratify=self.y
        )
        print(f"train={len(self.y_train)} test={len(self.y_test)}")
        self.next(self.join_data)

    # ----------------------------------------------------------------- static join
    @step
    def join_data(self, inputs):
        # [BRANCH] In a static join, parents are addressable by step name.
        self.class_balance = inputs.profile_data.class_balance
        self.feature_stats = inputs.profile_data.feature_stats
        # Everything else that is identical (X, y, names...) or only exists on one side
        # (X_train...) is merged automatically. Conflicting values would raise.
        self.merge_artifacts(inputs)
        # A join cannot also be a split (static or foreach) - that needs its own step.
        self.next(self.plan_grid)

    @step
    def plan_grid(self):
        # [CONFIG] + [PARAM] build the model grid.
        self.model_specs = [dict(m) for m in self.cfg.models] + list(self.extra_models)
        if self.inject_broken_model:
            # C must be > 0 - sklearn raises at fit time, every retry fails, @catch absorbs it.
            self.model_specs.append({"name": "broken_logreg", "family": "logreg", "params": {"C": -1.0}})
        print("model grid:", [m["name"] for m in self.model_specs])

        # [FOREACH] One build_model task per element of self.model_specs.
        self.next(self.build_model, foreach="model_specs")

    # ----------------------------------------------------------------- outer foreach body
    @step
    def build_model(self):
        # [FOREACH] self.input is this task's element, self.index its position.
        self.spec = self.input
        self.spec_name = self.spec["name"]
        print(f"model #{self.index}: {self.spec_name} ({self.spec['family']}) {self.spec['params']}")
        self.folds = list(range(self.cfg.cv.folds))
        # [FOREACH] Nested foreach: a fold fan-out inside every model branch.
        self.next(self.fit_fold, foreach="folds")

    # ----------------------------------------------------------------- inner foreach body
    @catch(var="fit_error", print_exception=False)  # [CATCH] failure -> artifact, flow goes on
    @retry(times=cfg.training.retries, minutes_between_retries=0)  # [RETRY] + [CONFIG] in a decorator
    @timeout(seconds=cfg.training.timeout_seconds)  # [RESOURCES]
    @resources(cpu=cfg.training.cpu, memory=cfg.training.memory_mb)  # used by --with kubernetes/batch
    @environment(vars={"OMP_NUM_THREADS": "1", "TOUR_STAGE": "cv"})
    @step
    def fit_fold(self):
        import numpy as np
        from sklearn.model_selection import StratifiedKFold

        self.fold = self.input
        self.score = None  # defined up-front so it exists even if the fit fails
        # [FOREACH] foreach_stack(): (index, num_splits, value) for every enclosing foreach.
        print("foreach stack:", [(idx, n) for idx, n, _value in self.foreach_stack()])
        print(f"attempt {current.retry_count} of {self.spec_name} fold {self.fold}, "
              f"OMP_NUM_THREADS={os.environ['OMP_NUM_THREADS']}")

        # [RETRY] Transient failure: only the first attempt of one task fails.
        if self.flaky and current.retry_count == 0 and self.fold == 0 and self.spec_name == self.model_specs[0]["name"]:
            raise RuntimeError("simulated transient failure (e.g. a flaky network call)")

        skf = StratifiedKFold(n_splits=len(self.folds), shuffle=True, random_state=self.seed)
        tr_idx, va_idx = list(skf.split(self.X_train, self.y_train))[self.fold]
        t0 = time.perf_counter()
        est = make_estimator(self.spec["family"], self.spec["params"], self.seed)
        est.fit(self.X_train[tr_idx], self.y_train[tr_idx])
        self.fit_seconds = time.perf_counter() - t0
        self.score = float(np.mean(est.predict(self.X_train[va_idx]) == self.y_train[va_idx]))
        print(f"fold {self.fold}: accuracy={self.score:.4f} in {self.fit_seconds:.2f}s")
        self.next(self.aggregate_folds)

    # ----------------------------------------------------------------- inner join
    @step
    def aggregate_folds(self, inputs):
        import numpy as np

        # [CATCH] Failed tasks carry the exception in `fit_error` instead of crashing the run.
        ok = [i for i in inputs if not getattr(i, "fit_error", None)]
        failed = [i for i in inputs if getattr(i, "fit_error", None)]
        self.fold_scores = [i.score for i in ok]
        self.errors = sorted({str(i.fit_error) for i in failed})
        self.mean_cv = float(np.mean(self.fold_scores)) if ok else None
        self.std_cv = float(np.std(self.fold_scores)) if ok else None
        # Per-fold artifacts differ between inputs, so exclude them from the merge.
        self.merge_artifacts(inputs, exclude=["fold", "score", "fit_error", "fit_seconds"])
        print(f"{self.spec_name}: ok={len(ok)} failed={len(failed)} mean_cv={self.mean_cv}")
        self.next(self.select_best)

    # ----------------------------------------------------------------- outer join
    @step
    def select_best(self, inputs):
        self.leaderboard = sorted(
            (
                {
                    "name": i.spec_name,
                    "family": i.spec["family"],
                    "params": i.spec["params"],
                    "mean_cv": i.mean_cv,
                    "std_cv": i.std_cv,
                    "status": "ok" if i.mean_cv is not None else "failed",
                    "errors": i.errors,
                }
                for i in inputs
            ),
            key=lambda r: (r["mean_cv"] is None, -(r["mean_cv"] or 0)),
        )
        ok = [r for r in self.leaderboard if r["status"] == "ok"]
        if not ok:
            raise RuntimeError("every model failed during CV - nothing to select")
        self.best_spec = ok[0]
        for r in self.leaderboard:
            print(f"{r['name']:>16}  {r['status']:>6}  cv={r['mean_cv']}")
        # Only carry over what later steps need; `include` is the whitelist form.
        self.merge_artifacts(
            inputs,
            include=["X_train", "X_test", "y_train", "y_test", "feature_names", "target_names",
                     "dataset_name", "class_balance"],
        )
        self.next(self.train_final)

    # ----------------------------------------------------------------- final model
    @card(type="blank", id="report")
    @step
    def train_final(self):
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, confusion_matrix

        # [RESUME] Crash on demand, then: `python tour_flow.py resume train_final`
        if os.environ.get("TOUR_CRASH") == "1":
            raise RuntimeError("TOUR_CRASH=1 - simulated crash, try `resume`")

        best = self.best_spec
        self.model = make_estimator(best["family"], best["params"], self.seed)
        self.model.fit(self.X_train, self.y_train)
        pred = self.model.predict(self.X_test)
        self.test_accuracy = float(accuracy_score(self.y_test, pred))
        self.confusion = confusion_matrix(self.y_test, pred).tolist()

        # [SWITCH] The value of this artifact picks the next step.
        self.decision = "promote" if self.test_accuracy >= self.min_accuracy else "reject"

        rc = current.card["report"]
        rc.append(Markdown(f"# Final model: `{best['name']}`\nfamily `{best['family']}`, params `{best['params']}`"))
        rc.append(ValueBox(
            title="Test accuracy", value=f"{self.test_accuracy:.4f}",
            subtitle=f"threshold {self.min_accuracy}",
            theme="success" if self.decision == "promote" else "danger",
            change_indicator=f"decision: {self.decision}",
        ))
        rc.append(Markdown("## CV leaderboard"))
        rc.append(Table(
            [[r["name"], r["family"], r["status"],
              "-" if r["mean_cv"] is None else f"{r['mean_cv']:.4f} ± {r['std_cv']:.4f}"]
             for r in self.leaderboard],
            headers=["model", "family", "status", "cv accuracy"],
        ))
        fig, ax = plt.subplots(figsize=(4, 4))
        ConfusionMatrixDisplay(confusion_matrix(self.y_test, pred), display_labels=self.target_names).plot(ax=ax, colorbar=False)
        rc.append(Image.from_matplotlib(fig, label="Confusion matrix (test)"))
        plt.close(fig)

        self.next({"promote": self.promote, "reject": self.reject}, condition="decision")

    # ----------------------------------------------------------------- switch branches
    @step
    def promote(self):
        from metaflow import Run

        # [TAGS] Runs are queryable by tag later: Flow("TourFlow").runs("promoted")
        run = Run(f"{current.flow_name}/{current.run_id}")
        run.add_tags(["promoted", f"model:{self.best_spec['name']}"])
        self.outcome = f"promoted {self.best_spec['name']} (acc={self.test_accuracy:.4f})"
        self.next(self.finalize)

    @step
    def reject(self):
        from metaflow import Run

        Run(f"{current.flow_name}/{current.run_id}").add_tag("rejected")
        self.outcome = (f"rejected {self.best_spec['name']}: "
                        f"{self.test_accuracy:.4f} < {self.min_accuracy}")
        self.next(self.finalize)

    # ----------------------------------------------------------------- after the switch
    @step
    def finalize(self):
        # Not a join: only one of promote/reject ran, so there is a single parent.
        self.summary = {
            "run_label": self.run_label,
            "dataset": self.dataset_name,
            "best_model": self.best_spec["name"],
            "cv_accuracy": self.best_spec["mean_cv"],
            "test_accuracy": self.test_accuracy,
            "decision": self.decision,
            "outcome": self.outcome,
        }
        print(self.summary)
        self.next(self.end)

    @card  # [CARD] the default card renders every artifact + the DAG
    @step
    def end(self):
        print(f"done: {self.outcome}")


if __name__ == "__main__":
    TourFlow()
