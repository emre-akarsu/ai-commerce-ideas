"""Question impact: how many lines of a scope a question can change.

A question's impact is the number of lines whose activity (module condition, line condition or
with_module context) or lookup row depends on it. For the global `finish_level` question it is
the number of lines whose selected option differs from the line default at some finish level.
Impact is exported (`priority` in job-kit-ui/1, also `impact` in job-kit-ui/2); it no longer
decides which questions are asked upfront (that is a scope decision with a `reason_upfront`).
"""

from __future__ import annotations

from .formula import condition_names
from .model import FINISH_LEVEL_QUESTION, FINISH_LEVELS, Line, Scope, option_for_level


def _changes_with_level(line: Line) -> bool:
    return any(option_for_level(line, level).id != line.default_option  # type: ignore[union-attr]
               for level in FINISH_LEVELS) if line.options else False


def question_impact(scope: Scope, question_id: str) -> int:
    count = 0
    for m in scope.modules:
        module_names = condition_names(m.when) if m.when else set()
        for x in m.lines:
            if question_id == FINISH_LEVEL_QUESTION:
                count += _changes_with_level(x)
                continue
            names = module_names | (condition_names(x.effective_when) if x.effective_when
                                    else set())
            lookup = x.spec_lookup is not None and x.spec_lookup["key"] == question_id
            count += question_id in names or lookup
    return count
