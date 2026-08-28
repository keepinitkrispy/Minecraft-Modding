package dev.solbridge.companion;

import android.accessibilityservice.*;
import android.view.accessibility.*;
import android.graphics.Path;
import android.graphics.Rect;
import android.os.Bundle;
import java.util.*;

public class SolAccessibilityService extends AccessibilityService {
    static volatile SolAccessibilityService INSTANCE;
    static final ArrayDeque<String> EVENTS = new ArrayDeque<>();

    @Override protected void onServiceConnected() {
        INSTANCE = this;
        synchronized (EVENTS) { EVENTS.addLast("{\"type\":\"service_connected\"}"); }
    }

    @Override public void onInterrupt() {}
    @Override public void onDestroy() { if (INSTANCE == this) INSTANCE = null; super.onDestroy(); }

    @Override public void onAccessibilityEvent(AccessibilityEvent e) {
        String rec = "{\"t\":" + System.currentTimeMillis()
            + ",\"type\":" + e.getEventType()
            + ",\"pkg\":\"" + esc(String.valueOf(e.getPackageName()))
            + "\",\"cls\":\"" + esc(String.valueOf(e.getClassName()))
            + "\",\"text\":\"" + esc(String.valueOf(e.getText())) + "\"}";
        synchronized (EVENTS) {
            EVENTS.addLast(rec);
            while (EVENTS.size() > 200) EVENTS.removeFirst();
        }
    }

    static String esc(String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\r", " ").replace("\n", " ");
    }

    static String events() {
        StringBuilder b = new StringBuilder("[");
        synchronized (EVENTS) {
            boolean first = true;
            for (String s : EVENTS) {
                if (!first) b.append(',');
                first = false;
                b.append(s);
            }
        }
        return b.append(']').toString();
    }

    String tree() {
        AccessibilityNodeInfo r = getRootInActiveWindow();
        StringBuilder b = new StringBuilder();
        int[] count = {0};
        dump(r, b, 0, count);
        return "[" + b + "]";
    }

    void dump(AccessibilityNodeInfo x, StringBuilder b, int d, int[] count) {
        if (x == null || d > 18 || count[0] > 800) return;
        count[0]++;
        if (b.length() > 0) b.append(',');
        Rect z = new Rect();
        x.getBoundsInScreen(z);
        b.append("{\"d\":").append(d)
         .append(",\"cls\":\"").append(esc(String.valueOf(x.getClassName())))
         .append("\",\"text\":\"").append(esc(String.valueOf(x.getText())))
         .append("\",\"desc\":\"").append(esc(String.valueOf(x.getContentDescription())))
         .append("\",\"id\":\"").append(esc(x.getViewIdResourceName()))
         .append("\",\"click\":").append(x.isClickable())
         .append(",\"edit\":").append(x.isEditable())
         .append(",\"b\":\"").append(z.left).append(',').append(z.top).append(',').append(z.right).append(',').append(z.bottom)
         .append("\"}");
        for (int i=0; i<x.getChildCount(); i++) dump(x.getChild(i), b, d+1, count);
    }

    boolean tap(int x, int y) {
        Path p = new Path();
        p.moveTo(x, y);
        GestureDescription.Builder g = new GestureDescription.Builder();
        g.addStroke(new GestureDescription.StrokeDescription(p, 0, 60));
        return dispatchGesture(g.build(), null, null);
    }

    boolean global(int action) { return performGlobalAction(action); }

    boolean setText(String s) {
        AccessibilityNodeInfo n = findFocus(AccessibilityNodeInfo.FOCUS_INPUT);
        if (n == null) n = findEditable(getRootInActiveWindow());
        if (n == null) return false;
        Bundle b = new Bundle();
        b.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, s);
        return n.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, b);
    }

    AccessibilityNodeInfo findEditable(AccessibilityNodeInfo n) {
        if (n == null) return null;
        if (n.isEditable()) return n;
        for (int i=0; i<n.getChildCount(); i++) {
            AccessibilityNodeInfo r = findEditable(n.getChild(i));
            if (r != null) return r;
        }
        return null;
    }
}
