import os
import sys
from distutils.util import strtobool

import click

from globus_cli.parsing.command_state import CommandState


def outformat_is_json():
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.outformat_is_json()


def outformat_is_unix():
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.outformat_is_unix()


def outformat_is_text():
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.outformat_is_text()


def get_jmespath_expression():
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.jmespath_expr


def verbosity():
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.verbosity


def is_verbose():
    """
    Only safe to call within a click context.
    """
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    return state.is_verbose()


def out_is_terminal():
    return sys.stdout.isatty()


def err_is_terminal():
    return sys.stderr.isatty()


def term_is_interactive() -> bool:
    explicit_val = os.getenv("GLOBUS_CLI_INTERACTIVE")
    if explicit_val is not None:
        try:
            return strtobool(explicit_val.lower())
        except ValueError:
            pass
    return os.getenv("PS1") is not None
