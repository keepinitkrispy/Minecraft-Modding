# SolBridge app-UID installer experiment

This helper is built and executed on-device under the Termux UID. It uses Android's app-side `PackageInstaller` API path (via hidden Binder interfaces with TermuxAm's hidden-API bypass) instead of the shell `cmd package install-write` path. The immediate target is to prove APK bytes can be written into a Termux-owned install session on Android 17 without shell/Shizuku.
