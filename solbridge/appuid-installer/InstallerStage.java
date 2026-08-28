package com.termux.termuxam;

import android.content.pm.PackageInstaller;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import java.io.File;
import java.io.FileInputStream;
import java.io.OutputStream;
import java.lang.reflect.Method;

public class InstallerStage {
    static Object invoke(Object obj, String name, Object... args) throws Exception {
        Method best = null;
        outer: for (Method m : obj.getClass().getMethods()) {
            if (!m.getName().equals(name) || m.getParameterCount() != args.length) continue;
            Class<?>[] t = m.getParameterTypes();
            for (int i=0;i<t.length;i++) {
                if (args[i] == null) continue;
                Class<?> a = args[i].getClass();
                if (t[i].isPrimitive()) {
                    if ((t[i]==int.class && a==Integer.class) || (t[i]==long.class && a==Long.class) ||
                        (t[i]==boolean.class && a==Boolean.class) || (t[i]==float.class && a==Float.class)) continue;
                    continue outer;
                }
                if (!t[i].isAssignableFrom(a)) continue outer;
            }
            best = m; break;
        }
        if (best == null) throw new NoSuchMethodException(name + "/" + args.length + " on " + obj.getClass());
        best.setAccessible(true);
        return best.invoke(obj, args);
    }

    static void bypassHiddenApi() throws Exception {
        Class<?> c = Class.forName("com.termux.termuxam.reflection.ReflectionUtils");
        Method m = c.getDeclaredMethod("bypassHiddenAPIReflectionRestrictions");
        m.setAccessible(true);
        m.invoke(null);
    }

    public static void main(String[] args) throws Exception {
        bypassHiddenApi();
        String apkPath = args.length > 0 ? args[0] : "/sdcard/Download/SolBridgeCompanion.apk";
        File apk = new File(apkPath);
        System.out.println("APK=" + apk + " exists=" + apk.isFile() + " size=" + apk.length());

        Class<?> sm = Class.forName("android.os.ServiceManager");
        Method getService = sm.getDeclaredMethod("getService", String.class);
        getService.setAccessible(true);
        IBinder packageBinder = (IBinder) getService.invoke(null, "package");
        if (packageBinder == null) throw new IllegalStateException("package binder null");

        Class<?> ipmStub = Class.forName("android.content.pm.IPackageManager$Stub");
        Method asInterface = ipmStub.getDeclaredMethod("asInterface", IBinder.class);
        asInterface.setAccessible(true);
        Object ipm = asInterface.invoke(null, packageBinder);
        Object installer = invoke(ipm, "getPackageInstaller");
        System.out.println("INSTALLER_PROXY=" + installer.getClass().getName());

        PackageInstaller.SessionParams params = new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
        params.setAppPackageName("dev.solbridge.companion");
        Object sessionIdObj;
        try {
            sessionIdObj = invoke(installer, "createSession", params, "com.termux", null, 0);
        } catch (NoSuchMethodException e) {
            sessionIdObj = invoke(installer, "createSession", params, "com.termux", 0);
        }
        int sid = ((Integer)sessionIdObj).intValue();
        System.out.println("SESSION=" + sid);

        Object session = invoke(installer, "openSession", sid);
        System.out.println("SESSION_PROXY=" + session.getClass().getName());
        ParcelFileDescriptor pfd = (ParcelFileDescriptor) invoke(session, "openWrite", "base.apk", 0L, apk.length());
        System.out.println("OPENWRITE=ok fd=" + pfd.getFd());
        long total = 0;
        try (FileInputStream in = new FileInputStream(apk); OutputStream out = new ParcelFileDescriptor.AutoCloseOutputStream(pfd)) {
            byte[] buf = new byte[65536];
            for (int n; (n = in.read(buf)) > 0;) { out.write(buf, 0, n); total += n; }
            out.flush();
        }
        System.out.println("WROTE=" + total);
        Object names = invoke(session, "getNames");
        if (names instanceof String[]) {
            StringBuilder sb = new StringBuilder();
            for (String n : (String[])names) { if (sb.length()>0) sb.append(','); sb.append(n); }
            System.out.println("NAMES=" + sb);
        }
        invoke(session, "close");
        System.out.println("STAGED_SESSION=" + sid);
    }
}
