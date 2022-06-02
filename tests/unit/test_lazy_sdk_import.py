"""
        ***************
        * PLEASE READ *
        ***************

If these tests fail, it probably means you broke a delicate but important feature of the
CLI. Read this full docstring before changing these tests.


It's important to test the behavior of importing the globus_cli command tree to ensure
that it does not import the main globus_sdk components.

This is a performance enhancement which avoids paying the cost for expensive import-time
logic done in globus_sdk, requests, and urllib3 when the CLI is running a command like
  globus ls --help
or tab completion.

It is *very* easy to accidentally undo this performance improvement. For example, a new
module with an innocuous annotation:

    import globus_sdk

    def foo(client: globus_sdk.TransferClient) -> None: pass

The annotation should be deferred (default behavior on py3.10+) but because it isn't
quoted or guarded with `from __future__ import annotations`, it will evaluate at
runtime.

Because the overhead of `import requests` alone (let alone all of the SDK imports) is
about 100ms, it eats a significant chunk of our time budget for completions and other
very latency-sensitive usages. We need to ensure that doesn't get done when the CLI does
its (almost entirely eager) imports.
"""
import subprocess
import sys

import globus_sdk
import pytest


@pytest.mark.skipif(
    not hasattr(globus_sdk, "_force_eager_imports"),
    reason="globus_sdk lazy imports not supported on this version",
)
@pytest.mark.skipif(sys.version_info < (3, 7), reason="lazy imports require py3.7+")
def test_importing_cli_doesnt_import_requests():
    to_run = "; ".join(
        [
            "import sys",
            "from globus_cli import main",
            "assert 'requests' not in sys.modules",
        ]
    )
    proc = subprocess.Popen(
        f'{sys.executable} -c "{to_run}"',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    status = proc.wait()
    assert status == 0, str(proc.communicate())
    proc.stdout.close()
    proc.stderr.close()
