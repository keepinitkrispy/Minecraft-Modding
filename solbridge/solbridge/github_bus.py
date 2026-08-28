from __future__ import annotations
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GitHubError(RuntimeError):
    pass


class GitHubBus:
    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.base = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "solbridge/0.1",
        }

    def _request(self, method: str, path: str, *, params: dict | None = None,
                 body: dict | None = None, allow_status: tuple[int, ...] = ()):
        url = self.base + path
        if params:
            url += "?" + urlencode(params)
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = dict(self.headers)
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=20) as r:
                raw = r.read()
                status = r.status
        except HTTPError as e:
            raw = e.read()
            status = e.code
            if status not in allow_status:
                detail = raw.decode("utf-8", errors="replace")[:2000]
                raise GitHubError(f"GitHub API {status}: {detail}") from e
        obj = json.loads(raw.decode("utf-8")) if raw else None
        return status, obj

    def pending(self):
        _, items = self._request(
            "GET", "/issues",
            params={"state": "open", "labels": "solbridge-command", "per_page": 20},
        )
        return [x for x in (items or []) if "pull_request" not in x]

    def comment(self, issue_number: int, body: str):
        return self._request(
            "POST", f"/issues/{issue_number}/comments", body={"body": body}
        )[1]

    def close(self, issue_number: int):
        return self._request(
            "PATCH", f"/issues/{issue_number}", body={"state": "closed"}
        )[1]

    def ensure_labels(self):
        for name, color, desc in [
            ("solbridge-command", "1f6feb", "Command for SolBridge device agent"),
            ("solbridge-running", "d29922", "Claimed by SolBridge device agent"),
            ("solbridge-done", "238636", "Completed by SolBridge device agent"),
            ("solbridge-error", "da3633", "Failed in SolBridge device agent"),
        ]:
            self._request(
                "POST", "/labels",
                body={"name": name, "color": color, "description": desc},
                allow_status=(422,),
            )

    def labels(self, issue_number: int, labels: list[str]):
        return self._request(
            "POST", f"/issues/{issue_number}/labels", body={"labels": labels}
        )[1]
