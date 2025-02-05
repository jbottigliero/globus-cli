def test_list_commands_contains_expected_commands(run_line):
    result = run_line("globus list-commands")
    # this is a snapshot of a grepped `globus list-commands` output which worked,
    # filtered to one command per group
    for cmd in (
        "globus cli-profile-list",
        "globus delete",
        "globus get-identities",
        "globus list-commands",
        "globus login",
        "globus logout",
        "globus ls",
        "globus mkdir",
        "globus rename",
        "globus rm",
        "globus transfer",
        "globus update",
        "globus version",
        "globus whoami",
        "globus api auth",
        "globus bookmark create",
        "globus collection delete",
        "globus endpoint activate",
        "globus endpoint permission create",
        "globus endpoint role create",
        "globus endpoint server add",
        "globus endpoint storage-gateway list",
        "globus endpoint user-credential delete",
        "globus flows delete",
        "globus gcp create guest",
        "globus group create",
        "globus group invite accept",
        "globus group member add",
        "globus search delete-by-query",
        "globus search index create",
        "globus search index role create",
        "globus search subject delete",
        "globus search task list",
        "globus session consent",
        "globus task cancel",
        "globus timer list",
    ):
        assert cmd in result.output
