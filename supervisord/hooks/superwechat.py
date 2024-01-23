#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# fork from https://github.com/slara/superslacker/blob/master/superslacker/superslacker.py
#
# A event listener meant to be subscribed to PROCESS_STATE_CHANGE
# events.  It will send wechat messages when processes that are children of
# supervisord transition unexpectedly to the EXITED state.

# A supervisor config snippet that tells supervisor to use this script
# as a listener is below.
#
# [eventlistener:superwechat]
# command=python superslacker
# events=PROCESS_STATE,TICK_60

"""
Usage: superslacker [-t token] [-c channel] [-n hostname] [-w webhook] [-e events]
Options:
  -h, --help            show this help message and exit
  -t TOKEN, --token=TOKEN
                        Wechat Token
  -w WEBHOOK, --webhook=WEBHOOK
                        Wechat WebHook URL
  -n HOSTNAME, --hostname=HOSTNAME
                        System Hostname
  -e EVENTS, --events=EVENTS
                        Supervisor process state event(s)
"""

import os
import sys
import socket
import requests
import logging
from itertools import groupby
from typing import List
from datetime import datetime, timedelta

from superlance.process_state_monitor import ProcessStateMonitor
from supervisor import childutils

logging.basicConfig(
    format="[%(asctime)s] - %(levelname)s - %(message)s", level=logging.INFO
)


class Wechat:
    WECHAT_TITLE_COLORS = {
        "green": "info",
        "gray": "comment",
        "red": "warning",
    }

    def __init__(self, token: str, webhook: str):
        self._token = token
        self._webhook = webhook
        logging.info(f"send notify to {webhook}?key={token}")

    def send(
        self,
        title: str,
        message: str,
        title_color: str = "green",
        mentioned_list: List = [],
    ):
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"""
# <font color="{self._color(title_color)}">{title}</font>
{message}
"""
            },
            "mentioned_list": mentioned_list,
        }

        res = requests.post(self._push_url(), json=payload)
        if res.status_code // 100 != 2:
            logging.error(
                f"failed to push payload: {payload} to wechat, status: {res.status_code}, text: {res.text}\n"
            )

    def _push_url(self):
        return f"{self._webhook}?key={self._token}"

    def _color(self, color: str):
        return self.WECHAT_TITLE_COLORS.get(color, "black")


class SuperWechat(ProcessStateMonitor):
    SUPERVISOR_EVENTS = (
        "STARTING",
        "RUNNING",
        "BACKOFF",
        "STOPPING",
        "FATAL",
        "EXITED",
        "STOPPED",
        "UNKNOWN",
    )

    EVENTS_WECHAT_COLORS = {
        "PROCESS_STATE_STARTING": "green",
        "PROCESS_STATE_RUNNING": "green",
        "PROCESS_STATE_BACKOFF": "gray",
        "PROCESS_STATE_STOPPING": "gray",
        "PROCESS_STATE_FATAL": "red",
        "PROCESS_STATE_EXITED": "red",
        "PROCESS_STATE_STOPPED": "red",
        "PROCESS_STATE_UNKNOWN": "gray",
    }

    @classmethod
    def _get_opt_parser(cls):
        from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

        parser = ArgumentParser(
            formatter_class=ArgumentDefaultsHelpFormatter,
            description="A event listener meant to be subscribed to PROCESS_STATE_CHANGE events",
        )

        parser.add_argument(
            "-t",
            "--token",
            default=os.getenv("BLOCKCHAIN_ETL_WECHAT_TOKEN"),
            help="Wechat Token",
        )
        parser.add_argument(
            "-w",
            "--webhook",
            default=os.getenv("BLOCKCHAIN_ETL_WECHAT_WEBHOOK"),
            help="Wechat WebHook URL",
        )
        parser.add_argument(
            "-n",
            "--hostname",
            default=socket.gethostname(),
            help="System Hostname",
        )
        parser.add_argument(
            "-e",
            "--events",
            default=",".join(cls.SUPERVISOR_EVENTS),
            help="Supervisor event(s). Can be any, some or all of {} as comma separated values".format(
                cls.SUPERVISOR_EVENTS
            ),
        )

        return parser

    @classmethod
    def create_from_cmd_line(cls):
        parser = cls._get_opt_parser()
        options = parser.parse_args()

        if "SUPERVISOR_SERVER_URL" not in os.environ:
            logging.error("Must run as a supervisor event listener\n")
            sys.exit(1)

        return cls(**options.__dict__)

    def __init__(self, **kwargs):
        ProcessStateMonitor.__init__(self, **kwargs)
        self.hostname = kwargs.get("hostname", None)
        self._wechat = Wechat(kwargs["token"], kwargs["webhook"])

        self.process_state_events = [
            "PROCESS_STATE_{}".format(e.strip().upper())
            for e in kwargs.get("events", "").split(",")
            if e in self.SUPERVISOR_EVENTS
        ]

    def get_process_state_change_msg(self, headers, payload):
        pheaders, _ = childutils.eventdata(payload + "\n")
        return "{hostname};{groupname}:{processname};{from_state};{event}".format(
            hostname=self.hostname, event=headers["eventname"], **pheaders
        )

    def send_batch_notification(self):
        batchedmsgs = [tuple(msg.rsplit(";")) for msg in self.batchmsgs]

        # convert to utc+8 datetime
        now = (datetime.utcnow() + timedelta(hours=8)).strftime(
            "%Y-%m-%d %H:%M:%S +0800"
        )

        for host_proc, msgs in groupby(batchedmsgs, key=lambda e: (e[0], e[1])):
            hostname, processname = host_proc
            events = [(e[2], e[3]) for e in msgs]
            message = f"""
> Hostname: `{hostname}`
> Time: <font color="info">{now}</font>
> Process: <font color="warning">{processname}</font>
> State: <font color="warning">{'-> '.join(e[0] for e in events)}</font>
> Event: {', '.join(e[1] for e in events)}
"""
            self._wechat.send(
                "Supervisor Event",
                message,
                title_color=self.EVENTS_WECHAT_COLORS[events[-1][1]],
            )


def main():
    superwechat = SuperWechat.create_from_cmd_line()
    superwechat.run()


if __name__ == "__main__":
    main()
