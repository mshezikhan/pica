import os
import sys
import subprocess


def is_windows():
    return os.name == "nt"


def enable_autostart(app_name="Pica"):
    if not is_windows():
        return

    startup_dir = os.path.join(
        os.environ["APPDATA"],
        "Microsoft",
        "Windows",
        "Start Menu",
        "Programs",
        "Startup"
    )

    exe_path = sys.executable
    shortcut_path = os.path.join(startup_dir, f"{app_name}.lnk")

    if os.path.exists(shortcut_path):
        return

    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{exe_path}"
$Shortcut.WorkingDirectory = "{os.path.dirname(exe_path)}"
$Shortcut.IconLocation = "{exe_path}"
$Shortcut.Save()
'''

    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command", ps_script
            ],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception:
        pass
