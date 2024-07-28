#!/usr/bin/env python3

import asyncio
import sys

from paradox.config import config as cfg
from paradox.lib.encodings import register_encodings

from common import check_version, get_logger, get_alarm, init_timezone, get_parser, load_config, start_interface_manager


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
