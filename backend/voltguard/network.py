"""Radial low-voltage network model: per-phase load flow, technical losses and voltages.

A zone is one distribution transformer feeding a few LV branches. Each branch is a
chain of poles (nodes) at increasing distance from the transformer, and every premise
hangs off one node on one phase (SDD 5.2: real LV networks branch and run on three
phases). The same model is used twice:

* by the simulator, with the true loads (metered + hidden), to produce supply, losses
  and meter voltages;
* by the detection engine, with metered loads only, to give the engineering estimate
  of technical loss (FR-ZD-01) and the voltage each meter should see (FR-PS-02).

The solver is a backward/forward sweep, vectorised over time. It replaces pandapower
behind the same role (see DEVIATIONS.md): pandapower's balanced solver cannot model
single-phase connections, and its 3-phase solver is too slow for thousands of
half-hours per zone on a laptop.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

V_NOMINAL = 230.0  # phase-to-neutral, volts
A = np.exp(2j * np.pi / 3)  # 120 degree phase rotation


@dataclass
class LossParams:
    """Network parameters (SRS AS-8). Defaults describe a typical urban 415 V overhead ABC network."""

    r_phase_ohm_per_m: float = 0.000320   # 95 mm2 aluminium aerial bundled cable
    x_phase_ohm_per_m: float = 0.000085
    r_neutral_ohm_per_m: float = 0.000320
    r_service_ohm: float = 0.10           # service cable from pole to meter, phase + neutral
    kva: float = 500.0
    no_load_kw: float = 0.9               # transformer core loss
    full_load_copper_kw: float = 6.0      # transformer copper loss at rated load
    power_factor: float = 0.95

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: dict | None) -> "LossParams":
        params = cls()
        for key, value in (data or {}).items():
            if hasattr(params, key):
                setattr(params, key, float(value))
        return params


@dataclass
class ZoneNetwork:
    """Topology of one zone, built from premise branch/phase/distance (canonical `premise` table)."""

    node_parent: np.ndarray          # parent node index; node 0 is the transformer busbar
    node_branch: np.ndarray
    node_distance_m: np.ndarray
    seg_length_m: np.ndarray         # length of the segment from parent to node
    prem_node: np.ndarray            # node index per premise
    prem_phase: np.ndarray           # 0, 1, 2 (or -1 when unknown: spread across phases)
    params: LossParams = field(default_factory=LossParams)

    @property
    def n_nodes(self) -> int:
        return len(self.node_parent)

    @classmethod
    def from_premises(cls, branches, distances, phases, params: LossParams | None = None) -> "ZoneNetwork":
        branches = np.asarray(branches)
        distances = np.round(np.asarray(distances, dtype=float), 1)
        phases = np.asarray(phases, dtype=int)
        parents, node_branch, node_dist, seg_len = [-1], [""], [0.0], [0.0]
        prem_node = np.zeros(len(branches), dtype=int)
        for branch in sorted(set(branches.tolist())):
            mask = branches == branch
            positions = sorted(set(distances[mask].tolist()))
            prev_index, prev_dist = 0, 0.0
            for dist in positions:
                index = len(parents)
                parents.append(prev_index)
                node_branch.append(branch)
                node_dist.append(dist)
                seg_len.append(max(dist - prev_dist, 1.0))
                prem_node[mask & (distances == dist)] = index
                prev_index, prev_dist = index, dist
        return cls(
            node_parent=np.array(parents),
            node_branch=np.array(node_branch, dtype=object),
            node_distance_m=np.array(node_dist),
            seg_length_m=np.array(seg_len),
            prem_node=prem_node,
            prem_phase=phases,
            params=params or LossParams(),
        )

    def path_resistance(self) -> np.ndarray:
        """Phase resistance from the transformer to each node (ohm)."""
        r = np.zeros(self.n_nodes)
        for node in range(1, self.n_nodes):
            r[node] = r[self.node_parent[node]] + self.seg_length_m[node] * self.params.r_phase_ohm_per_m
        return r


@dataclass
class FlowResult:
    loss_kw: np.ndarray          # (T,) LV technical loss between the transformer meter and the customer meters
    prem_voltage: np.ndarray     # (n_premises, T) voltage at each meter
    supply_kw: np.ndarray        # (T,) power leaving the transformer, as its LV-side meter sees it
    transformer_loss_kw: np.ndarray  # (T,) core and copper loss, upstream of the transformer meter


def _phase_shares(phases: np.ndarray) -> np.ndarray:
    """(n_premises, 3) share of each premise's current carried on each phase."""
    shares = np.zeros((len(phases), 3))
    known = phases >= 0
    shares[np.where(known)[0], phases[known]] = 1.0
    shares[~known] = 1.0 / 3.0
    return shares


