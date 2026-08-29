from __future__ import annotations
import base64
import json
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
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
            "User-Agent": "solbridge/0.2",
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
        blocked = {"solbridge-running", "solbridge-done", "solbridge-error"}
        out = []
        for x in items or []:
            if "pull_request" in x:
                continue
            labels = {str(v.get("name", "")) for v in (x.get("labels") or []) if isinstance(v, dict)}
            if labels & blocked:
                continue
            out.append(x)
        out.sort(key=lambda x: int(x.get("number") or 0))
        return out

    def verify_owner_command_file(self, *, path: str, commit_sha: str, expected: dict) -> bool:
        owner = self.repo.split("/", 1)[0]
        if not path.startswith("commands/") or not path.endswith(".json") or ".." in path:
            return False
        if len(commit_sha) != 40 or any(c not in "0123456789abcdefABCDEF" for c in commit_sha):
            return False
        _, commit = self._request("GET", f"/commits/{commit_sha}")
        actor = str(((commit or {}).get("author") or {}).get("login") or "")
        if actor.lower() != owner.lower():
            return False
        _, item = self._request(
            "GET", f"/contents/{quote(path, safe='/')}", params={"ref": commit_sha}
        )
        if not isinstance(item, dict) or item.get("type") != "file" or item.get("encoding") != "base64":
            return False
        try:
            raw = base64.b64decode(str(item.get("content") or "")).decode("utf-8")
            actual = json.loads(raw)
        except Exception:
            return False
        return actual == expected

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
