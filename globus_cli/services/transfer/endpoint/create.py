import click

from globus_cli.parsing import (
    CaseInsensitiveChoice, common_options, endpoint_create_and_update_params)
from globus_cli.helpers import print_json_response

from globus_cli.services.transfer.helpers import (
    get_client, assemble_generic_doc)


@click.command('create', help='Create a new Endpoint')
@common_options
@endpoint_create_and_update_params(create=True)
@click.option('--endpoint-type', required=True,
              help=('Type of endpoint to create. "gcp" and "gcs" are just '
                    'shorthand for "globus-connect-personal" and '
                    '"globus-connect-server", respectively'),
              type=CaseInsensitiveChoice((
                  'globus-connect-server', 'globus-connect-personal',
                  's3', 'gcp', 'gcs')))
def endpoint_create(endpoint_type, display_name, description, organization,
                    contact_email, contact_info, info_link, public,
                    default_directory, force_encryption, oauth_server,
                    myproxy_server, myproxy_dn):
    """
    Executor for `globus transfer endpoint create`
    """
    ep_doc = assemble_generic_doc(
        'endpoint',
        display_name=display_name, description=description,
        organization=organization, contact_email=contact_email,
        contact_info=contact_info, info_link=info_link,
        force_encryption=force_encryption, public=public,
        default_directory=default_directory,
        myproxy_server=myproxy_server, myproxy_dn=myproxy_dn,
        oauth_server=oauth_server)
    if endpoint_type == 's3':
        raise click.ClickException(
            'At this time, S3-backed endpoints can only be created via the '
            'legacy hosted Globus CLI.\n'
            '\n'
            'For more information, see:\n'
            '- https://docs.globus.org/cli/using-the-cli\n'
            '- https://docs.globus.org/how-to/amazon-aws-s3-endpoints'
        )
    elif endpoint_type in ('globus-connect-personal', 'gcp'):
        ep_doc['is_globus_connect'] = True
    elif endpoint_type in ('globus-connect-server', 'gcs'):
        pass

    client = get_client()
    res = client.create_endpoint(ep_doc)
    print_json_response(res)
