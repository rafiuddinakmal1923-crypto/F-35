// Feeder schematic (UI brief 3.2): an SVG one-line diagram of the zone. Transformer at the left, each
// phase a lane, branches as lines, premises as nodes in street order; node colour = risk score; the
// voltage-residual overlay shades the dip deepening towards the fitted tap. Hover or focus a node for
// premise ID, score and residual; click or Enter opens the premise drawer. No exact locations.
import { useMemo, useState } from "react";
import { t } from "../i18n.js";
import { layoutSchematic, schematicSummary } from "../lib/schematic.js";

function nodeFill(mix) {
  return `color-mix(in srgb, var(--accent) ${Math.round(mix * 100)}%, var(--neutral))`;
}

export default function FeederSchematic({ zone, suspects, voltage, minDropV, onOpen, highlight }) {
  const layout = useMemo(() => layoutSchematic({ suspects, voltage, minDropV, width: 760 }), [suspects, voltage, minDropV]);
  const [tip, setTip] = useState(null);
  if (!layout.nodes.length) return <p className="muted">{t("schematicEmpty")}</p>;
  const sum = schematicSummary(layout);
  const busTop = layout.lanes[0]?.top + 10;
  const busBottom = layout.lanes[layout.lanes.length - 1].top + layout.lanes[layout.lanes.length - 1].height - 10;
  const txX = 34;
  const busX = layout.left - 6;
  const show = (nd, e) => {
    const box = e.currentTarget.ownerSVGElement.getBoundingClientRect();
    const k = box.width / layout.width;
    setTip({ nd, left: nd.x * k, top: nd.y * k });
  };
  return (
    <div className="schematic-wrap schematic">
      <p className="sr-only">{t("schematicSummary", {
        zone, phases: sum.phases, branches: sum.branches, premises: sum.premises, top: sum.top?.id, score: sum.top?.score,
        dip: sum.deepest ? `${sum.deepest.id} ${sum.deepest.residual.toFixed(2)} V` : t("none"),
      })}</p>
      <svg viewBox={`0 0 ${layout.width} ${layout.height}`} role="group" aria-label={t("feederSchematic")}>
        {layout.lanes.map((lane) => (
          <g key={lane.phase}>
            <rect className="lane-bg" x={layout.left - 2} y={lane.top} width={layout.width - layout.left - 6} height={lane.height} rx="8" />
            <text className="lane-label" x={layout.left + 6} y={lane.top + 13}>{t("phase")} {lane.phase}</text>
            {lane.branches.map((b) => (
              <g key={b.name}>
                {layout.overlay && b.dip ? (
                  <path className="dip" d={`M${b.dip[0].x},${b.y} ${b.dip.map((d) => `L${d.x},${b.y + 2 + d.depth * 13}`).join(" ")} L${b.dip[b.dip.length - 1].x},${b.y} Z`} />
                ) : null}
                <line className="wire" x1={busX} x2={layout.width - 20} y1={b.y} y2={b.y} />
                <text className="branch-label" x={layout.left + 6} y={b.y - 5}>{b.name}</text>
                {b.tap ? (
                  <g>
                    <line className="tap" x1={b.tap.x} x2={b.tap.x} y1={b.y - 15} y2={b.y + 15} />
                    <text className="tap-label" x={b.tap.x + 4} y={b.y - 8}>{t("tapHere", { v: b.tap.dropV.toFixed(1) })}</text>
                  </g>
                ) : null}
                {b.nodes.map((nd) => {
                  const top = nd.id === layout.top?.id || nd.id === highlight;
                  const label = t("nodeLabel", { id: nd.id, score: nd.score, rank: nd.rank,
                    residual: nd.residual != null ? `${nd.residual.toFixed(2)} V` : t("notAvailable") });
                  return (
                    <g key={nd.id}>
                      {top ? <circle className="node-ring" cx={nd.x} cy={nd.y} r="10" /> : null}
                      <circle className={`node ${top ? "top" : ""}`} cx={nd.x} cy={nd.y} r={4 + nd.mix * 3} style={{ fill: nodeFill(nd.mix) }}
                        tabIndex={0} role="button" aria-label={label}
                        onMouseEnter={(e) => show(nd, e)} onMouseLeave={() => setTip(null)} onFocus={(e) => show(nd, e)} onBlur={() => setTip(null)}
                        onClick={() => onOpen?.(nd.id)} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onOpen?.(nd.id))} />
                    </g>
                  );
                })}
              </g>
            ))}
          </g>
        ))}
        <line className="bus" x1={busX} x2={busX} y1={busTop} y2={busBottom} />
        <line className="wire" x1={txX + 16} x2={busX} y1={(busTop + busBottom) / 2} y2={(busTop + busBottom) / 2} />
        <circle className="tx" cx={txX} cy={(busTop + busBottom) / 2 - 7} r="13" />
        <circle className="tx" cx={txX} cy={(busTop + busBottom) / 2 + 7} r="13" />
        <text className="tx-label" x={txX} y={(busTop + busBottom) / 2 + 36} textAnchor="middle">TX</text>
      </svg>
      {tip ? (
        <div className="schematic-tip" style={{ left: tip.left, top: tip.top }}>
          <b>{tip.nd.id}</b> · {t("riskScore")} {tip.nd.score} · #{tip.nd.rank}<br />
          {t("residual")}: {tip.nd.residual != null ? `${tip.nd.residual.toFixed(2)} V` : t("notAvailable")}
        </div>
      ) : null}
      <div className="row" style={{ marginTop: 6 }}>
        <span className="score-scale">{t("score")} 0 <i aria-hidden="true" /> 60+</span>
        {layout.overlay ? <span className="legend"><span className="area" style={{ "--c": "var(--accent-soft)" }}>{t("dipOverlay")}</span>
          <span className="dash" style={{ "--c": "var(--accent)" }}>{t("voltageLegendTap")}</span></span> : null}
      </div>
      {!layout.overlay ? <p className="notice warn" style={{ marginTop: 8 }}>{t("voltageOff")}</p> : null}
    </div>
  );
}
