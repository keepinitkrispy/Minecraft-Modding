from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_companion_declares_termux_recovery_permission_and_visibility():
    manifest = (ROOT / "native-companion-template" / "AndroidManifest.xml").read_text()
    assert 'android:name="com.termux.permission.RUN_COMMAND"' in manifest
    assert '<package android:name="com.termux"' in manifest


def test_guardian_uses_fixed_background_run_command_target():
    src = (ROOT / "native-companion-template" / "src" / "dev" / "solbridge" / "companion" / "BridgeService.java").read_text()
    assert 'TERMUX_RUN_SERVICE = "com.termux.app.RunCommandService"' in src
    assert 'ENSURE_SCRIPT = "/data/data/com.termux/files/home/.local/bin/solbridge-ensure"' in src
    assert 'i.setAction("com.termux.RUN_COMMAND")' in src
    assert 'i.putExtra("com.termux.RUN_COMMAND_BACKGROUND", true)' in src
    assert 'RUN_COMMAND_SESSION_ACTION' not in src
    assert 'checkSelfPermission(RUN_COMMAND_PERMISSION)' in src
    assert 'guardianLoop' in src


def test_guardian_exposes_own_permission_settings_for_automated_recovery():
    src = (ROOT / "native-companion-template" / "src" / "dev" / "solbridge" / "companion" / "BridgeService.java").read_text()
    assert 'Settings.ACTION_APPLICATION_DETAILS_SETTINGS' in src
    assert 'p.startsWith("/permission_settings")' in src
    wrapper = (ROOT / "deploy_guardian_heartbeat.py").read_text()
    assert 'd.companion_get("/permission_settings")' in wrapper
    assert 'run commands in termux environment' in wrapper.lower()
    assert 'additional permissions' in wrapper.lower()


def test_guardian_only_recovers_after_stale_heartbeat():
    src = (ROOT / "native-companion-template" / "src" / "dev" / "solbridge" / "companion" / "BridgeService.java").read_text()
    assert 'HEARTBEAT_TIMEOUT_MS = 45_000L' in src
    assert 'GUARDIAN_RETRY_MS = 60_000L' in src
    assert 'heartbeatAge > HEARTBEAT_TIMEOUT_MS' in src
    assert 'p.startsWith("/heartbeat")' in src
    assert 'heartbeat_age_ms' in src


def test_agent_sends_heartbeat_each_poll_cycle():
    agent = (ROOT / "solbridge" / "agent.py").read_text()
    assert 'def _heartbeat() -> bool:' in agent
    assert 'companion_get("/heartbeat", timeout=3.0)' in agent
    loop = agent.index('while not STOP:')
    heartbeat = agent.index('_heartbeat()', loop)
    pending = agent.index('bus.pending()', loop)
    assert loop < heartbeat < pending


def test_install_script_exposes_only_fixed_recovery_script_and_external_gate():
    install = (ROOT / "install-termux.sh").read_text()
    assert 'cat > "$HOME/.local/bin/solbridge-ensure"' in install
    assert 'allow-external-apps=true' in install
    assert 'sv up solbridge' in install
    assert 'service-daemon start' in install
    assert 'chmod 700 "$HOME/.local/bin/solbridge-ensure"' in install


def test_boot_fallback_reuses_same_recovery_primitive():
    install = (ROOT / "install-termux.sh").read_text()
    assert 'exec "$HOME/.local/bin/solbridge-ensure"' in install


def test_fault_injection_requires_native_attempt_and_heartbeat_recovery():
    fault = (ROOT / "guardian_recovery_fault_test.py").read_text()
    assert 'service_down()' in fault
    assert 'guardian_attempt_advanced' in fault
    assert 'service_recovered' in fault
    assert 'heartbeat_resumed' in fault
    assert 'all(result["checks"].values())' in fault
