// Premise page (FR-UI-03; UI brief 2.3): the same detail as the zone's drawer, on its own page.
// Personal details and exact location appear only on an open case, for that case's people.
import { useParams } from "react-router-dom";
import PremiseDetail from "../components/PremiseDetail.jsx";
import { t } from "../i18n.js";

export default function Premise() {
  const { id } = useParams();
  return (
    <div className="page">
      <div className="page-head"><h1>{t("premise")} {id}</h1></div>
      <PremiseDetail id={id} />
    </div>
  );
}
