package dev.solbridge.companion;

import android.app.*;
import android.accessibilityservice.AccessibilityService;
import android.content.*;
import android.os.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class BridgeService extends Service {
    static final String TOKEN = "__TOKEN__";
    volatile boolean run = true;
    ServerSocket server;

    @Override public void onCreate() {
        super.onCreate();
        NotificationManager nm = (NotificationManager)getSystemService(NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26) {
            nm.createNotificationChannel(new NotificationChannel("solbridge", "SolBridge", NotificationManager.IMPORTANCE_LOW));
        }
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
            ? new Notification.Builder(this, "solbridge") : new Notification.Builder(this);
        b.setContentTitle("SolBridge control plane")
         .setContentText("Local agent bridge active")
         .setSmallIcon(android.R.drawable.stat_notify_sync);
        startForeground(8765, b.build());
        new Thread(this::serve, "solbridge-http").start();
    }

    @Override public int onStartCommand(Intent i, int flags, int startId) { return START_STICKY; }
    @Override public android.os.IBinder onBind(Intent i) { return null; }
    @Override public void onDestroy() {
        run = false;
        try { if (server != null) server.close(); } catch (Exception ignored) {}
        super.onDestroy();
    }

    void serve() {
        try {
            server = new ServerSocket();
            server.setReuseAddress(true);
            server.bind(new InetSocketAddress(InetAddress.getByName("127.0.0.1"), 8765));
            while (run) {
                Socket s = server.accept();
                new Thread(() -> handle(s), "solbridge-client").start();
            }
        } catch (Exception ignored) {}
    }

    void handle(Socket s) {
        try {
            s.setSoTimeout(3000);
            BufferedReader r = new BufferedReader(new InputStreamReader(s.getInputStream(), StandardCharsets.UTF_8));
            String first = r.readLine();
            if (first == null) return;
            Map<String,String> headers = new HashMap<>();
            String line;
            while ((line = r.readLine()) != null && !line.isEmpty()) {
                int q = line.indexOf(':');
                if (q > 0) headers.put(line.substring(0,q).trim().toLowerCase(Locale.ROOT), line.substring(q+1).trim());
            }
            if (!TOKEN.equals(headers.get("x-solbridge-token"))) {
                reply(s, 403, "{\"ok\":false,\"error\":\"forbidden\"}");
                return;
            }
            String[] parts = first.split(" ");
            String path = parts.length > 1 ? parts[1] : "/";
            reply(s, 200, route(path));
        } catch (Exception e) {
            try { reply(s, 500, "{\"ok\":false,\"error\":\"" + json(e.toString()) + "\"}"); } catch (Exception ignored) {}
        } finally {
            try { s.close(); } catch (Exception ignored) {}
        }
    }

    String route(String p) throws Exception {
        SolAccessibilityService a = SolAccessibilityService.INSTANCE;
        if (p.startsWith("/health")) {
            return "{\"ok\":true,\"accessibility\":" + (a != null) + ",\"pid\":" + android.os.Process.myPid() + "}";
        }
        if (p.startsWith("/events")) return SolAccessibilityService.events();
        if (p.startsWith("/tree")) return a == null ? "[]" : a.tree();
        if (p.startsWith("/tap")) {
            Map<String,String> q = query(p);
            return ok(a != null && a.tap(Integer.parseInt(q.get("x")), Integer.parseInt(q.get("y"))));
        }
        if (p.startsWith("/back")) return ok(a != null && a.global(AccessibilityService.GLOBAL_ACTION_BACK));
        if (p.startsWith("/home")) return ok(a != null && a.global(AccessibilityService.GLOBAL_ACTION_HOME));
        if (p.startsWith("/text")) {
            Map<String,String> q = query(p);
            return ok(a != null && a.setText(q.getOrDefault("value", "")));
        }
        if (p.startsWith("/launch")) {
            Map<String,String> q = query(p);
            Intent i = getPackageManager().getLaunchIntentForPackage(q.get("package"));
            if (i == null) return ok(false);
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(i);
            return ok(true);
        }
        return "{\"ok\":false,\"error\":\"unknown\"}";
    }

    Map<String,String> query(String p) throws Exception {
        Map<String,String> m = new HashMap<>();
        int x = p.indexOf('?');
        if (x < 0) return m;
        for (String kv : p.substring(x+1).split("&")) {
            String[] z = kv.split("=", 2);
            String k = URLDecoder.decode(z[0], "UTF-8");
            String v = z.length > 1 ? URLDecoder.decode(z[1], "UTF-8") : "";
            m.put(k, v);
        }
        return m;
    }

    String ok(boolean x) { return "{\"ok\":" + x + "}"; }

    static String json(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\r", " ").replace("\n", " ");
    }

    void reply(Socket s, int code, String body) throws Exception {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        OutputStream o = s.getOutputStream();
        String h = "HTTP/1.1 " + code + " OK\r\n"
                 + "Content-Type: application/json\r\n"
                 + "Content-Length: " + bytes.length + "\r\n"
                 + "Connection: close\r\n\r\n";
        o.write(h.getBytes(StandardCharsets.UTF_8));
        o.write(bytes);
        o.flush();
    }
}
