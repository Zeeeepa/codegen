"""Largely copied from swebench/harness/modal_eval/run_evaluation_modal.py

Points of difference:
 - We added CGModalSandboxRuntime class that is used to populate the sandbox with the snapshot.
 - We are adding custom post-processing of the TestOutput in run_instances_modal
"""

import io
import json
import time
import traceback
from collections import defaultdict
from contextlib import nullcontext
from importlib.metadata import version
from unittest.mock import patch

import modal as modal_lib
from swebench.harness.constants import (
    APPLY_PATCH_FAIL,
    APPLY_PATCH_PASS,
    SWEbenchInstance,
)
from swebench.harness.docker_build import setup_logger
from swebench.harness.grading import get_eval_report
from swebench.harness.modal_eval.run_evaluation_modal import (
    LOCAL_SANDBOX_ENTRYPOINT_PATH,
    REMOTE_SANDBOX_ENTRYPOINT_PATH,
    ModalSandboxRuntime,
    TestOutput,
    get_log_dir,
    swebench_image,
)
from swebench.harness.run_evaluation import main
from swebench.harness.test_spec.test_spec import TestSpec, make_test_spec
from swebench.harness.utils import EvaluationError


class SnapshotManager:
    def get_snapshot_uid(self, example: SWEbenchInstance) -> str:
        msg = "Not implemented"
        raise NotImplementedError(msg)

    def save_snapshot_uid(self, example: SWEbenchInstance, snapshot_uid: str) -> None:
        msg = "Not implemented"
        raise NotImplementedError(msg)


class VolumeSnapshotManager(SnapshotManager):
    def __init__(self, volume_name: str = "swebench-agent-snapshot-volume"):
        self.snapshot_volume = modal_lib.Volume.from_name(volume_name, create_if_missing=True)
        self.snapshot_meta_file_path: str = "/root/snapshot_meta.json"

    def get_snapshot_uid(self, example: SWEbenchInstance) -> str:
        snapshot_meta = self.read_snapshot_meta()
        return snapshot_meta[example.repo][example.environment_setup_commit]

    def save_snapshot_uid(self, example: SWEbenchInstance, snapshot_uid: str) -> None:
        snapshot_meta = self.read_snapshot_meta()
        snapshot_meta[example.repo][example.environment_setup_commit] = snapshot_uid
        with self.snapshot_volume.batch_upload() as upload:
            upload.put_file(
                io.BytesIO(json.dumps(snapshot_meta).encode("utf-8")),
                self.snapshot_meta_file_path,
            )
        self.snapshot_volume.commit()

    def read_snapshot_meta(self) -> dict[str, dict[str, str]]:
        bytes_io = io.BytesIO()
        try:
            self.snapshot_volume.read_file_into_fileobj(self.snapshot_meta_file_path, bytes_io)
            snapshot_meta = json.loads(bytes_io.getvalue().decode("utf-8"))
        except FileNotFoundError:
            snapshot_meta = {}
        return defaultdict(lambda: defaultdict(lambda: None), snapshot_meta)


class ModalDictSnapshotManager(SnapshotManager):
    def __init__(self, name: str = "swebench-agent-snapshot-dict"):
        self.snapshot_dict = modal_lib.Dict.from_name(name, create_if_missing=True)

    def get_snapshot_uid(self, example: SWEbenchInstance) -> str | None:
        try:
            return self.snapshot_dict[(example.repo, example.environment_setup_commit)]
        except KeyError:
            return None

    def save_snapshot_uid(self, example: SWEbenchInstance, snapshot_uid: str) -> None:
        self.snapshot_dict[(example.repo, example.environment_setup_commit)] = snapshot_uid


class CGModalSandboxRuntime(ModalSandboxRuntime):
    def __init__(
        self,
        example: SWEbenchInstance,
        timeout: int | None = None,
        verbose: bool = True,
    ):
        self.example = example
        self.snapshot_manager = ModalDictSnapshotManager()
        self.test_spec = make_test_spec(example)
        self.sandbox = self._get_sandbox(timeout)
        self.verbose = verbose
        self._stream_tasks = []

        # Hack for pylint
        self.write_file("/sys/fs/cgroup/cpu/cpu.shares", "2048")

    @property
    def image(self) -> modal_lib.Image:
        return ModalSandboxRuntime.get_instance_image(self.test_spec)

    def _get_sandbox(self, timeout: int | None = None):
        """Populate sandbox ourselves"""
        uid = self.snapshot_manager.get_snapshot_uid(self.example)
        if uid is None:
            sandbox = super()._get_sandbox(timeout)
            snapshot = sandbox._experimental_snapshot()
            self.snapshot_manager.save_snapshot_uid(self.example, snapshot.object_id)
        else:
            return modal_lib.Sandbox._experimental_from_snapshot(uid)


app = modal_lib.App.lookup("swebench-agent-run", create_if_missing=True)


