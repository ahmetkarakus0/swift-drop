import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SERVICES = [
    "user-service",
    "restaurant-service",
    "order-service",
    "courier-service",
    "dispatch-service",
    "gateway",
]


def main():
    for service in SERVICES:
        service_dir = ROOT / service
        command = (
            f"$Host.UI.RawUI.WindowTitle = '{service}'; "
            f"cd '{service_dir}'; "
            r".\.venv\Scripts\Activate.ps1; "
            "python main.py"
        )
        subprocess.Popen(
            [
                "powershell",
                "-NoExit",
                "-ExecutionPolicy", "Bypass",
                "-Command", command,
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        print(f"Started {service}")


if __name__ == "__main__":
    main()
