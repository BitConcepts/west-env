"""Host-side nested Podman integration test using Docker."""

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

OUTER_BASE_IMAGE = os.environ.get(
    "WEST_ENV_PODMAN_NESTED_BASE_IMAGE",
    "quay.io/podman/stable:latest",
)
OUTER_TEST_IMAGE = os.environ.get(
    "WEST_ENV_PODMAN_NESTED_IMAGE",
    "west-env-test-podman-nested:latest",
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


def ensure_outer_test_image():
    if os.environ.get("WEST_ENV_PODMAN_NESTED_IMAGE"):
        return

    with tempfile.TemporaryDirectory(prefix="west-env-podman-outer-image-") as tmp:
        dockerfile = Path(tmp) / "Dockerfile"
        dockerfile.write_text(
            textwrap.dedent(
                f"""\
                FROM {OUTER_BASE_IMAGE}
                RUN dnf -y install python3 python3-pip git && dnf clean all
                RUN python3 -m pip install --no-cache-dir west PyYAML
                ENTRYPOINT []
                CMD ["sh"]
                """
            ),
            encoding="utf-8",
        )
        subprocess.check_call(
            ["docker", "build", "-t", OUTER_TEST_IMAGE, tmp],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


@unittest.skipUnless(docker_available(), "Docker is required for nested Podman test")
class NestedPodmanInDockerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_outer_test_image()

    def test_real_podman_runtime_path_inside_docker(self):
        with tempfile.TemporaryDirectory(prefix="west-env-podman-smoke-files-") as tmp:
            tmpdir = Path(tmp)
            (tmpdir / "Dockerfile").write_text(
                textwrap.dedent(
                    """\
                    FROM docker.io/library/alpine:latest
                    RUN apk add --no-cache git
                    ENTRYPOINT []
                    CMD ["sh"]
                    """
                ),
                encoding="utf-8",
            )
            (tmpdir / "run_podman_smoke.py").write_text(
                textwrap.dedent(
                    """\
                    import os
                    import sys
                    import tempfile
                    from pathlib import Path

                    sys.path.insert(0, '/repo')

                    from west_env.config import EnvConfig
                    import west_env.container as container

                    root = Path(tempfile.mkdtemp(prefix='west-env-podman-real-'))
                    (root / '.west').mkdir()
                    (root / '.west' / 'config').write_text(
                        '[manifest]\\npath = .\\nfile = west.yml\\n',
                        encoding='utf-8',
                    )
                    (root / 'west.yml').write_text(
                        'manifest:\\n  self:\\n    path: .\\n',
                        encoding='utf-8',
                    )
                    (root / 'app').mkdir()

                    container._west_topdir = lambda: str(root)
                    os.chdir(root / 'app')

                    cfg = EnvConfig(
                        {
                            'env': {
                                'type': 'container',
                                'container': {
                                    'engine': 'podman',
                                    'image': 'inner-git-shell:latest',
                                },
                            }
                        }
                    )

                    container.run_container(
                        cfg,
                        [
                            'sh',
                            '-c',
                            'pwd > podman-real.txt && test -d ../.west && test -f ../west.yml',
                        ],
                    )
                    print((root / 'app' / 'podman-real.txt').read_text(encoding='utf-8').strip())
                    """
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--privileged",
                    "-v",
                    f"{REPO_ROOT}:/repo",
                    "-v",
                    f"{tmpdir}:/hosttmp",
                    OUTER_TEST_IMAGE,
                    "sh",
                    "-lc",
                    "podman build -t inner-git-shell:latest -f /hosttmp/Dockerfile /hosttmp >/dev/null && python3 /hosttmp/run_podman_smoke.py",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertEqual(result.stdout.strip().splitlines()[-1], "/work/app")


if __name__ == "__main__":
    unittest.main()
