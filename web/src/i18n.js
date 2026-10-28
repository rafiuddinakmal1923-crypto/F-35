// Interface labels in English and Bahasa Melayu (SRS 2.3, NFR-13).
import { useEffect, useState } from "react";

const LABELS = {
  en: {
    signIn: "Sign in", signOut: "Sign out", username: "Username", password: "Password",
    overview: "Network overview", cases: "Cases", dataManager: "Data manager", settings: "Settings", audit: "Audit log",
    models: "Models", assistant: "Assistant", field: "Inspector app",
    flaggedZones: "Leaking zones", gapPerDay: "Unexplained energy (kWh/day)", noBalance: "Zones without balance",
    openCases: "Open cases", zone: "Zone", district: "District", allDistricts: "All districts", date: "Date",
    gap: "Gap", uncertainty: "Uncertainty", flatness: "Flatness (CV)", gapStart: "Gap started", sinceStart: "since data start",
    priority: "Priority", largeLoad: "Large load", runDetection: "Run detection", runCaseJob: "Run case job",
    suspects: "Ranked suspects", score: "Risk score", reasons: "Reasons", confidence: "Confidence", tags: "Tags",
    energyBalance: "Energy balance", hourlyGap: "Hourly gap profile", voltageStrip: "Neighbour voltage", usage: "Use vs similar homes",
    accountEvents: "Account events", premise: "Premise", case: "Case", status: "Status", origin: "Origin",
    claim: "Claim", approve: "Approve", reject: "Reject", assign: "Assign", team: "Team", masked: "Personal details hidden",
    riskNote: "Scores rank risk. They are not a finding of theft; people decide after inspection.",
    myCases: "My cases", sync: "Sync", offline: "Offline", online: "Online", pending: "waiting to sync",
    outcome: "Outcome", notes: "Notes", photo: "Photo", submit: "Submit", safety: "Safety checklist",
    confirmed_theft: "Confirmed theft", false_alarm: "False alarm", inconclusive: "Inconclusive", no_access: "No access",
    routine: "Routine meter check", address: "Address", wipeNotice: "Case data on this phone is encrypted and wiped after sync or within 24 hours.",
    mainNav: "Main navigation",
  },
  ms: {
    signIn: "Log masuk", signOut: "Log keluar", username: "Nama pengguna", password: "Kata laluan",
    overview: "Gambaran rangkaian", cases: "Kes", dataManager: "Pengurus data", settings: "Tetapan", audit: "Log audit",
    models: "Model", assistant: "Pembantu", field: "Aplikasi pemeriksa",
    flaggedZones: "Zon bocor", gapPerDay: "Tenaga tidak dijelaskan (kWj/hari)", noBalance: "Zon tanpa imbangan",
    openCases: "Kes terbuka", zone: "Zon", district: "Daerah", allDistricts: "Semua daerah", date: "Tarikh",
    gap: "Jurang", uncertainty: "Ketidakpastian", flatness: "Kerataan (CV)", gapStart: "Jurang bermula", sinceStart: "sejak data bermula",
    priority: "Keutamaan", largeLoad: "Beban besar", runDetection: "Jalankan pengesanan", runCaseJob: "Jalankan tugas kes",
    suspects: "Senarai premis berisiko", score: "Skor risiko", reasons: "Sebab", confidence: "Keyakinan", tags: "Tag",
    energyBalance: "Imbangan tenaga", hourlyGap: "Profil jurang mengikut jam", voltageStrip: "Voltan jiran", usage: "Penggunaan berbanding rumah serupa",
    accountEvents: "Peristiwa akaun", premise: "Premis", case: "Kes", status: "Status", origin: "Asal",
    claim: "Tuntut", approve: "Lulus", reject: "Tolak", assign: "Tugaskan", team: "Pasukan", masked: "Butiran peribadi disembunyikan",
    riskNote: "Skor menilai risiko. Ia bukan penemuan kecurian; keputusan dibuat oleh manusia selepas pemeriksaan.",
    myCases: "Kes saya", sync: "Segerak", offline: "Luar talian", online: "Dalam talian", pending: "menunggu segerak",
    outcome: "Keputusan", notes: "Catatan", photo: "Foto", submit: "Hantar", safety: "Senarai semak keselamatan",
    confirmed_theft: "Kecurian disahkan", false_alarm: "Penggera palsu", inconclusive: "Tidak muktamad", no_access: "Tiada akses",
    routine: "Pemeriksaan meter rutin", address: "Alamat", wipeNotice: "Data kes di telefon ini disulitkan dan dipadam selepas segerak atau dalam 24 jam.",
    mainNav: "Navigasi utama",
  },
};

let lang = localStorage.getItem("vg_lang") || "en";
const subscribers = new Set();

export function t(key) {
  return LABELS[lang][key] ?? LABELS.en[key] ?? key;
}

export function setLang(next) {
  lang = next;
  try {
    localStorage.setItem("vg_lang", next);
  } catch {
    /* storage may be blocked */
  }
  subscribers.forEach((fn) => fn(next));
}

export function useLang() {
  const [current, setCurrent] = useState(lang);
  useEffect(() => {
    subscribers.add(setCurrent);
    return () => subscribers.delete(setCurrent);
  }, []);
  return current;
}
