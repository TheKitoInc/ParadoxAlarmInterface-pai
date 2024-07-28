#!/usr/bin/env python3

import argparse
import asyncio
import sys

from paradox.config import config as cfg
from paradox.lib.encodings import register_encodings


def check_version():
    if sys.version_info < (3, 6,):
        print(
            "You are using Python %s.%s, but PAI requires at least Python 3.6"
            % (sys.version_info[0], sys.version_info[1])
        )
        sys.exit(-1)


def get_logger():
    import logging
    from paradox.main import configure_logger
    logger = logging.getLogger("PAI").getChild(__name__)
    configure_logger(logger)
    return logger


def get_alarm():
    from paradox.paradox import Paradox
    return Paradox()


def init_timezone():
    import time
    time.tzset()


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        help="specify path to an alternative configuration file",
    )
    return parser


def load_config(args):
    if "config" in args and args.config is not None:
        import os

        config_file = os.path.abspath(args.config)
        cfg.load(config_file)
    else:
        cfg.load()


def start_interface_manager(alarm):
    from paradox.interfaces.interface_manager import InterfaceManager
    interface_manager = InterfaceManager(alarm, config=cfg)
    interface_manager.start()


def get_time_with_timezone():
    import pytz
    from datetime import datetime

    now = datetime.now().astimezone()

    if cfg.SYNC_TIME_TIMEZONE:
        tzinfo = pytz.timezone(cfg.SYNC_TIME_TIMEZONE)
        now = now.astimezone(tzinfo)

    return now


def get_time_dict():
    now = get_time_with_timezone()

    return dict(
        century=int(now.year / 100),
        year=int(now.year % 100),
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
    )


async def sync_time(alarm):

    if await alarm.connect():

        args = get_time_dict()

        reply = await alarm.send_wait(
            alarm.panel.get_message("SetTimeDate"),
            args,
            reply_expected=0x3,
            timeout=10
        )

        await alarm.disconnect()

        return reply is not None


def main():

    # Get the parser
    parser = get_parser()

    # Parse the arguments
    args = parser.parse_args()

    # Set the timezone
    init_timezone()

    # Load the configuration
    load_config(args)

    # Registering additional encodings
    register_encodings()

    # Create the alarm panel
    alarm = get_alarm()

    # Start the interface manager
    start_interface_manager(alarm)

    # Run the multithreaded loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sync_time(alarm))

    sys.exit(0)


if __name__ == "__main__":
    try:
        check_version()
        logger = get_logger()
        main()
    except ImportError as error:
        from paradox.lib import help
        help.import_error_help(error)
