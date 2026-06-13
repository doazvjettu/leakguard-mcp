"""Rule registry. Ordered list drives both scanning and the MCP rule catalog."""

from __future__ import annotations

from leakguard.core.rules.base import Rule
from leakguard.core.rules.lg001 import LG001
from leakguard.core.rules.lg002 import LG002
from leakguard.core.rules.lg003 import LG003
from leakguard.core.rules.lg004 import LG004
from leakguard.core.rules.lg005 import LG005
from leakguard.core.rules.lg006 import LG006
from leakguard.core.rules.lg007 import LG007
from leakguard.core.rules.lg008 import LG008
from leakguard.core.rules.lg009 import LG009
from leakguard.core.rules.lg010 import LG010

# Full v1 ruleset, ordered by id.
RULES: list[Rule] = [
    LG001(), LG002(), LG003(), LG004(), LG005(),
    LG006(), LG007(), LG008(), LG009(), LG010(),
]

RULES_BY_ID: dict[str, Rule] = {r.id: r for r in RULES}
