"""Makes ansible-lint pytest fixtures available for lint rule tests."""

import pytest
from ansiblelint.file_utils import Lintable
from ansiblelint.rules import RulesCollection
from ansiblelint.runner import Runner
from ansiblelint.testing.fixtures import *  # noqa: F403

CUSTOM_RULESDIR = ".ansible-lint-rules"


@pytest.fixture
def custom_rules(config_options, app):  # noqa: F811
    """Return a RulesCollection loaded from .ansible-lint-rules/."""
    from ansiblelint.rules import RulesCollection

    return RulesCollection(
        app=app,
        rulesdirs=[CUSTOM_RULESDIR],
        options=config_options,
    )


@pytest.fixture
def ansible_lint_runner(request, custom_rules: RulesCollection) -> list:
    path = request.param[0]
    rule_id = request.param[1]
    results = Runner(Lintable(path), rules=custom_rules).run()
    return [r for r in results if r.rule.id == rule_id]
