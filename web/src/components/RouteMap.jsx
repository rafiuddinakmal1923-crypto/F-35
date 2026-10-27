// Team route on a map (supervisor Dispatch page): base, numbered stops and the visiting order.
import L from "leaflet";
import { CircleMarker, MapContainer, Marker, Polyline, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const numbered = (n, joint) => L.divIcon({ className: "", iconSize: [26, 26], iconAnchor: [13, 13],
  html: `<span class="map-stop ${joint ? "joint" : ""}">${n}</span>` });

export default function RouteMap({ route }) {
  if (!route?.base) return <p className="muted">No base location on the roster for this team.</p>;
  const pts = [[route.base.lat, route.base.lon], ...route.stops.map((s) => [s.lat, s.lon])];
  const bounds = L.latLngBounds(pts).pad(0.25);
  return (
    <div className="route-map">
      <MapContainer bounds={bounds} style={{ height: "100%", width: "100%" }} scrollWheelZoom={false}>
        <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap contributors"
          referrerPolicy="strict-origin" />
        <Polyline positions={pts} pathOptions={{ color: "#2b5278", weight: 3, dashArray: "6 6" }} />
        <CircleMarker center={pts[0]} radius={8} pathOptions={{ color: "#0f3d5e", fillColor: "#f5b700", fillOpacity: 1 }}>
          <Tooltip>{route.team_name} base</Tooltip>
        </CircleMarker>
        {route.stops.map((s) => (
          <Marker key={s.case_id} position={[s.lat, s.lon]} icon={numbered(s.stop, s.joint_operation)}>
            <Tooltip>{`${s.stop}. ${s.case_id} · +${s.leg_km} km${s.joint_operation ? " · joint operation" : ""}`}</Tooltip>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