@app.function(
    image=swebench_image.add_local_file(
        LOCAL_SANDBOX_ENTRYPOINT_PATH,
        REMOTE_SANDBOX_ENTRYPOINT_PATH,
    ).add_local_python_source("modal_harness"),
    timeout=120 * 60,  # Much larger than default timeout to account for image build time
)
def run_instance_modal(
    test_spec: TestSpec,
    pred: dict,
    run_id: str,
    timeout: int | None = None,
) -> TestOutput:
    """Run a single instance with the given prediction.

    Args:
        test_spec (TestSpec): TestSpec instance
        pred (dict): Prediction w/ model_name_or_path, model_patch, instance_id
        run_id (str): Run ID
        timeout (int): Timeout for running tests
    """
    instance_id = test_spec.instance_id
    log_dir = get_log_dir(pred, run_id, instance_id)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "run_instance.log"

    logger = setup_logger(instance_id, log_file, add_stdout=True)

    try:
        runner = ModalSandboxRuntime(test_spec, timeout)
    except Exception as e:
        print(f"Error creating sandbox: {e}")
        raise EvaluationError(
            instance_id,
            f"Error creating sandbox: {e}",
            logger,
        ) from e

    patch_diff = pred.get("model_patch", "")

    try:
        patch_file = "/tmp/patch.diff"
        runner.write_file(patch_file, patch_diff)

        apply_patch_output, returncode = runner.exec(
            "cd /testbed && git apply -v /tmp/patch.diff",
        )

        if returncode != 0:
            logger.info("Failed to apply patch to container, trying again...")

            apply_patch_output, returncode = runner.exec(
                "cd /testbed && patch --batch --fuzz=5 -p1 -i /tmp/patch.diff",
            )

            if returncode != 0:
                logger.info(f"{APPLY_PATCH_FAIL}:\n{apply_patch_output}")
                raise EvaluationError(
                    instance_id,
                    f"{APPLY_PATCH_FAIL}:\n{apply_patch_output}",
                    logger,
                )
            else:
                logger.info(f"{APPLY_PATCH_PASS}:\n{apply_patch_output}")
        else:
            logger.info(f"{APPLY_PATCH_PASS}:\n{apply_patch_output}")

        # Get git diff before running eval script
        git_diff_output_before, returncode = runner.exec(
            "cd /testbed && git diff",
        )
        logger.info(f"Git diff before:\n{git_diff_output_before}")

        eval_file = "/root/eval.sh"
        eval_script = test_spec.eval_script
        # django hack
        eval_script = eval_script.replace("locale-gen", "locale-gen en_US.UTF-8")
        runner.write_file(eval_file, eval_script)

        start_time = time.time()

        run_command = "cd /testbed"
        # pylint hack
        if "pylint" in test_spec.instance_id:
            run_command += " && PYTHONPATH="
        # increase recursion limit for testing
        run_command += " && python3 -c 'import sys; sys.setrecursionlimit(10000)'"
        # run eval script
        run_command += " && /bin/bash /root/eval.sh"
        test_output, returncode = runner.exec(run_command)

        total_runtime = time.time() - start_time

        test_output_path = log_dir / "test_output.txt"
        logger.info(f"Test runtime: {total_runtime:_.2f} seconds")
        with open(test_output_path, "w") as f:
            f.write(test_output)
            logger.info(f"Test output for {instance_id} written to {test_output_path}")
            print(f"Test output for {instance_id} written to {test_output_path}")

        # Get git diff after running eval script
        git_diff_output_after, returncode = runner.exec("cd /testbed && git diff")

        # Check if git diff changed after running eval script
        logger.info(f"Git diff after:\n{git_diff_output_after}")
        if git_diff_output_after != git_diff_output_before:
            logger.info("Git diff changed after running eval script")

        # Get report from test output
        logger.info(f"Grading answer for {instance_id}...")
        report = get_eval_report(
            test_spec=test_spec,
            prediction=pred,
            test_log_path=test_output_path,
            include_tests_status=True,
        )
        logger.info(f"report: {report}\nResult for {instance_id}: resolved: {report[instance_id]['resolved']}")

        return TestOutput(
            instance_id=instance_id,
            test_output=test_output,
            report_json_str=json.dumps(report, indent=4),
            run_instance_log=log_file.read_text(),
            patch_diff=patch_diff,
            log_dir=log_dir,
            errored=False,
        )
    except modal_lib.exception.SandboxTimeoutError as e:
        raise EvaluationError(
            instance_id,
            f"Test timed out after {timeout} seconds.",
            logger,
        ) from e
    except EvaluationError:
        error_msg = traceback.format_exc()
        logger.info(error_msg)
        return TestOutput(
            instance_id=instance_id,
            test_output="",
            report_json_str="",
            run_instance_log=log_file.read_text(),
            patch_diff=patch_diff,
            log_dir=log_dir,
            errored=True,
        )
    except Exception as e:
        error_msg = f"Error in evaluating model for {instance_id}: {e}\n{traceback.format_exc()}\nCheck ({logger.log_file}) for more information."
        logger.exception(error_msg)
        return TestOutput(
            instance_id=instance_id,
            test_output="",
            report_json_str="",
            run_instance_log=log_file.read_text(),
            patch_diff=patch_diff,
            log_dir=log_dir,
            errored=True,
        )


