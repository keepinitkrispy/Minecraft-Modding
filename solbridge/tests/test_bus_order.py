from solbridge.github_bus import GitHubBus


class FakeBus(GitHubBus):
    def __init__(self, items):
        self.items = items

    def _request(self, method, path, **kwargs):
        return 200, self.items


def test_pending_commands_are_oldest_first_and_blocked_are_ignored():
    items = [
        {"number": 30, "labels": [{"name": "solbridge-command"}]},
        {"number": 10, "labels": [{"name": "solbridge-command"}]},
        {"number": 20, "labels": [{"name": "solbridge-command"}, {"name": "solbridge-running"}]},
    ]
    assert [x["number"] for x in FakeBus(items).pending()] == [10, 30]
