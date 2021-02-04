import json
import re

import pytest
import responses


def test_gcp_creation(run_line, load_api_fixtures):
    """
    Runs endpoint create with --personal
    Confirms personal endpoint is created successfully
    """
    load_api_fixtures("gcp_create.yaml")
    result = run_line("globus endpoint create --personal personal_create -F json")
    res = json.loads(result.output)
    assert res["DATA_TYPE"] == "endpoint_create_result"
    assert res["code"] == "Created"
    assert "id" in res


def test_shared_creation(run_line, load_api_fixtures, go_ep1_id):
    """
    Runs endpoint create with --shared and a host path
    Confirms shared endpoint is created successfully
    """
    load_api_fixtures("transfer_activate_success.yaml")
    load_api_fixtures("endpoint_operations.yaml")
    result = run_line(
        "globus endpoint create share_create "
        "-F json --shared {}:/~/".format(go_ep1_id)
    )
    res = json.loads(result.output)
    assert res["DATA_TYPE"] == "endpoint_create_result"
    assert res["code"] == "Created"
    assert "Shared endpoint" in res["message"]
    assert "id" in res


def test_gcs_creation(run_line, load_api_fixtures):
    """
    Runs endpoint create with --server
    Confirms endpoint is created successfully
    """
    load_api_fixtures("endpoint_operations.yaml")
    result = run_line("globus endpoint create gcs_create --server -F json")
    res = json.loads(result.output)
    assert res["DATA_TYPE"] == "endpoint_create_result"
    assert res["code"] == "Created"
    assert res["globus_connect_setup_key"] is None
    assert "id" in res


@pytest.mark.parametrize("ep_type", ["personal", "server"])
def test_text_ouptut(run_line, load_api_fixtures, ep_type):
    """
    Creates GCP and GCS endpoint
    Confirms (non)presence of setup key in text output
    """
    if ep_type == "personal":
        opt = "--personal"
        data = load_api_fixtures("gcp_create.yaml")
        ep_id = data["metadata"]["endpoint_id"]
        setup_key = data["metadata"]["setup_key"]
    else:
        opt = "--server"
        data = load_api_fixtures("endpoint_operations.yaml")
        ep_id = data["metadata"]["endpoint_id"]
        setup_key = None

    result = run_line(f"globus endpoint create gcp_text {opt}")
    got_ep_id = re.search(r"Endpoint ID:\s*(\S*)", result.output).group(1)
    assert got_ep_id == ep_id

    if ep_type == "personal":
        got_setup_key = re.search(r"Setup Key:\s*(\S*)", result.output).group(1)
        assert got_setup_key == setup_key
    else:
        assert "Setup Key:" not in result.output


@pytest.mark.parametrize(
    "ep_type,type_opts",
    [
        ("personal", ("--personal",)),
        ("share", ("--shared", "{GO_EP1_ID}:/~/")),
        ("server", ("--server",)),
    ],
)
def test_general_options(run_line, load_api_fixtures, ep_type, type_opts, go_ep1_id):
    """
    Creates a shared, personal, and server endpoints using options
    available for all endpoint types. Confirms expected values through SDK
    """
    if ep_type == "personal":
        load_api_fixtures("gcp_create.yaml")
    else:
        load_api_fixtures("endpoint_operations.yaml")
    if ep_type == "share":
        load_api_fixtures("transfer_activate_success.yaml")

    # options with option value and expected value
    # if expected value is not set, it will be copied from the option value
    option_dicts = [
        {"opt": "--description", "key": "description", "val": "sometext"},
        {"opt": "--default-directory", "key": "default_directory", "val": "/share/"},
        {"opt": "--organization", "key": "organization", "val": "someorg"},
        {"opt": "--department", "key": "department", "val": "somedept"},
        {"opt": "--keywords", "key": "keywords", "val": "some,key,words"},
        {"opt": "--contact-email", "key": "contact_email", "val": "a@b.c"},
        {"opt": "--contact-info", "key": "contact_info", "val": "info"},
        {"opt": "--info-link", "key": "info_link", "val": "http://a.b"},
        {
            "opt": "--force-encryption",
            "key": "force_encryption",
            "val": None,
            "expected": True,
        },
        {
            "opt": "--disable-verify",
            "key": "disable_verify",
            "val": None,
            "expected": True,
        },
    ]
    if ep_type == "server":
        option_dicts.extend(
            [
                {"opt": "--myproxy-dn", "key": "myproxy_dn", "val": "/dn"},
                {
                    "opt": "--myproxy-server",
                    "key": "myproxy_server",
                    "val": "srv.example.com",
                },
                {"opt": "--private", "key": "public", "val": "", "expected": False},
                {
                    "opt": "--location",
                    "key": "location",
                    "val": "1.1,2",
                    "expected": "1.1,2",
                },
            ]
        )
    for x in option_dicts:
        if "expected" not in x:
            x["expected"] = x["val"]

    # make and run the line, get and track the id for cleanup
    line = ["globus", "endpoint", "create", "myendpoint", "-F", "json"] + [
        x.format(GO_EP1_ID=go_ep1_id) for x in type_opts
    ]
    for item in option_dicts:
        line.append(item["opt"])
        if item["val"]:
            line.append(item["val"])
    run_line(" ".join(line))

    # get and confirm values which were sent as JSON
    sent_data = json.loads(responses.calls[-1].request.body)
    for item in option_dicts:
        assert item["expected"] == sent_data[item["key"]]


@pytest.mark.parametrize(
    "ep_type,type_opts",
    [
        ("personal", ("--personal",)),
        ("share", ("--shared", "{GO_EP1_ID}:/~/")),
    ],
)
def test_invalid_gcs_only_options(run_line, ep_type, type_opts, go_ep1_id):
    """
    For all GCS only options, tries to create a GCP and shared endpoint
    Confirms invalid options are caught at the CLI level rather than API
    """
    options = [
        "--public",
        "--private",
        "--myproxy-dn /dn",
        "--myproxy-server mpsrv.example.com",
        "--oauth-server oasrv.example.com",
        "--location 1,1",
    ]
    for opt in options:
        result = run_line(
            "globus endpoint create invalid_gcs {} {} ".format(
                " ".join(x.format(GO_EP1_ID=go_ep1_id) for x in type_opts), opt
            ),
            assert_exit_code=2,
        )
        assert "Globus Connect Server" in result.stderr


def test_invalid_managed_only_options(run_line):
    """
    For all managed only options, tries to create a GCS endpoint
    Confirms invalid options are caught at the CLI level rather than AP
    """
    options = [
        "--network-use custom",
        "--max-concurrency 2",
        "--preferred-concurrency 1",
        "--max-parallelism 2",
        "--preferred-parallelism 1",
    ]
    for opt in options:
        result = run_line(
            f"globus endpoint create invalid_managed --server {opt}",
            assert_exit_code=2,
        )
        assert "managed endpoints" in result.stderr


def test_mutex_options(run_line):
    options = [
        "--default-directory /foo/ --no-default-directory",
        "--subscription-id aa3ccabf-d0dc-4ea8-b6aa-6c9b4ae9b0d3 --no-managed",
    ]
    for opts in options:
        result = run_line(
            f"globus endpoint create withbadopts --server {opts}",
            assert_exit_code=2,
        )
        assert "mutually exclusive" in result.stderr
