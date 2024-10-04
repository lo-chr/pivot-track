from pathlib import Path
from typing import List, Union

from common_osint_model import Host, Domain
from pivot_track.lib.connectors import NotificationConnector
from pivot_track.lib.track import TrackingDefinition

import logging

logger = logging.getLogger(__name__)


class FileConnector(NotificationConnector):
    file_path: Path = None

    def __init__(self, file_path: Path) -> None:
        if file_path.exists and file_path.is_file:
            self.file_path = file_path
        else:
            raise FileNotFoundError

    def _com_to_strings(self, notify_items: List[Union[Host, Domain]]) -> list:
        """This function transfers a set of Common OSINT Model items to a list of identifiable strings (hostnames and IPs for now)."""
        notify_strings = list()
        for element in notify_items:
            if isinstance(element, Host):
                notify_strings.append(element.ip)
            elif isinstance(element, Domain):
                notify_strings.append(element.domain)
        return notify_strings

    def notify(
        self,
        definition: TrackingDefinition = None,
        notify_items: List[Union[Host, Domain]] = None,
    ):
        logger.debug(
            f'Got {len(notify_items)} for last run of  "{str(definition.uuid)}".'
        )
        notification = "🚨🚨🚨 New Tracking Results"
        if definition is not None:
            notification += f' for "{definition.title}" ({str(definition.uuid)}):\n'
        if notify_items is not None and len(notify_items) > 0:
            logger.info(f"Appending notification for {len(notify_items)} items.")
            notification += f"{'\n'.join([notify_string for notify_string in self._com_to_strings(notify_items)])}"
        try:
            with open(self.file_path, "a") as out_file:
                out_file.write(f"{notification}\n\n")
        except FileNotFoundError:
            logger.error(
                f"Could not write to notification output: {self.file_path.absolute().as_posix()}"
            )
