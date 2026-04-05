# Feature: openenv-email-triage, Property 1: Invalid Action raises ValidationError without state mutation

"""
**Validates: Requirements 1.4, 1.5**
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from openenv_email_triage.models import Action, Operation

# All valid operation string values
_VALID_OPERATIONS = {op.value for op in Operation}

# Strategy: strings that are NOT valid Operation values
invalid_operation_st = st.text().filter(lambda s: s not in _VALID_OPERATIONS)

# Strategy: ints outside {1, 2, 3}
invalid_priority_st = st.integers().filter(lambda n: n not in (1, 2, 3))


@given(invalid_op=invalid_operation_st)
@settings(max_examples=100)
def test_invalid_operation_raises_validation_error(invalid_op: str) -> None:
    """Constructing an Action with an invalid operation string must raise ValidationError."""
    with pytest.raises(ValidationError):
        Action(operation=invalid_op)


@given(invalid_priority=invalid_priority_st)
@settings(max_examples=100)
def test_invalid_priority_raises_validation_error(invalid_priority: int) -> None:
    """Constructing an Action with a priority outside {1,2,3} must raise ValidationError."""
    with pytest.raises(ValidationError):
        Action(operation=Operation.prioritize, priority=invalid_priority)


@given(priority=st.sampled_from([1, 2, 3]))
@settings(max_examples=50)
def test_valid_priority_does_not_raise(priority: int) -> None:
    """Constructing an Action with a valid priority must NOT raise."""
    action = Action(operation=Operation.prioritize, priority=priority)
    assert action.priority == priority


@given(op=st.sampled_from(list(Operation)))
@settings(max_examples=50)
def test_valid_operation_does_not_raise(op: Operation) -> None:
    """Constructing an Action with any valid Operation must NOT raise."""
    action = Action(operation=op)
    assert action.operation == op
