#!/usr/bin/env python3
"""Entrypoint for nanobot gateway in Docker.

Resolves environment variables into config.json at runtime, then launches nanobot gateway.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    # Paths
    app_dir = Path("/app/nanobot")
    config_file = app_dir / "config.json"
    resolved_file = app_dir / "config.resolved.json"
    workspace_dir = app_dir / "workspace"
    venv_dir = Path("/app/.venv")

    # Install editable workspace dependencies at runtime using pip
    # These are bind-mounted but need to be registered in the venv
    print("Installing editable workspace dependencies...", file=sys.stderr)
    # Install to user site-packages (the container has pip but no venv pip)
    subprocess.run(
        ["pip3", "install", "--break-system-packages", "-e", "/app/nanobot-websocket-channel/nanobot-channel-protocol"],
        check=True,
    )
    subprocess.run(
        ["pip3", "install", "--break-system-packages", "-e", "/app/mcp/mcp-lms"],
        check=True,
    )
    subprocess.run(
        ["pip3", "install", "--break-system-packages", "-e", "/app/nanobot-websocket-channel/nanobot-webchat"],
        check=True,
    )
    subprocess.run(
        ["pip3", "install", "--break-system-packages", "-e", "/app/nanobot-websocket-channel/mcp-webchat"],
        check=True,
    )
    subprocess.run(
        ["pip3", "install", "--break-system-packages", "-e", "/app/mcp/mcp-obs"],
        check=True,
    )
    print("Editable dependencies installed.", file=sys.stderr)

    # Add user site-packages to PYTHONPATH so the installed packages are found
    user_site_packages = "/home/appuser/.local/lib/python3.14/site-packages"
    os.environ["PYTHONPATH"] = user_site_packages + ":" + os.environ.get("PYTHONPATH", "")
    print(f"Set PYTHONPATH={user_site_packages}", file=sys.stderr)

    # Read base config
    with open(config_file) as f:
        config = json.load(f)

    # Override provider settings from env vars
    llm_api_key = os.environ.get("LLM_API_KEY")
    llm_api_base_url = os.environ.get("LLM_API_BASE_URL")
    llm_api_model = os.environ.get("LLM_API_MODEL")

    if llm_api_key:
        config["providers"]["custom"]["apiKey"] = llm_api_key
    if llm_api_base_url:
        config["providers"]["custom"]["apiBase"] = llm_api_base_url
    if llm_api_model:
        config["agents"]["defaults"]["model"] = llm_api_model

    # Override gateway settings from env vars
    gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT")

    if gateway_host:
        config["gateway"]["host"] = gateway_host
    if gateway_port:
        config["gateway"]["port"] = int(gateway_port)

    # Override MCP LMS server settings from env vars
    lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL")
    lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY")

    if "mcpServers" not in config.get("tools", {}):
        config.setdefault("tools", {})["mcpServers"] = {}

    if lms_backend_url:
        config["tools"]["mcpServers"].setdefault("lms", {})["env"] = config["tools"]["mcpServers"].get("lms", {}).get("env", {})
        config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = lms_backend_url
    if lms_api_key:
        config["tools"]["mcpServers"].setdefault("lms", {})["env"] = config["tools"]["mcpServers"].get("lms", {}).get("env", {})
        config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = lms_api_key

    # Configure mcp-obs MCP server
    obs_logs_url = os.environ.get("NANOBOT_VICTORIALOGS_URL")
    obs_traces_url = os.environ.get("NANOBOT_VICTORIATRACES_URL")

    if obs_logs_url or obs_traces_url:
        config["tools"]["mcpServers"]["obs"] = {
            "command": "python",
            "args": ["-m", "mcp_obs"],
        }
        env = {}
        if obs_logs_url:
            env["NANOBOT_VICTORIALOGS_URL"] = obs_logs_url
        if obs_traces_url:
            env["NANOBOT_VICTORIATRACES_URL"] = obs_traces_url
        if env:
            config["tools"]["mcpServers"]["obs"]["env"] = env

    # Configure webchat channel if enabled via env vars
    webchat_enabled = os.environ.get("NANOBOT_WEBCHAT_ENABLED", "false").lower() == "true"
    webchat_host = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT")

    if webchat_enabled:
        config["channels"]["webchat"] = {
            "enabled": True,
            "allowFrom": ["*"],
        }
        if webchat_host:
            config["channels"]["webchat"]["host"] = webchat_host
        if webchat_port:
            config["channels"]["webchat"]["port"] = int(webchat_port)

    # Configure mcp-webchat MCP server if enabled
    mcp_webchat_enabled = os.environ.get("NANOBOT_MCP_WEBSOCKET_ENABLED", "false").lower() == "true"
    mcp_webchat_ui_relay_url = os.environ.get("NANOBOT_MCP_WEBSOCKET_UI_RELAY_URL")
    mcp_webchat_token = os.environ.get("NANOBOT_MCP_WEBSOCKET_TOKEN")

    if mcp_webchat_enabled:
        config["tools"]["mcpServers"]["webchat"] = {
            "command": "python",
            "args": ["-m", "mcp_webchat"],
        }
        env = {}
        if mcp_webchat_ui_relay_url:
            env["NANOBOT_MCP_WEBSOCKET_UI_RELAY_URL"] = mcp_webchat_ui_relay_url
        if mcp_webchat_token:
            env["NANOBOT_MCP_WEBSOCKET_TOKEN"] = mcp_webchat_token
        if env:
            config["tools"]["mcpServers"]["webchat"]["env"] = env

    # Write resolved config
    with open(resolved_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Using config: {resolved_file}", file=sys.stderr)

    # Launch nanobot gateway with PYTHONPATH set
    env = os.environ.copy()
    env["PYTHONPATH"] = user_site_packages + ":" + env.get("PYTHONPATH", "")
    subprocess.run(
        ["nanobot", "gateway", "--config", str(resolved_file), "--workspace", str(workspace_dir)],
        env=env,
        check=True,
    )


if __name__ == "__main__":
    main()
