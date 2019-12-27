import os
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Set,
)

import yaml

from .base import AbstractSnapshotSerializer


if TYPE_CHECKING:
    from syrupy.types import SerializableData


class YAMLSnapshotSerializer(AbstractSnapshotSerializer):
    @property
    def file_extension(self) -> str:
        return "yaml"

    def discover_snapshots(self, filepath: str) -> Set[str]:
        return set(self._read_raw_file(filepath).keys())

    def _read_snapshot_from_file(
        self, snapshot_file: str, snapshot_name: str
    ) -> "SerializableData":
        raw_snapshots = self._read_raw_file(snapshot_file)
        return raw_snapshots.get(snapshot_name, None)

    def _write_snapshot_to_file(
        self, snapshot_file: str, snapshot_name: str, data: "SerializableData"
    ) -> None:
        snapshots = self.__read_file(snapshot_file)
        snapshots[snapshot_name] = snapshots.get(snapshot_name, {})
        snapshots[snapshot_name][self._data_key] = data
        self.__write_file(snapshot_file, snapshots)

    def delete_snapshots_from_file(
        self, snapshot_file: str, snapshot_names: Set[str]
    ) -> None:
        snapshots = self.__read_file(snapshot_file)
        for name in snapshot_names:
            snapshots.pop(name, None)

        if snapshots:
            self.__write_file(snapshot_file, snapshots)
        else:
            os.remove(snapshot_file)

    def serialize(self, data: "SerializableData") -> str:
        """
        Returns the serialized form of 'data' to be compared
        with the snapshot data written to disk.
        """
        return str(yaml.dump({self._data_key: data}, allow_unicode=True))

    @property
    def _data_key(self) -> str:
        return "data"

    def __write_file(self, filepath: str, data: "SerializableData") -> None:
        """
        Writes the snapshot data into the snapshot file that be read later.
        """
        with open(filepath, "w") as f:
            yaml.dump(data, f, allow_unicode=True)

    def __read_file(self, filepath: str) -> Any:
        """
        Read the snapshot data from the snapshot file into a python instance.
        """
        try:
            with open(filepath, "r") as f:
                return yaml.load(f, Loader=yaml.FullLoader) or {}
        except FileNotFoundError:
            pass
        return {}

    def _read_raw_file(self, filepath: str) -> Dict[str, str]:
        """
        Read the raw snapshot data (str) from the snapshot file into a dict
        of snapshot name to raw data. This does not attempt any deserialization
        of the snapshot data.
        """
        snapshots = {}
        try:
            with open(filepath, "r") as f:
                test_name = None
                for line in f:
                    if line[0] not in (" ", "\n") and line[-2] == ":":
                        test_name = line[:-2]  # newline & colon
                        snapshots[test_name] = ""
                    elif test_name is not None:
                        offset = min(len(line) - 1, 2)
                        snapshots[test_name] += line[offset:]
        except FileNotFoundError:
            pass

        return snapshots
