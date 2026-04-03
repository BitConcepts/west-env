"""End-to-end bootstrap test for the example workspace flow.

Runs inside Docker to avoid polluting the host.  Uses a trimmed manifest
that references only the west-env repo (no full Zephyr tree) so the test
finishes in reasonable time while still exercising the real bootstrap
script mechanics: venv creation, west init, west update, west-env
visibility, and ``west env doctor``.
"""

# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BASE_IMAGE = os.environ.get(
    "WEST_ENV_BOOTSTRAP_BASE_IMAGE",
    "python:3.12-slim",
)
BOOTSTRAP_IMAGE = os.environ.get(
    "WEST_ENV_BOOTSTRAP_IMAGE",
    "west-env-test-bootstrap:latest",
)


def docker_available():
    try:
        subprocess.check_output(
            ["docker", "--version"],
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:  # noqa
        return False


def ensure_bootstrap_image():
    if os.environ.get("WEST_ENV_BOOTSTRAP_IMAGE"):
        return

    with tempfile.TemporaryDirectory(prefix="west-env-bootstrap-img-") as tmp:
        dockerfile = Path(tmp) / "Dockerfile"
        dockerfile.write_text(
            textwrap.dedent(
                f"""\
                FROM {BASE_IMAGE}
                RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
                RUN python -m pip install --no-cache-dir west PyYAML
                ENTRYPOINT []
                CMD ["bash"]
                """
            ),
            encoding="utf-8",
        )
        subprocess.check_call(
            ["docker", "build", "-t", BOOTSTRAP_IMAGE, tmp],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


@unittest.skipUnless(docker_available(), "Docker is required for bootstrap e2e test")
class BootstrapE2ETests(unittest.TestCase):
    """Validate the example workspace bootstrap flow inside Docker."""

    @classmethod
    def setUpClass(cls):
        ensure_bootstrap_image()

    def test_bootstrap_and_doctor_with_lightweight_manifest(self):
        """Copy example workspace, replace manifest with a minimal one,
        run the bootstrap steps, then verify ``west env doctor``."""

        # The script we run inside Docker:
        #   1. Copy the example workspace files from /repo/example/workspace
        #   2. Replace west.yml with a lightweight manifest pointing at the
        #      mounted repo so ``west update`` is a local clone (~instant)
        #   3. Stub out zephyr/scripts/requirements.txt so the bootstrap
        #      pip-install step succeeds
        #   4. Run the bootstrap steps manually (we can't use bootstrap.sh
        #      directly because it checks for pyproject.toml at the workspace
        #      root which would fail since we _do_ have it in /repo but not
        #      in /ws)
        #   5. Run ``west env doctor`` in native mode

        inner_script = textwrap.dedent(
            r"""
            set -eu

            # --- git safe.directory for mounted repo ---
            git config --global --add safe.directory /repo

            # --- setup workspace ---
            mkdir -p /ws/scripts
            cp /repo/example/workspace/west-env.yml /ws/
            cp /repo/example/workspace/scripts/*.sh /ws/scripts/ || true

            # --- lightweight manifest ---
            cat > /ws/west.yml <<'MANIFEST'
            manifest:
              self:
                path: .

              projects:
                - name: west-env
                  path: modules/west-env
                  url: /repo
                  revision: HEAD
                  west-commands: west-commands.yml
            MANIFEST

            # --- native mode for doctor ---
            cat > /ws/west-env.yml <<'ENVYML'
            env:
              type: native
            ENVYML

            cd /ws

            # --- venv + west ---
            python -m venv .venv
            . .venv/bin/activate
            pip install --quiet --upgrade pip
            pip install --quiet west PyYAML

            # --- west init + update ---
            west init -l .
            west update

            # --- stub zephyr requirements so bootstrap-like flow works ---
            mkdir -p /ws/zephyr/scripts
            touch /ws/zephyr/scripts/requirements.txt

            # --- validate ---
            echo "=== west list ==="
            west list

            echo "=== west env doctor ==="
            west env doctor
            """
        )

        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{REPO_ROOT}:/repo:ro",
                BOOTSTRAP_IMAGE,
                "bash",
                "-c",
                inner_script,
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Print output for debugging on failure
        if result.returncode != 0:
            print("STDOUT:", result.stdout[-2000:])
            print("STDERR:", result.stderr[-2000:])

        self.assertEqual(result.returncode, 0, f"Bootstrap failed:\n{result.stderr[-1000:]}")
        self.assertIn("west-env", result.stdout)
        self.assertIn("Environment looks good", result.stdout)


if __name__ == "__main__":
    unittest.main()
