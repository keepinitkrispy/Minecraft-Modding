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
    assert 'checkSelfPermission(RUN_COMMAND_PERMISSION)' in src
    assert 'guardianLoop' in src
    assert 'Thread.sleep(1000)' in src


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
