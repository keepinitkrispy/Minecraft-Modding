package com.termux.termuxam;

import android.content.pm.PackageInstaller;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import java.io.File;
import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.security.MessageDigest;

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

    static String hex(byte[] b) {
        StringBuilder sb = new StringBuilder();
        for (byte x : b) sb.append(String.format("%02x", x & 0xff));
        return sb.toString();
    }

    static String sha256(InputStream in) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        byte[] buf = new byte[65536];
        for (int n; (n = in.read(buf)) > 0;) md.update(buf, 0, n);
        return hex(md.digest());
    }

    static OutputStream fileBridgeStream(ParcelFileDescriptor pfd) throws Exception {
        Class<?> c = Class.forName("android.os.FileBridge$FileBridgeOutputStream");
        try {
            Constructor<?> ctor = c.getDeclaredConstructor(ParcelFileDescriptor.class);
            ctor.setAccessible(true);
            return (OutputStream) ctor.newInstance(pfd);
        } catch (NoSuchMethodException e) {
            Constructor<?> ctor = c.getDeclaredConstructor(FileDescriptor.class);
            ctor.setAccessible(true);
            return (OutputStream) ctor.newInstance(pfd.getFileDescriptor());
        }
    }

    public static void main(String[] args) throws Exception {
        bypassHiddenApi();
        String apkPath = args.length > 0 ? args[0] : "/sdcard/Download/SolBridgeCompanion.apk";
        File apk = new File(apkPath);
        String srcHash;
        try (FileInputStream fin = new FileInputStream(apk)) { srcHash = sha256(fin); }
        System.out.println("APK=" + apk + " exists=" + apk.isFile() + " size=" + apk.length() + " sha256=" + srcHash);

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
        ParcelFileDescriptor pfd = (ParcelFileDescriptor) invoke(session, "openWrite", "base.apk", 0L, apk.length());
        System.out.println("OPENWRITE=ok fd=" + pfd.getFd());
        long total = 0;
        try (FileInputStream in = new FileInputStream(apk); OutputStream out = fileBridgeStream(pfd)) {
            byte[] buf = new byte[65536];
            for (int n; (n = in.read(buf)) > 0;) { out.write(buf, 0, n); total += n; }
            Method fsync = out.getClass().getDeclaredMethod("fsync");
            fsync.setAccessible(true);
            fsync.invoke(out);
            System.out.println("FSYNC=ok");
        }
        System.out.println("WROTE=" + total);

        ParcelFileDescriptor readPfd = (ParcelFileDescriptor) invoke(session, "openRead", "base.apk");
        String stagedHash;
        try (InputStream rin = new ParcelFileDescriptor.AutoCloseInputStream(readPfd)) { stagedHash = sha256(rin); }
        System.out.println("STAGED_SHA256=" + stagedHash + " MATCH=" + srcHash.equals(stagedHash));

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
