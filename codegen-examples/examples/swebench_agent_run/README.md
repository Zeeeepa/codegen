# INSTRUCTIONS

1. Create a `.env` file in the root directory and add your API keys.

1. cd into the `codegen-examples/examples/swebench_agent_run` directory

1. Create a `.venv` with `uv venv` and activate it with `source .venv/bin/activate`

1. Install the codegen dependencies with `uv add codegen`

- Note: If you'd like to install the dependencies in the global environment, you can use `uv pip install -e ../../../`. This will allow you to test modifications to the codegen codebase. You will need to run `uv pip install -e ../../../` each time you make changes to the codebase.

5. Ensure that you have a modal account and profile set up. If you don't have one, you can create one at https://modal.com/

1. Activate the appropriate modal profile `uv modal profile activate <profile_name>`

1. Launch the modal app with `uv run modal deploy --env=<env_name> entry_point.py`

1. Run the evaluation with `python run_eval.py` with the desired options:

- ```bash
  $ python run_eval.py --help
  Usage: run_eval.py [OPTIONS]

  Options:
  --use-existing-preds            Use existing predictions instead of
                                generating new ones.
  --dataset [princeton-nlp/SWE-bench_Lite|princeton-nlp/SWE-bench|princeton-nlp/SWE-bench-verified]
                                The dataset to use.
  --length INTEGER                The number of examples to process.
  --instance-id TEXT              The instance ID of the example to process.
  --help                          Show this message and exit.
  ```
