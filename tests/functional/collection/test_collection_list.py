import pytest
import responses


def test_collection_list(run_line, load_api_fixtures, add_gcs_login):
    data = load_api_fixtures("collection_operations.yaml")
    epid = data["metadata"]["endpoint_id"]
    add_gcs_login(epid)
    result = run_line(f"globus collection list {epid}")
    collection_names = ["Happy Fun Collection Name 1", "Happy Fun Collection Name 2"]
    for name in collection_names:
        assert name in result.stdout


def test_collection_list_opts(run_line, load_api_fixtures, add_gcs_login):
    data = load_api_fixtures("collection_operations.yaml")
    epid = data["metadata"]["endpoint_id"]
    add_gcs_login(epid)
    cid = data["metadata"]["mapped_collection_id"]
    run_line(f"globus collection list --mapped-collection-id {cid} {epid}")
    assert responses.calls[-1].request.params["mapped_collection_id"] == cid
    run_line(f"globus collection list --include-private-policies {epid}")
    assert responses.calls[-1].request.params["include"] == "private_policies"


@pytest.mark.parametrize(
    "filter_val",
    [
        "mapped_collections",
        "mapped-collections",
        "MaPpeD-cOLlectiOns",
        "guest-collections",
        "guest_Collections",
        ["Mapped-Collections", "Managed_by-me"],
        ["mapped-collections", "managed-by_me", "created-by-me"],
    ],
)
def test_collection_list_filters(
    run_line, load_api_fixtures, add_gcs_login, filter_val
):
    data = load_api_fixtures("collection_operations.yaml")
    epid = data["metadata"]["endpoint_id"]
    add_gcs_login(epid)
    if not isinstance(filter_val, list):
        filter_val = [filter_val]
    filter_str = " ".join(f"--filter {f}" for f in filter_val)
    run_line(f"globus collection list {filter_str} {epid}")
    filter_params = {v.lower().replace("-", "_") for v in filter_val}
    assert set(responses.calls[-1].request.params["filter"].split(",")) == filter_params
