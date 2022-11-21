# imports
from argparse import Namespace
from deps import irecovery
from pathlib import Path
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.exceptions import NoDeviceConnectedError
import logger


def device_info(type: str, string: str, data_dir: Path, args: Namespace) -> str:
    """Get info about the device"""
    try:
        if type == "normal":
            with LockdownClient(client_name="palera1n", usbmux_connection_type="USB") as lockdown:
                return lockdown.all_values[string]
        elif type == "recovery":
            #status, output = sp.getstatusoutput(f"{get_storage_dir() / 'irecovery'} -q | grep {string} | sed 's/{string}: //'")
            code, output = irecovery(data_dir, args).run("info")
            
            for line in output.split('\n'):
                if string in line:
                    info = line.replace(f"{string}: ", "")
                    
            return info
    except NoDeviceConnectedError:
        logger.error('No device connected.')
        exit(1)