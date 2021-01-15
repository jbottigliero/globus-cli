import json

import pytest
import responses

import globus_cli.services.transfer
from tests.constants import GO_EP1_ID


@pytest.fixture
def patch_sleep(monkeypatch):
    sleep_calls = []

    def mock_sleep(*args, **kwargs):
        sleep_calls.append((args, kwargs))

    monkeypatch.setattr(globus_cli.services.transfer.time, "sleep", mock_sleep)

    return sleep_calls


def _get_delete_call():
    # get the delete call, parse the body, and return both
    try:
        delete_call = next(
            r.request for r in responses.calls if r.request.url.endswith("/delete")
        )
    except StopIteration:
        return None, None
    sent_data = json.loads(delete_call.body)
    return delete_call, sent_data


def _load_probably_json_substring(x):
    """
    Weak method of extracting JSON object from a string which includes JSON and
    non-JSON data. Just gets the largest substring from { to }
    Works well for these cases, where click.CliRunner gives us output
    containing both stderr and stdout.
    """
    return json.loads(x[x.index("{") : x.rindex("}") + 1])


def test_recursive(run_line, load_api_fixtures):
    """
    Makes a dir on ep1, then --recursive rm's it.
    Confirms delete task was successful.
    """
    load_api_fixtures("transfer_activate_success.yaml")
    load_api_fixtures("get_submission_id.yaml")
    load_api_fixtures("submit_delete_success.yaml")

    result = run_line("globus rm -r -F json {}:/foo".format(GO_EP1_ID))
    res = _load_probably_json_substring(result.output)
    assert res["status"] == "SUCCEEDED"


def test_no_file(run_line, load_api_fixtures):
    """
    Attempts to remove a non-existent file. Confirms exit code 1
    """
    load_api_fixtures("transfer_activate_success.yaml")
    load_api_fixtures("get_submission_id.yaml")
    load_api_fixtures("submit_delete_failed.yaml")

    run_line("globus rm {}:/nosuchfile.txt".format(GO_EP1_ID), assert_exit_code=1)

    # confirm that we sent `ignore_missing=False`
    # makes sense in context with the ignore-missing test below
    _delete_call, sent_data = _get_delete_call()
    assert sent_data["ignore_missing"] is False


def test_ignore_missing(run_line, load_api_fixtures):
    """
    Attempts to remove a non-existant file path, with --ignore-missing.
    Confirms exit code 0 and silent output.
    """
    load_api_fixtures("transfer_activate_success.yaml")
    load_api_fixtures("get_submission_id.yaml")
    load_api_fixtures("submit_delete_success.yaml")

    path = "/~/nofilehere.txt"
    result = run_line("globus rm -f {}:{}".format(GO_EP1_ID, path))
    assert "Delete task submitted under ID " in result.stderr

    # confirm that we sent `ignore_missing=True`
    _delete_call, sent_data = _get_delete_call()
    assert sent_data["ignore_missing"] is True


def test_timeout(run_line, load_api_fixtures, patch_sleep):
    """
    If a task is retrying without success, `rm` should wait and eventually time out.
    """
    load_api_fixtures("transfer_activate_success.yaml")
    load_api_fixtures("get_submission_id.yaml")
    load_api_fixtures("submit_delete_queued.yaml")

    result = run_line(
        "globus rm -r --timeout 2 {}:/foo/bar.txt".format(GO_EP1_ID),
        assert_exit_code=1,
    )
    assert "Task has yet to complete after 2 seconds" in result.stderr


def test_timeout_explicit_status(run_line, load_api_fixtures, patch_sleep):
    """
    As above, submit a task which sits queued and times out.
    Confirms rm exits STATUS after given timeout, where
    STATUS is set via the --timeout-exit-code opt
    """
    load_api_fixtures("transfer_activate_success.yaml")
    load_api_fixtures("get_submission_id.yaml")
    load_api_fixtures("submit_delete_queued.yaml")

    status = 50
    result = run_line(
        "globus rm -r --timeout 1 --timeout-exit-code {} {}:/foo/bar.txt".format(
            status, GO_EP1_ID
        ),
        assert_exit_code=status,
    )
    assert "Task has yet to complete after 1 seconds" in result.stderr
