package dev.solbridge.companion;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.content.Intent;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(40, 60, 40, 40);
        TextView t = new TextView(this);
        t.setText("SolBridge Companion\n\nDurable Android control plane\nLoopback: 127.0.0.1:8765");
        t.setTextSize(20);
        l.addView(t);
        Button start = new Button(this);
        start.setText("Start control plane");
        start.setOnClickListener(v -> startBridge());
        l.addView(start);
        Button access = new Button(this);
        access.setText("Enable Accessibility control");
        access.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));
        l.addView(access);
        setContentView(l);
        startBridge();
    }

    void startBridge() {
        Intent i = new Intent(this, BridgeService.class);
        if (Build.VERSION.SDK_INT >= 26) startForegroundService(i); else startService(i);
    }
}