def patched_swebench_eval(  # Defaults from swebench harness
    predictions_path,  # Required argument
    run_id,  # Required argument
    dataset_name="princeton-nlp/SWE-bench_Lite",
    split="test",
    instance_ids=None,  # Default None since it's optional
    max_workers=4,
    open_file_limit=4096,
    timeout=1800,
    force_rebuild=False,
    cache_level="env",
    clean=False,
    namespace="swebench",
    instance_image_tag="latest",
    rewrite_reports=False,
    report_dir=".",
    modal=False,
    **kwargs,
):
    with (
        patch(
            "swebench.harness.modal_eval.run_evaluation_modal.run_instance_modal",
            modal_lib.Function.from_name(
                app_name="swebench-agent-run",
                name="run_instance_modal",
            ),
        ),
        patch(
            "swebench.harness.modal_eval.run_evaluation_modal.app",
            app,
        ),
    ):
        # Don't want swebench to run app.run() again
        app.run = nullcontext
        return main(
            dataset_name=dataset_name,
            split=split,
            instance_ids=instance_ids,
            predictions_path=predictions_path,
            max_workers=max_workers,
            force_rebuild=force_rebuild,
            cache_level=cache_level,
            clean=clean,
            open_file_limit=open_file_limit,
            run_id=run_id,
            timeout=timeout,
            namespace=namespace,
            rewrite_reports=rewrite_reports,
            modal=modal,
            instance_image_tag=instance_image_tag,
            report_dir=report_dir,
            **kwargs,
        )


# def run_instances_modal(
#     predictions: dict,
#     instances: list,
#     full_dataset: list,
#     run_id: str,
#     timeout: int,
# ):
#     """Run all instances for the given predictions on Modal.

#     Args:
#         predictions (dict): Predictions dict generated by the model
#         instances (list): List of instances
#         run_id (str): Run ID
#         timeout (int): Timeout for running tests
#     """
#     test_specs = list(map(make_test_spec, instances))

#     with modal.enable_output():
#         with app.run():
#             run_test_specs = []

#             # Check for instances that have already been run
#             for test_spec in test_specs:
#                 log_dir = get_log_dir(
#                     predictions[test_spec.instance_id], run_id, test_spec.instance_id
#                 )
#                 if log_dir.exists():
#                     continue
#                 run_test_specs.append(test_spec)

#             if run_test_specs:
#                 # Run instances that haven't been run yet
#                 results = run_instance_modal.starmap(
#                     [
#                         (
#                             test_spec,
#                             predictions[test_spec.instance_id],
#                             run_id,
#                             timeout,
#                         )
#                         for test_spec in run_test_specs
#                     ],
#                 )

#                 for result in results:
#                     result = cast(TestOutput, result)

#                     # Save logs locally
#                     log_dir = result.log_dir
#                     log_dir.mkdir(parents=True, exist_ok=True)
#                     with open(log_dir / "run_instance.log", "w") as f:
#                         f.write(result.run_instance_log)
#                     with open(log_dir / "test_output.txt", "w") as f:
#                         f.write(result.test_output)
#                     with open(log_dir / "patch.diff", "w") as f:
#                         f.write(result.patch_diff)
#                     with open(log_dir / "report.json", "w") as f:
#                         try:
#                             report_json = json.loads(result.report_json_str)
#                             json.dump(report_json, f, indent=4)
#                         except Exception:
#                             # This happens if the test fails with any exception
#                             print(f"{result.instance_id}: no report.json")

#             make_run_report(predictions, full_dataset, run_id)


def write_report_to_db(report_file: str):
    import psycopg2

    try:
        codegen_version = version("codegen")
    except Exception:
        codegen_version = "dev"

    with open(report_file) as f:
        report = json.load(f)

    # Establish connection
    conn = psycopg2.connect(host="localhost", database="swebench", user="swebench", password="swebench")

    # Create a cursor
    cur = conn.cursor()

    try:
        # Single row insert
        cur.execute(
            "INSERT INTO table_name (codegen_version, submitted, completed_instances, resolved_instances, unresolved_instances, empty_patches, error_instances) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                codegen_version,
                report["submitted_instances"],
                report["completed_instances"],
                report["resolved_instances"],
                report["unresolved_instances"],
                report["empty_patch_instances"],
                report["error_instances"],
            ),
        )

        # Commit the transaction
        conn.commit()

    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Error: {e}")

    finally:
        # Close cursor and connection
        cur.close()
        conn.close()
