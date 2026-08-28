from __future__ import annotations
import requests

class GitHubBus:
    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.base = f"https://api.github.com/repos/{repo}"
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "solbridge/0.1",
        })

    def _check(self, r):
        r.raise_for_status()
        return r.json() if r.content else None

    def pending(self):
        r = self.s.get(f"{self.base}/issues", params={"state":"open", "labels":"solbridge-command", "per_page":20}, timeout=20)
        items = self._check(r)
        return [x for x in items if "pull_request" not in x]

    def comment(self, issue_number: int, body: str):
        return self._check(self.s.post(f"{self.base}/issues/{issue_number}/comments", json={"body": body}, timeout=20))

    def close(self, issue_number: int):
        return self._check(self.s.patch(f"{self.base}/issues/{issue_number}", json={"state":"closed"}, timeout=20))

    def ensure_labels(self):
        for name, color, desc in [
            ("solbridge-command", "1f6feb", "Command for SolBridge device agent"),
            ("solbridge-running", "d29922", "Claimed by SolBridge device agent"),
            ("solbridge-done", "238636", "Completed by SolBridge device agent"),
            ("solbridge-error", "da3633", "Failed in SolBridge device agent"),
        ]:
            r = self.s.post(f"{self.base}/labels", json={"name":name, "color":color, "description":desc}, timeout=20)
            if r.status_code not in (201, 422):
                r.raise_for_status()

    def labels(self, issue_number: int, labels: list[str]):
        return self._check(self.s.post(f"{self.base}/issues/{issue_number}/labels", json={"labels": labels}, timeout=20))
