"""Section 28: run swebench.harness.run_evaluation unchanged, except that every container it
creates gets the session proxy, the session CA bundle (read-only) and host networking - the same
setup as the SWE-Skills-Bench adapter (section 22). Arguments are passed through unchanged.

  <harness python> scripts/harness_net.py --dataset_name ... (same arguments as run_evaluation)
"""

from __future__ import annotations

import os
import runpy

CA = "/root/.ccr/ca-bundle.crt"
CA_IN = "/usr/local/share/gk-ca.crt"
PROXY_VARS = ("HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "no_proxy")
CA_VARS = ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "PIP_CERT", "CURL_CA_BUNDLE")


def net_kwargs() -> dict:
    env = {k: os.environ[k] for k in PROXY_VARS if k in os.environ}
    env.update(dict.fromkeys(CA_VARS, CA_IN))
    return {
        "network_mode": "host",
        "environment": env,
        "volumes": {CA: {"bind": CA_IN, "mode": "ro"}},
    }


def patch() -> None:
    import docker.models.containers as dmc  # in the harness env only

    orig = dmc.ContainerCollection.create

    def create(self, image, command=None, **kw):
        extra = net_kwargs()
        env = dict(kw.get("environment") or {})
        env.update(extra["environment"])
        kw["environment"] = env
        kw["network_mode"] = extra["network_mode"]
        kw["volumes"] = {**(kw.get("volumes") or {}), **extra["volumes"]}
        return orig(self, image, command, **kw)

    dmc.ContainerCollection.create = create


if __name__ == "__main__":
    if not os.path.exists(CA) or "HTTPS_PROXY" not in os.environ:
        raise SystemExit("section 28 needs the session CA bundle and HTTPS_PROXY")
    patch()
    runpy.run_module("swebench.harness.run_evaluation", run_name="__main__")
