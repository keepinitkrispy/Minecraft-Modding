package dev.solbridge.companion;

import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.content.Intent;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    static final String RUN_COMMAND_PERMISSION = "com.termux.permission.RUN_COMMAND";

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(40, 60, 40, 40);
        TextView t = new TextView(this);
        t.setText("SolBridge Companion\n\nDurable Android control plane + Termux recovery guardian\nLoopback: 127.0.0.1:8765");
        t.setTextSize(20);
        l.addView(t);
        Button start = new Button(this);
        start.setText("Start control plane");
        start.setOnClickListener(v -> startBridge());
        l.addView(start);
        Button recovery = new Button(this);
        recovery.setText("Enable Termux recovery");
        recovery.setOnClickListener(v -> requestRecoveryPermission());
        l.addView(recovery);
        Button access = new Button(this);
        access.setText("Enable Accessibility control");
        access.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));
        l.addView(access);
        setContentView(l);
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(RUN_COMMAND_PERMISSION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{RUN_COMMAND_PERMISSION}, 8765);
        }
        startBridge();
    }

    void requestRecoveryPermission() {
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(RUN_COMMAND_PERMISSION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{RUN_COMMAND_PERMISSION}, 8765);
        }
    }

    void startBridge() {
        Intent i = new Intent(this, BridgeService.class);
        if (Build.VERSION.SDK_INT >= 26) startForegroundService(i); else startService(i);
    }
}
