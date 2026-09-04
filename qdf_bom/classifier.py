"""Connector classifier: maps arm bitmask to catalog part ID."""

from __future__ import annotations

from .catalog import PartsCatalog

# 12 socket directions (cardinal + diagonal), matching Quadro.exe geometry.
# Bits 0-5: cardinal (X,Y,Z); bits 6-11: diagonal (XY plane + XZ plane).
SOCKET_DIRS: dict[int, tuple[int, int, int]] = {
    0:  (1,  0,  0),   # +X
    1:  (-1,  0,  0),   # -X
    2:  (0,  1,  0),   # +Y
    3:  (0, -1,  0),   # -Y
    4:  (0,  0,  1),   # +Z
    5:  (0,  0, -1),   # -Z
    6:  (1,  1,  0),   # +X+Y
    7:  (1, -1,  0),   # +X-Y
    8:  (-1,  1,  0),   # -X+Y
    9:  (-1, -1,  0),   # -X-Y
    10: (1,  0,  1),   # +X+Z
    11: (-1,  0,  1),   # -X+Z
}


class ConnectorClassifier:
    """Classifies connector3 arm bitmasks to catalog part IDs."""

    def __init__(self, catalog: PartsCatalog) -> None:
        self._catalog = catalog

    def classify(self, arm_mask: int) -> str:
        """Return catalog part_id for the given arm bitmask, or 'connector_unknown'."""
        sockets = [i for i in range(12) if arm_mask & (1 << i)]
        if not sockets:
            return "connector_unknown"

        dirs = [SOCKET_DIRS.get(s, (0, 0, 0)) for s in sockets]
        arms = len(sockets)
        has_z = any(d[2] != 0 for d in dirs)

        # Space connectors (arms with Z component)
        if arms >= 3 and has_z:
            for c in self._catalog.connectors_by_arms(arms):
                if c.kind == "space":
                    return c.id

        # Planar connectors (all arms in one plane)
        if arms >= 3 and not has_z:
            for c in self._catalog.connectors_by_arms(arms):
                if c.kind == "planar":
                    return c.id

        # 2-arm connectors
        if arms == 2:
            d1, d2 = dirs
            opposite = d1 == tuple(-x for x in d2)
            if opposite:
                for c in self._catalog.connectors_by_arms(2):
                    if c.kind == "planar" and c.arm_angle == 180:
                        return c.id
            else:
                for c in self._catalog.connectors_by_arms(2):
                    if c.kind == "planar" and c.arm_angle == 90:
                        return c.id

        # Special connectors (catch-all)
        for c in self._catalog.connectors_by_arms(arms):
            if c.kind == "special":
                return c.id

        return "connector_unknown"
