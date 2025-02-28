"""
Largely copied from swebench/harness/modal_eval/run_evaluation_modal.py

Points of difference:
 - We added CGModalSandboxRuntime class that is used to populate the sandbox with the snapshot.
 - We are adding custom post-processing of the TestOutput in run_instances_modal
"""

import json
import time
import traceback
from typing import cast

import modal
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
)
from swebench.harness.test_spec.test_spec import TestSpec, make_test_spec
from swebench.harness.utils import EvaluationError

from .snapshot_manager import ModalDictSnapshotManager

app = modal.App.from_name("swebench-agent-run", create_if_missing=True)


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
    def image(self) -> modal.Image:
        return ModalSandboxRuntime.get_instance_image(self.test_spec)

    def _get_sandbox(self, timeout: int | None = None):
        """
        Populate sandbox ourselves
        """
        uid = self.snapshot_manager.get_snapshot_uid(self.example)
        if uid is None:
            sandbox = super()._get_sandbox(timeout)
            snapshot = sandbox._experimental_snapshot()
            self.snapshot_manager.save_snapshot_uid(self.example, snapshot.object_id)
        else:
            return modal.Sandbox._experimental_from_snapshot(uid)


@app.function(
    image=modal.Image.debian_slim(python_version="3.13").add_local_file(
        LOCAL_SANDBOX_ENTRYPOINT_PATH,
        REMOTE_SANDBOX_ENTRYPOINT_PATH,
    ),
    timeout=120 * 60,  # Much larger than default timeout to account for image build time
)
def run_instance_modal(
    test_spec: TestSpec,
    pred: dict,
    run_id: str,
    timeout: int | None = None,
) -> TestOutput:
    """
    Run a single instance with the given prediction.

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
        runner = CGModalSandboxRuntime(test_spec, timeout)
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
    except modal.exception.SandboxTimeoutError as e:
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
        logger.error(error_msg)
        return TestOutput(
            instance_id=instance_id,
            test_output="",
            report_json_str="",
            run_instance_log=log_file.read_text(),
            patch_diff=patch_diff,
            log_dir=log_dir,
            errored=True,
        )


def run_instances_modal(
    predictions: dict,
    instances: list,
    full_dataset: list,
    run_id: str,
    timeout: int,
):
    """
    Run all instances for the given predictions on Modal.

    Args:
        predictions (dict): Predictions dict generated by the model
        instances (list): List of instances
        run_id (str): Run ID
        timeout (int): Timeout for running tests
    """
    test_specs = list(map(make_test_spec, instances))

    with modal.enable_output():
        with app.run():
            run_test_specs = []

            # Check for instances that have already been run
            for test_spec in test_specs:
                log_dir = get_log_dir(predictions[test_spec.instance_id], run_id, test_spec.instance_id)
                if log_dir.exists():
                    continue
                run_test_specs.append(test_spec)

            if run_test_specs:
                # Run instances that haven't been run yet
                results = run_instance_modal.starmap(
                    [
                        (
                            test_spec,
                            predictions[test_spec.instance_id],
                            run_id,
                            timeout,
                        )
                        for test_spec in run_test_specs
                    ],
                )

                for result in results:
                    result = cast(TestOutput, result)

                    # log_dir = result.log_dir
                    # log_dir.mkdir(parents=True, exist_ok=True)
                    # with open(log_dir / "run_instance.log", "w") as f:
                    #     f.write(result.run_instance_log)
                    # with open(log_dir / "test_output.txt", "w") as f:
                    #     f.write(result.test_output)
                    # with open(log_dir / "patch.diff", "w") as f:
                    #     f.write(result.patch_diff)
                    # with open(log_dir / "report.json", "w") as f:
                    #     try:
                    #         report_json = json.loads(result.report_json_str)
                    #         json.dump(report_json, f, indent=4)
                    #     except Exception:
                    #         # This happens if the test fails with any exception
                    #         print(f"{result.instance_id}: no report.json")

                    # TODO: DO SOMETHING WITH OUTPUTS AND LOGS.
                    # TODO: SAVE THINGS TO POSTGRESQL FOR DASHBOARD
