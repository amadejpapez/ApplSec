"""
Errors collected during the run. The run continues, but fails at the end if any were collected.
Append here instead of raising when raising would lose or block other posts.
"""

errors: list[Exception] = []
