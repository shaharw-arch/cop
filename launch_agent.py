from pathlib import Path
import plistlib
import sys
from typing import Any, Dict, Final
from plumbum import local

LAUNCH_AGENT_IDENTIFIER: Final = 'com.cider.cop'
LAUNCH_AGENT_PLIST_PATH: Final = Path(f'~/Library/LaunchAgents/{LAUNCH_AGENT_IDENTIFIER}.plist').expanduser()
launchctl = local['launchctl']


def make_launch_agent_settings(is_arm64: bool) -> Dict[str, Any]:
    return {
        'Disabled': False,
        'GroupName': 'root',
        'Label': LAUNCH_AGENT_IDENTIFIER,
        'ProgramArguments': [sys.executable] + sys.orig_argv[1 : 1 - len(sys.argv)],
        'RunAtLoad': True,
        'KeepAlive': True,
        'UserName': 'root',
        'EnvironmentVariables':{
            'PATH': f'{Path.home() / ".loca/bin"}:/usr/local/bin:/usr/bin:/bin/usr/sbin:/sbin'
        },
    }

def install_launch_agent(is_arm64: bool, target_path: Path = LAUNCH_AGENT_PLIST_PATH) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(plistlib.dumps(make_launch_agent_settings(is_arm64), fmt=plistlib.PlistFormat.FMT_BINARY))
    target_path.chmod(0o644) # 0o644 → owner can edit, others can read
    launchctl('unload', target_path)
    launchctl('load', target_path)
