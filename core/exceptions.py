"""Errors shared across the portal. Pure Python: no Django imports."""


class PortalError(Exception):
    """Base class for errors the portal shows to users as a message."""


class ScriptUnavailable(PortalError):
    """The script for a module or experiment is missing or its path is unsafe."""


class InvalidParams(PortalError):
    """Run parameters do not match what the script accepts."""


class RunRefused(PortalError):
    """A run was not started (runs disabled, no permission, bad script or params)."""


class RunAlreadyActive(RunRefused):
    """The same module or experiment is already queued or running."""

    def __init__(self, run):
        super().__init__("This is already running. Showing that run.")
        self.run = run
