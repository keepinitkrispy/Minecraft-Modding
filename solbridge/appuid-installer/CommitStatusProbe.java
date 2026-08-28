package com.termux.termuxam;

import android.content.Intent;
import android.content.IntentSender;
import android.content.pm.PackageInstaller;
import android.os.IBinder;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;

public class CommitStatusProbe {
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
        int sid = Integer.parseInt(args[0]);

        Class<?> lirClass = Class.forName("com.android.server.pm.PackageManagerShellCommand$LocalIntentReceiver");
        Constructor<?> ctor = lirClass.getDeclaredConstructor();
        ctor.setAccessible(true);
        Object lir = ctor.newInstance();
        Method getSender = lirClass.getDeclaredMethod("getIntentSender");
        Method getResult = lirClass.getDeclaredMethod("getResult");
        getSender.setAccessible(true);
        getResult.setAccessible(true);
        IntentSender sender = (IntentSender) getSender.invoke(lir);
        System.out.println("LOCAL_RECEIVER=ok class=" + lirClass.getName());

        Class<?> sm = Class.forName("android.os.ServiceManager");
        Method getService = sm.getDeclaredMethod("getService", String.class);
        getService.setAccessible(true);
        IBinder packageBinder = (IBinder) getService.invoke(null, "package");
        Class<?> ipmStub = Class.forName("android.content.pm.IPackageManager$Stub");
        Method asInterface = ipmStub.getDeclaredMethod("asInterface", IBinder.class);
        asInterface.setAccessible(true);
        Object ipm = asInterface.invoke(null, packageBinder);
        Object installer = invoke(ipm, "getPackageInstaller");
        Object session = invoke(installer, "openSession", sid);

        try {
            invoke(session, "commit", sender, false);
        } catch (NoSuchMethodException e) {
            invoke(session, "commit", sender);
        }
        System.out.println("COMMIT_CALLED=1");
        Intent result = (Intent) getResult.invoke(lir);
        int status = result.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE);
        String msg = result.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE);
        System.out.println("STATUS=" + status);
        System.out.println("MESSAGE=" + msg);
        System.out.println("RESULT=" + result.toUri(Intent.URI_INTENT_SCHEME));
        Intent confirm = null;
        try { confirm = result.getParcelableExtra(PackageInstaller.EXTRA_INTENT, Intent.class); }
        catch (Throwable t) { Object x=result.getParcelableExtra(PackageInstaller.EXTRA_INTENT); if (x instanceof Intent) confirm=(Intent)x; }
        if (confirm != null) {
            System.out.println("CONFIRM_COMPONENT=" + confirm.getComponent());
            System.out.println("CONFIRM=" + confirm.toUri(Intent.URI_INTENT_SCHEME));
            if (confirm.getExtras() != null) {
                for (String k : confirm.getExtras().keySet()) {
                    Object v = null; try { v=confirm.getExtras().get(k); } catch(Throwable ignored) {}
                    System.out.println("CONFIRM_EXTRA " + k + " = " + (v==null?"null":v.getClass().getName()+":"+String.valueOf(v)));
                }
            }
        }
    }
}
