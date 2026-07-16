"""BRAVO Consultant Intelligence Layer.

This package owns goal/workflow semantics.  It deliberately does not own model
invocation, permissions, or durable side effects; those remain in the existing
agent runtime and control plane.
"""

from app.consultant.service import ConsultantService

__all__ = ["ConsultantService"]