def solve(net: ZoneNetwork, load_kw: np.ndarray, v_tx: np.ndarray | float = V_NOMINAL, iterations: int = 3) -> FlowResult:
    """Backward/forward sweep for every interval at once.

    load_kw: (n_premises, T) average real power per interval at each premise.
    v_tx:    transformer LV busbar voltage per interval (scalar or (T,)).
    """
    p = net.params
    load_kw = np.atleast_2d(np.asarray(load_kw, dtype=float))
    n_prem, n_t = load_kw.shape
    v_tx = np.broadcast_to(np.asarray(v_tx, dtype=float), (n_t,))
    shares = _phase_shares(net.prem_phase)
    sin_phi = np.sqrt(max(1.0 - p.power_factor**2, 0.0))
    seg_r = net.seg_length_m * p.r_phase_ohm_per_m
    seg_x = net.seg_length_m * p.x_phase_ohm_per_m
    seg_rn = net.seg_length_m * p.r_neutral_ohm_per_m

    node_v = np.repeat(v_tx[None, None, :], net.n_nodes, axis=0).repeat(3, axis=1)  # (nodes, 3, T)
    prem_v = np.repeat(v_tx[None, :], n_prem, axis=0)
    for _ in range(iterations):
        # Premise current (A) from its power and its own voltage; split across phases.
        prem_i = load_kw * 1000.0 / (np.maximum(prem_v, 150.0) * p.power_factor)
        node_i = np.zeros((net.n_nodes, 3, n_t))
        for phase in range(3):
            np.add.at(node_i[:, phase, :], net.prem_node, prem_i * shares[:, phase][:, None])
        seg_i = node_i.copy()
        for node in range(net.n_nodes - 1, 0, -1):
            seg_i[net.node_parent[node]] += seg_i[node]
        node_v[0] = v_tx[None, :]
        for node in range(1, net.n_nodes):
            drop = seg_i[node] * (seg_r[node] * p.power_factor + seg_x[node] * sin_phi)
            node_v[node] = node_v[net.node_parent[node]] - drop
        # Meter voltage = pole voltage minus the drop on the premise's own service cable.
        pole_v = np.einsum("pk,pkt->pt", shares, node_v[net.prem_node])
        prem_v = pole_v - prem_i * p.r_service_ohm

    phase_loss = (seg_i[1:] ** 2 * seg_r[1:, None, None]).sum(axis=(0, 1))
    neutral_i = np.abs(seg_i[1:, 0] + A * seg_i[1:, 1] + A**2 * seg_i[1:, 2])
    neutral_loss = (neutral_i**2 * seg_rn[1:, None]).sum(axis=0)
    service_loss = (prem_i**2 * p.r_service_ohm).sum(axis=0)
    lv_loss_kw = (phase_loss + neutral_loss + service_loss) / 1000.0
    supply_kw = load_kw.sum(axis=0) + lv_loss_kw
    loading = supply_kw / (p.kva * p.power_factor)
    tx_loss_kw = p.no_load_kw + p.full_load_copper_kw * loading**2
    return FlowResult(loss_kw=lv_loss_kw, prem_voltage=prem_v, supply_kw=supply_kw, transformer_loss_kw=tx_loss_kw)
