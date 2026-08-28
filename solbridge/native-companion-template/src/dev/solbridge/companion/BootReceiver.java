package dev.solbridge.companion;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public class BootReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context c, Intent i) {
        Intent service = new Intent(c, BridgeService.class);
        if (Build.VERSION.SDK_INT >= 26) c.startForegroundService(service); else c.startService(service);
    }
}
