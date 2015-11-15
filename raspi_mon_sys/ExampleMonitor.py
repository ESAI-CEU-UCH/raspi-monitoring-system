#!/usr/bin/env python2.7
"""This module is an example of how monitoring Python modules should be
implemented.
"""

# Do module configuration stuff.
__channel = "emonhub/rx/{0}/values"

def start():
    pass

# This function SHOULD BE implemented always.
def publish(client):
    """Publishes dummy value at a dummy channel."""
    client.publish(__channel.format("dummy_channel"), "dummy_value")
