"""Windows specific functions for cli_tool_audit"""
import winreg


def get_installed_programs_registry():
    """List apps with windows versions (many are 4 part versions)"""
    path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
    programs = []

    for i in range(0, winreg.QueryInfoKey(key)[0]):
        skey_name = winreg.EnumKey(key, i)
        skey = winreg.OpenKey(key, skey_name)
        try:
            name = winreg.QueryValueEx(skey, "DisplayName")[0]
            version = winreg.QueryValueEx(skey, "DisplayVersion")[0]
            programs.append((name, version))
        except OSError:
            pass
        finally:
            winreg.CloseKey(skey)

    return programs


if __name__ == "__main__":

    def run() -> None:
        installed_programs = get_installed_programs_registry()
        for name, version in installed_programs:
            print(f"Name: {name}, Version: {version}")

    run()
