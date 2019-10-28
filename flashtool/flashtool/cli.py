# flashtool.py

import click
import flashtool as kmb
import flashtool.logging as logging
import flashtool.configparser as configparser
import os


app_default_cfg = {"app": {'timeout': None, 'force': False, 'retries': 0}}

logging_default_cfg = {
    "logging": {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            },
            "console": {
                "class": "flashtool.logging.SuppressExceptionFormatter",
                "format": "%(name)s: %(levelname)s. %(message)s"
            }
        },
        "handlers": {
            "file": {
                "class": "flashtool.logging.FileHandler",
                "level": "DEBUG",
                "formatter": "default",
                "filename": "flashtool.log"
            },
            "console": {
                "class": "flashtool.logging.ClickHandler",
                "level": "SUCCESS",
                "formatter": "console",
                "levelcolor": {
                    "CRITICAL": "red",
                    "ERROR": "red",
                    "WARNING": "yellow",
                    "INFO": None,
                    "DEBUG": None,
                    "NOTSET": None,
                    "SUCCESS": "green"
                }
            }
        },
        "root": {
            "handlers": [
                "file",
                "console"
            ],
            "level": "DEBUG"
        }
    },
}

cp = configparser.ConfigParser(config_type="json")

cp.read_dict(app_default_cfg)
cp.read_dict(logging_default_cfg)

cp.read(os.path.expanduser('~/flashtool/config.json'))

cp.read('config.json')

logger = logging.getLogger("flashtool", logging_cfg=cp["logging"])


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version="0.1")
def cli():
    pass


@cli.command("download", short_help='Download binaries into device. Type "flashtool download -h" for more.')
@click.option("-v", "--verbose", "verbose", count=True)
@click.option("-t", "--timeout", type=int, default=-1, help="Timeout in seconds.")
@click.option("-d", '--device-type', type=click.Choice(('usb', 'pcie'), case_sensitive=False), multiple=True, help="Filter devices based on type: USB or PCIe")
# @click.option("-s", "--serialno", help="Select device with this serialno only.")
@click.argument("fip", type=click.Path(exists=True, resolve_path=True), required=True)
@click.option("-f", "--force", is_flag=True, help="Skip FIP checking.")
# def download(verbose, timeout, device_type, serialno, fip, force):
def download(verbose, timeout, device_type, fip, force):
    """Download FIP into device"""
    serialno = None
    try:
        if verbose > 0:
            for handler in logger.root.handlers:
                handler.setLevel("DEBUG")
            logger.debug("VERBOSE On")

        if timeout >= 0:
            cp["app"]["timeout"] = timeout
        timeout = cp["app"]["timeout"]
        logger.debug("Timeout is set to {}s".format(timeout))

        if force:
            cp['app']['force'] = force
        force = cp['app']['force']
        if force:
            logger.debug("Force mode on. FIP checking disabled")

        if not force:
            stdout = kmb.fip_check(fip)
            logger.debug(stdout)
            logger.info("FIP {} passed structural integrity test".format(fip))

        try:
            if len(device_type) > 1:
                raise click.BadOptionUsage(device_type, "--device-type can be provided only once")
            if device_type[0] == "usb":
                logger.debug("USB devices selected")
                devices = kmb.SingleUSBDevice.discover()
                if not devices:
                    raise kmb.DeviceNotFoundError("Keembay USB device not found")
            else:
                logger.debug("PCIE devices selected")
                devices = kmb.PCIEDevice.discover()
                if not devices:
                    raise kmb.DeviceNotFoundError("Keembay PCIE device not found")
        except IndexError:
            logger.debug("All devices selected")
            devices = [*kmb.SingleUSBDevice.discover(), *kmb.PCIEDevice.discover()]
            if not devices:
                raise kmb.DeviceNotFoundError("Keembay device not found")

        if serialno:
            devices = [device for device in devices if getattr(device, "dev_id", None) == serialno]
            if not devices:
                raise kmb.DeviceNotFoundError("Keembay device not found")

        logger.debug("Download Started")
        for device in devices:
            result, args, returncode, stdout = device.download(fip, timeout=timeout)
            logger.debug("args: {}".format(args))
            logger.debug("returncode: {}".format(returncode))
            logger.debug("stdout: {}".format(stdout))
            logger.debug("result: {}".format(result))
            logger.success("Download completed for device: {} in {}s".format(device, result["total"]["time"]))
    
    except Exception as ex:
        logger.exception("{}: {}".format(ex.__class__.__name__, str(ex)))



@cli.command("devices", short_help='List available devices. Type "flashtool devices -h" for more')
@click.option("-v", "--verbose", "verbose", count=True)
@click.option("-d", '--device-type', type=click.Choice(('usb', 'pcie'), case_sensitive=False), multiple=True, help="Filter devices based on type: USB or PCIe")
def devices(verbose, device_type):
    """List available devices"""
    try:
        if verbose > 0:
            for handler in logger.root.handlers:
                handler.setLevel("DEBUG")
            logger.debug("VERBOSE On")
        try:
            if len(device_type) > 1:
                raise click.BadOptionUsage(device_type, "--device-type can be provided only once")
            if device_type[0] == "usb":
                logger.debug("USB devices selected")
                devices = kmb.SingleUSBDevice.discover()
                if not devices:
                    raise kmb.DeviceNotFoundError("Keembay USB device not found")
            else:
                logger.debug("PCIE devices selected")
                devices = kmb.PCIEDevice.discover()
                if not devices:
                    raise kmb.DeviceNotFoundError("Keembay PCIE device not found")
        except IndexError:
            logger.debug("All devices selected")
            devices = [*kmb.SingleUSBDevice.discover(), *kmb.PCIEDevice.discover()]
            if not devices:
                raise kmb.DeviceNotFoundError("Keembay device not found")

        for device in devices:
            logger.success(str(device))

    except Exception as ex:
        logger.exception("{}: {}".format(ex.__class__.__name__, str(ex)))
    

if __name__ == "__main__":
    cli()
