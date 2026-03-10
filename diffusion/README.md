# pi0 eval example

## Installation

1. Run all instructions from `robot-inference-api/examples/pi0`
```bash
cd examples/pi0
```
2. Install uv:
```bash
curl -LsSf https://github.com/astral-sh/uv/releases/download/0.7.5/uv-installer.sh | sh
```
3. Sync the environment:
```bash
GIT_LFS_SKIP_SMUDGE=1 uv sync
```

## Robot inference
Run the eval script with the robot config:
```bash
uv run -m robot_inference.client.run_model --config pi0_robot.yaml
```

## Droid sim evals
Run the eval script with the sim config:
```bash
uv run --no-default-groups --group droidsim -m robot_inference.client.run_model --config pi0_droidsim.yaml
```
or alternatively:
```bash
uv sync --no-default-groups --group droidsim
source .venv/bin/activate
python3 -m robot_inference.client.run_model --config pi0_droidsim.yaml
```

## Droid sim policy server
Run the `serve.py` script with the server config:

```bash
uv run --no-default-groups --group droidsim -m robot_inference.policy_server.serve --config pi0_server.yaml
```
or alternatively:
```bash
uv sync --no-default-groups --group droidsim
source .venv/bin/activate
python3 -m robot_inference.policy_server.serve_policy --config pi0_server.yaml
```
