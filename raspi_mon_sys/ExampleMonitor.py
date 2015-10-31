#!/use/bin/env python
"""This module is an example of how monitoring Python modules should be
implemented.
"""

# Do module configuration stuff.
__channel = "emonhub/rx/{0}/values"

# This function SHOULD BE implemented always.
def publish(client):
    """Publishes dummy value at a dummy channel."""
    client.publish(__channel.format("dummy_channel"), "dummy_value")
