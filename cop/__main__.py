import platform
import time
from pathlib import Path
import click
from enum import Enum
import launch_agent

from pymobiledevice3.lockdown import LockdownClient, create_using_usbmux
from pymobiledevice3.usbmux import MuxDevice, list_devices
from plumbum import local

osascript = local['osascript']

GRAY_LIST_PATH = Path(__file__).resolve().parent / 'gray_devices_list.txt'


class AlertType(Enum):
    Information = 'informational'
    Warning = 'warning'
    Critical = 'critical'


def alert(title: str, message: str, alert_type: AlertType = AlertType.Information) -> None:
    script = f"""on run argv
        display alert (item 1 of argv) message (item 2 of argv) as {alert_type.value}
    end run"""
    osascript('-e', script, '--', title, message)


def notify(title: str, message: str, subtitle: str | None = None) -> None:
    script = """on run argv
        display notification item 1 of argv with title item 2 of argv subtitle item 3 of argv
    end run"""
    osascript('-e', script, '--', message, title, subtitle or '')


def handle_notify_event(udid: str, product_type: str, product_version: str, device_in_gray_list: bool) -> None:
    if not device_in_gray_list:
        alert(
            '🚨 Unlisted Phone Detected!',
            f'{product_type}{product_version}\n{udid}\n Please Notify Allen / Yair',
            alert_type=AlertType.Critical,
        )
        return


def is_device_in_gray_list(device_udid):
    with open(GRAY_LIST_PATH) as f:
        for line in f:
            if line.strip().upper() == device_udid:
                return True
    return False


def handle_lockdown_connection(lockdown: LockdownClient):
    assert lockdown.udid is not None
    assert lockdown.product_type is not None
    handle_notify_event(
        lockdown.udid, lockdown.product_type, lockdown.product_version, is_device_in_gray_list(lockdown.udid)
    )


def handle_mux_device(mux_device: MuxDevice):
    if not mux_device.is_usb:
        return
    with create_using_usbmux(autopair=False, serial=mux_device.serial) as lockdown:
        if not lockdown.paired:
            assert lockdown.udid is not None
            assert lockdown.product_type is not None
            handle_notify_event(
                lockdown.udid, lockdown.product_type, lockdown.product_version, is_device_in_gray_list(lockdown.udid)
            )
            return
        handle_lockdown_connection(lockdown)


@click.command()
@click.option(
    '--install-launch-agent',
    default=False,
    is_flag=True,
    help='Install cop as a launchd launch and exit',
)
def cli(install_launch_agent: bool = False) -> None:
    if install_launch_agent:
        launch_agent.install_launch_agent(platform.machine() == 'arm64')
        return

    notify('Cop started', '👮', '')
    while True:
        mux_devices = list_devices()
        for mux_device in mux_devices:
            handle_mux_device(mux_device)

        time.sleep(1)


if __name__ == '__main__':
    cli()
