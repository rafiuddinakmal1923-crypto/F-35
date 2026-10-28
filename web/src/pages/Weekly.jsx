// Weekly summary (managers and supervisors): the self-explanatory report for the region, in the interface
// language (English or Bahasa Melayu), exactly as printed to PDF; download it or send it to Telegram / the
// in-app chat. Every sentence on the report is rule-based and every figure comes from the database.
// The report itself is the server-rendered page (/weekly/html); this page only frames it.
import { Download, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { post, request } from "../api.js";
import { ErrorBox } from "../components/Common.jsx";
import { Skeleton } from "../components/ui.jsx";
import { t, useLang } from "../i18n.js";
import { LinkTelegram } from "./Dispatch.jsx";

export default function Weekly() {
  const lang = useLang();
  const [page, setPage] = useState(null);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const frame = useRef(null);

  useEffect(() => {
    let live = true;
    setPage(null);
    request(`/weekly/html?lang=${lang}`, { raw: true })
      .then((res) => res.text())
      .then((html) => live && setPage(html))
      .catch((e) => live && setError(e));
    return () => { live = false; };
  }, [lang]);

  function fit() {
    // Same-origin srcdoc without scripts: the page can read the report's height and show it in full.
    const doc = frame.current?.contentDocument;
    if (doc) frame.current.style.height = `${doc.documentElement.scrollHeight + 24}px`;
  }

  async function download() {
    setError(null);
    try {
      const res = await request(`/weekly/pdf?lang=${lang}`, { raw: true });
      const name = (res.headers.get("content-disposition") || "").match(/filename="([^"]+)"/)?.[1] || "voltguard-weekly.pdf";
      const url = URL.createObjectURL(await res.blob());
      Object.assign(document.createElement("a"), { href: url, download: name }).click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e);
    }
  }

  async function send() {
    setError(null);
    try {
      const r = await post(`/weekly/send?lang=${lang}`);
      setMessage(r.channel === "telegram" ? t("weeklySentTelegram") : t("weeklySentApp"));
    } catch (e) {
      setError(e);
    }
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>{t("weekly")}</h1>
          <span className="sub">{t("weeklyNote")}</span>
        </div>
        <div className="row">
          <button onClick={send} disabled={!page}><Send size={15} aria-hidden="true" />{t("weeklySend")}</button>
          <button className="primary" onClick={download} disabled={!page}><Download size={15} aria-hidden="true" />{t("weeklyDownload")}</button>
        </div>
      </div>
      <ErrorBox error={error} />
      {message ? <div className="notice ok">{message}</div> : null}
      <div className="report-frame">
        {page === null && !error ? <div style={{ width: "100%", maxWidth: 900 }}><Skeleton lines={8} block /></div> : null}
        {page !== null ? <iframe ref={frame} title={t("weekly")} srcDoc={page} sandbox="allow-same-origin" onLoad={fit} /> : null}
      </div>
      <div style={{ maxWidth: 480 }}><LinkTelegram /></div>
    </div>
  );
}
