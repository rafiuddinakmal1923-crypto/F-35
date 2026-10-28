"""Weekly report: rule-based sentences, charts, HTML and PDF (English or Bahasa Melayu).

Every sentence comes from fixed rules on the figures `digest.build` gathered, never from the
language model, so each statement can be traced to a number on the page. Every chart has a title
with units, a legend, a "what this shows / how to read it" box and a one-sentence takeaway.
Colour is never the only signal: bars carry value labels, whiskers and threshold marks.
"""

from __future__ import annotations

import html
import re
from datetime import date, datetime

from voltguard import pdf
from voltguard.agents import guardrails

PREMISE_ID = re.compile(r"\bP-[A-Z]{3}-\d{3}-\d{3}\b")
MONTHS = {"en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
          "ms": ["Jan", "Feb", "Mac", "Apr", "Mei", "Jun", "Jul", "Ogo", "Sep", "Okt", "Nov", "Dis"]}

T = {
    "en": {
        "title": "VoltGuard weekly summary · region {r}",
        "meta": "Report {id} · generated {when} MYT · for revenue-protection managers, region {r}",
        "meter_data": "Meter data", "field_work": "Field work",
        "banner_sim": "Simulated data (R0): not TNB data. Figures show how the system works, not real network performance.",
        "one_para": "This week in one paragraph.", "action": "Action {n}",
        "s1": "Unexplained energy in region {r} averaged {avg} kWh a day, {chg} than the week before, so the leak is {trend}.",
        "s1_nochange": "Unexplained energy in region {r} averaged {avg} kWh a day; there is no earlier week to compare with.",
        "s1_none": "There are no meter data for this week, so unexplained energy cannot be measured.",
        "lower": "{p} lower", "higher": "{p} higher",
        "trend_steady": "steady, not growing", "trend_rising": "growing", "trend_falling": "shrinking",
        "s2": "{n} of {m} zones are flagged; {top} alone accounts for {share} of the unexplained energy",
        "s2_flat": " and draws a flat 24/7 load typical of mining rigs",
        "s2_none": "No zone is flagged this week.",
        "s3_idle": "No cases were opened or closed this week and no inspections were recorded.",
        "s3": "{o} case(s) were opened and {c} closed this week; {v} inspection(s) were recorded.",
        "s3_novisit": "{o} case(s) were opened and {c} closed this week; no inspections were recorded yet.",
        "h_key": "1 · Key figures",
        "k_flagged": "Flagged zones", "k_flagged_d": "Unexplained energy above the flag rule for {k} days in a row",
        "k_of": "of {m}", "k_same": "no change vs last week", "k_diff": "{s} vs last week ({p} then)",
        "k_kwh": "Unexplained kWh per day", "k_kwh_d": "Average over the meter week, all zones with a transformer meter",
        "k_kwh_c": "{s} vs {p} the week before", "k_month": "kWh a month at this level",
        "k_month_d": "{avg} × 30 days. Value in RM: {rm}", "k_month_c": "estimate, see section 3",
        "k_cases": "Cases opened / closed", "k_cases_d": "During the field-work week", "k_cases_c": "{n} closed in total",
        "k_overdue": "Overdue cases", "k_overdue_d": "Assigned and not visited within {h} h",
        "k_rep": "Reports exported · open alerts", "k_rep_d": "Reports after both approvals · unacknowledged data or model alerts",
        "k_rep_c": "{n} new alert(s) this week", "k_none": "no earlier week",
        "why_title": "Why two dates?",
        "why": "Meter data reach VoltGuard daily, so energy figures cover the latest full week of readings ({e}). Cases and inspections are counted over the last 7 calendar days ({w}).",
        "why_sim": " In this prototype the simulated meter data end on {last}, which is why the two windows are {n} days apart; with live TNB data they would be one or two days apart.",
        "why_late": " Meter data have not arrived since {last} ({n} days ago): check the data feed before relying on this week's energy figures.",
        "h_energy": "2 · Is energy still going missing?",
        "c_energy": "Unexplained energy per day, whole region, last 14 days (kWh/day)",
        "l_series": "unexplained energy", "l_band": "margin of error ±{m} kWh", "l_avg": "weekly average", "l_week": "start of this week",
        "prev_avg": "prev. week avg {v}", "this_avg": "this week avg {v}", "week_starts": "week starts", "axis_kwh": "kWh/day",
        "read_energy": "<b>What this shows:</b> for each day, energy the transformers supplied minus what customers' meters recorded, minus the estimate for monthly-read meters and the expected technical loss in cables and transformers. <b>How to read it:</b> a line inside the shaded band could be measurement error; a line well above it means energy is leaving the network unrecorded.",
        "take": "Takeaway:",
        "t_none": "No meter data for this week, so there is nothing to compare.",
        "t_inside": "Unexplained energy averaged {avg} kWh a day, inside the margin of error (±{m} kWh): it could be measurement error, so nothing stands out this week.",
        "t_steady": "About {avg} kWh a day goes unrecorded, well above the margin of error (±{m} kWh) and steady compared with the week before ({chg}).",
        "t_rising": "About {avg} kWh a day goes unrecorded, above the margin of error (±{m} kWh) and rising: {chg} on the week before. Start with the zones in section 3.",
        "t_falling": "About {avg} kWh a day goes unrecorded, above the margin of error (±{m} kWh) but falling: {chg} on the week before, which may mean a tap was removed or inspections are working.",
        "t_flat": " A steady, flat leak points to a continuous load, not a one-off.",
        "h_where": "3 · Where is it going missing?",
        "c_zones": "Unexplained energy per zone this week (kWh/day)",
        "l_flagged": "flagged zone", "l_ok": "not flagged", "l_margin": "margin of error", "l_thr": "flag threshold for that zone",
        "read_zones": "<b>How to read it:</b> a zone is flagged when its unexplained energy stays above its threshold mark plus the margin of error for {k} days in a row. Thresholds differ by zone because they scale with the energy each transformer supplies ({p} of supply, or {g} kWh a day, whichever is larger).",
        "th_zone": "Zone", "th_district": "District", "th_kwh": "kWh/day", "th_pct": "% of supply", "th_margin": "Margin", "th_thr": "Threshold",
        "th_status": "Status", "th_started": "Leak started", "th_pattern": "Daily pattern", "th_priority": "Priority", "th_open": "Open cases",
        "st_flagged": "Flagged", "st_ok": "Not flagged", "since_start": "since data start", "flat": "flat 24/7 (CV {cv})", "varies": "varies by hour",
        "large": "Large load", "normal": "Normal", "dash": "–",
        "t_priority": "{z} is the priority: the largest flagged leak{large}{flat}.",
        "t_priority_large": ", above {p} of its supply", "t_priority_flat": ", flat around the clock",
        "t_inside_margin": " {z}'s {g} kWh a day sits inside its margin of error, so it is not flagged.",
        "t_below_thr": " {z}'s {g} kWh a day is above its margin of error but below its flag threshold, so it is not flagged.",
        "t_no_flag": "No zone is flagged: every zone's unexplained energy stays below its threshold plus margin of error.",
        "no_balance_h": "Zones without a transformer meter (no balance available)",
        "no_balance": "{zones}: no transformer meter, so no energy balance can be drawn; their premises are ranked on usage patterns only, at low confidence. Candidates for a transformer meter.",
        "h_value": "Value at risk (estimate)",
        "value": "{avg} kWh a day × 30 days ≈ <b>{month} kWh a month</b>. In RM: {rm}. This counts all unexplained energy, including the margin of error, so it is an upper estimate; counting only energy above each zone's threshold gives about <b>{above} kWh a month</b>{rm_above}.",
        "rm_unset": "[TNB tariff per kWh: to be supplied]", "rm_set": "about RM {v} a month (estimate, tariff RM {t}/kWh{src})",
        "rm_above": " (about RM {v})",
        "h_hits": "4 · Are inspections finding theft?",
        "c_hits": "Hit rate so far, with 95% ranges (% of inspections)",
        "l_model": "model-ranked inspections", "l_random": "random routine checks", "l_range": "95% range",
        "model_ranked": "Model-ranked", "random_sample": "Random sample",
        "hit_label": "{p} ({c} of {n}; range {lo}–{hi}%)",
        "th_insp": "Inspections", "th_lab": "Labelled", "th_conf": "Confirmed theft", "th_rate": "Hit rate", "th_range": "95% range", "th_means": "What it means",
        "means_model": "Homes chosen by VoltGuard's ranking", "means_random": "Homes picked at random in flagged zones: the fair baseline",
        "read_hits": "<b>How to read it:</b> the hit rate is the share of inspected homes where theft was confirmed. Random routine checks show what you would find without the model, so the gap between the two rows is the model's value. The 95% range shows how much the rate could move by chance with so few inspections.",
        "h_none": "No inspection has been labelled yet, so there is no hit rate to compare.",
        "h_only_model": "{a} of {n} model-ranked inspections found theft; there are no random routine checks yet to compare against.",
        "h_only_random": "{b} of random routine checks found theft; no model-ranked inspection is labelled yet.",
        "h_overlap": "Model-ranked inspections look {cmp} ({a} vs {b}), but the ranges overlap: {n} random check(s) are too few to prove a difference.",
        "h_apart": "Model-ranked inspections find theft more often than random checks ({a} vs {b}), and the ranges do not overlap, so the difference is unlikely to be chance.",
        "h_apart_worse": "Model-ranked inspections find theft less often than random checks ({a} vs {b}), and the ranges do not overlap: review the model's weights and thresholds.",
        "cmp_better": "better", "cmp_worse": "worse", "cmp_same": "similar",
        "h_no_week": " No inspections were recorded this week.",
        "h_synthetic": " Outcomes so far come from simulated cases, so they show how the measurement works, not real performance.",
        "outcomes_h": "Inspection outcomes", "th_outcome": "Outcome", "th_week": "This week", "th_all": "All time",
        "o_confirmed_theft": "Confirmed theft", "o_false_alarm": "False alarm", "o_inconclusive": "Inconclusive",
        "o_no_access": "No access (not used for learning)",
        "status_h": "Cases by status now", "th_status_name": "Status", "th_cases": "Cases", "th_meaning": "Meaning",
        "s_new": "New", "s_assigned": "Assigned", "s_visited": "Visited", "s_reporting": "Reporting", "s_closed": "Closed",
        "m_new": "Waiting for the supervisor", "m_assigned": "Team sent", "m_visited": "Outcome recorded",
        "m_reporting": "Theft confirmed, report in approval", "m_closed": "Finished",
        "h_trust": "5 · Can these figures be trusted?",
        "quality_h": "Data quality (meter week)", "q_complete": "Meter-days with ≥ 90% of readings", "q_monthly": "Meters read monthly (estimated daily)",
        "q_no_dtm": "Zones without a transformer meter", "q_dup": "Duplicate or out-of-order readings fixed",
        "q_dup_v": "not recorded for this data source", "q_fallbacks": "Fallbacks in use", "q_none": "none",
        "f_AS-2": "no transformer meter in {n} zone(s): listed without a balance (AS-2)",
        "f_AS-3-simulated": "voltage is simulated (AS-3)", "f_AS-3": "no voltage data: voltage locator off (AS-3)",
        "f_AS-7": "phase or branch missing: voltage evidence at low confidence (AS-7)",
        "f_AS-8": "network parameters missing: technical loss compared with similar zones (AS-8)",
        "f_AS-9": "no solar registrations: rooftop solar recognised from its daytime pattern only (AS-9)",
        "model_h": "Model in use", "m_scoring": "Scoring version", "m_retrained": "Last retrained",
        "m_retrained_v": "{at}, version {v}; {n} labels available", "m_not_retrained": "not retrained yet; {n} labels available",
        "m_alerts": "Data or drift alerts this week", "m_thresholds": "Thresholds",
        "m_thresholds_v": "{p} of supply or {g} kWh/day, {k} days; large load above {l}",
        "assume_h": "Assumptions and limits",
        "a_sim": "<b>Simulated data.</b> This prototype runs on a simulated region built from public household profiles; voltages come from a network model, because open data hold energy readings only.",
        "a_loss": "<b>Technical loss is estimated</b> by an engineering model of cables and transformers; its error is part of the margin of error.",
        "a_monthly": "<b>Monthly-read meters</b> ({p} of meters) are spread across the month using similar homes' daily patterns; this widens the margin.",
        "a_small": "<b>Small leaks can hide:</b> a tap of about 1% of a zone's supply sits inside the margin and will not flag the zone.",
        "a_rank": "<b>Scores rank risk;</b> they are not findings of theft. People decide after inspection.",
        "a_tariff": "<b>Tariff not yet supplied,</b> so value at risk is shown in kWh only.",
        "a_zone": "<b>Zone-level only:</b> this report holds no premise IDs, names or addresses, and covers region {r} only.",
        "steps_h": "6 · Recommended next steps",
        "steps_note": "Steps are generated from fixed rules on the figures above, not written by the language model.",
        "steps_none": "No action stands out from this week's figures.",
        "n_case_job": "Supervisor: run the case job for {zones}; their top suspects have no open case.",
        "n_case_job_joint": "Supervisor: run the case job for {zones}; suggest a joint operation with police for {large} (large, flat load).",
        "n_joint": "Supervisor: suggest a joint operation with police for {large} (large load above {p} of supply).",
        "n_overdue": "Supervisor: follow up {n} overdue case(s) assigned more than {h} h ago.",
        "n_alerts": "Data team: review {n} open data or model alert(s).",
        "n_random": "Manager: add random routine checks: {have} so far is too few to measure the model's real hit rate (aim for at least {min}).",
        "n_tariff": "Data team: confirm the TNB tariff so value at risk can be shown in RM.",
        "glossary_h": "Glossary",
        "g": [("Unexplained energy", "Supplied by the transformer minus metered use, minus estimates for monthly-read meters and expected technical loss."),
              ("Margin of error (u)", "How far unexplained energy can stray by chance, from meter accuracy, monthly-read estimates and the loss model."),
              ("Flagged zone", "Unexplained energy above the threshold plus the margin of error for 7 days in a row."),
              ("Flat 24/7", "The leak hardly changes across the day (coefficient of variation below 0.2), typical of mining rigs."),
              ("Hit rate", "Share of inspected homes where theft was confirmed."),
              ("Random routine check", "An inspection of a home picked at random in a flagged zone, used as the fair baseline.")],
        "foot": "VoltGuard AI · R0 prototype · Team F-35 · region {r} · report {id} · data: {data} · scoring: {model} · scores rank risk; people decide after inspection.",
        "data_sim": "simulated", "data_upload": "uploaded",
        "page_label": "page {page} of {total}",
        "headline": "{n} flagged zone(s), {kwh} kWh/day unexplained{chg}; {o} case(s) opened, {c} closed, {od} overdue{hr}.{step}",
        "hl_chg": " ({s} vs the week before)", "hl_hr": "; model-ranked hit rate {p}", "hl_step": " Next: {s}",
        "empty": "No detection results yet.",
    },
    "ms": {
        "title": "Ringkasan mingguan VoltGuard · wilayah {r}",
        "meta": "Laporan {id} · dijana {when} MYT · untuk pengurus perlindungan hasil, wilayah {r}",
        "meter_data": "Data meter", "field_work": "Kerja lapangan",
        "banner_sim": "Data simulasi (R0): bukan data TNB. Angka menunjukkan cara sistem berfungsi, bukan prestasi rangkaian sebenar.",
        "one_para": "Minggu ini dalam satu perenggan.", "action": "Tindakan {n}",
        "s1": "Tenaga yang tidak dapat dijelaskan di wilayah {r} purata {avg} kWh sehari, {chg} berbanding minggu sebelumnya, jadi kebocoran itu {trend}.",
        "s1_nochange": "Tenaga yang tidak dapat dijelaskan di wilayah {r} purata {avg} kWh sehari; tiada minggu terdahulu untuk dibandingkan.",
        "s1_none": "Tiada data meter untuk minggu ini, jadi tenaga yang tidak dapat dijelaskan tidak boleh diukur.",
        "lower": "{p} lebih rendah", "higher": "{p} lebih tinggi",
        "trend_steady": "stabil, tidak bertambah", "trend_rising": "bertambah", "trend_falling": "berkurang",
        "s2": "{n} daripada {m} zon ditandakan; {top} sahaja menyumbang {share} daripada tenaga yang tidak dapat dijelaskan",
        "s2_flat": " dan menarik beban rata 24/7 yang lazim bagi rig perlombongan",
        "s2_none": "Tiada zon yang ditandakan minggu ini.",
        "s3_idle": "Tiada kes dibuka atau ditutup minggu ini dan tiada pemeriksaan direkodkan.",
        "s3": "{o} kes dibuka dan {c} ditutup minggu ini; {v} pemeriksaan direkodkan.",
        "s3_novisit": "{o} kes dibuka dan {c} ditutup minggu ini; belum ada pemeriksaan direkodkan.",
        "h_key": "1 · Angka utama",
        "k_flagged": "Zon ditandakan", "k_flagged_d": "Tenaga yang tidak dapat dijelaskan melepasi peraturan tanda selama {k} hari berturut-turut",
        "k_of": "daripada {m}", "k_same": "tiada perubahan berbanding minggu lalu", "k_diff": "{s} berbanding minggu lalu ({p} ketika itu)",
        "k_kwh": "kWh tidak dapat dijelaskan sehari", "k_kwh_d": "Purata minggu meter, semua zon yang ada meter pengubah",
        "k_kwh_c": "{s} berbanding {p} minggu sebelumnya", "k_month": "kWh sebulan pada tahap ini",
        "k_month_d": "{avg} × 30 hari. Nilai dalam RM: {rm}", "k_month_c": "anggaran, lihat bahagian 3",
        "k_cases": "Kes dibuka / ditutup", "k_cases_d": "Dalam minggu kerja lapangan", "k_cases_c": "{n} ditutup kesemuanya",
        "k_overdue": "Kes tertunggak", "k_overdue_d": "Ditugaskan dan tidak dilawati dalam {h} jam",
        "k_rep": "Laporan dieksport · amaran terbuka", "k_rep_d": "Laporan selepas kedua-dua kelulusan · amaran data atau model yang belum diakui",
        "k_rep_c": "{n} amaran baharu minggu ini", "k_none": "tiada minggu terdahulu",
        "why_title": "Mengapa dua tarikh?",
        "why": "Data meter sampai ke VoltGuard setiap hari, jadi angka tenaga meliputi minggu bacaan penuh yang terkini ({e}). Kes dan pemeriksaan dikira dalam 7 hari kalendar terakhir ({w}).",
        "why_sim": " Dalam prototaip ini data meter simulasi berakhir pada {last}, sebab itu kedua-dua tempoh berjarak {n} hari; dengan data TNB sebenar jaraknya satu atau dua hari sahaja.",
        "why_late": " Data meter belum sampai sejak {last} ({n} hari lalu): semak suapan data sebelum bergantung pada angka tenaga minggu ini.",
        "h_energy": "2 · Adakah tenaga masih hilang?",
        "c_energy": "Tenaga yang tidak dapat dijelaskan sehari, seluruh wilayah, 14 hari terakhir (kWh/hari)",
        "l_series": "tenaga tidak dapat dijelaskan", "l_band": "margin ralat ±{m} kWh", "l_avg": "purata mingguan", "l_week": "permulaan minggu ini",
        "prev_avg": "purata minggu lalu {v}", "this_avg": "purata minggu ini {v}", "week_starts": "minggu bermula", "axis_kwh": "kWh/hari",
        "read_energy": "<b>Apa yang ditunjukkan:</b> bagi setiap hari, tenaga yang dibekalkan pengubah tolak tenaga yang direkodkan meter pelanggan, tolak anggaran bagi meter bacaan bulanan dan kehilangan teknikal yang dijangka dalam kabel dan pengubah. <b>Cara membacanya:</b> garisan di dalam jalur berlorek mungkin ralat pengukuran; garisan jauh di atasnya bermakna tenaga keluar dari rangkaian tanpa direkodkan.",
        "take": "Rumusan:",
        "t_none": "Tiada data meter untuk minggu ini, jadi tiada apa untuk dibandingkan.",
        "t_inside": "Tenaga yang tidak dapat dijelaskan purata {avg} kWh sehari, di dalam margin ralat (±{m} kWh): ia mungkin ralat pengukuran, jadi tiada yang menonjol minggu ini.",
        "t_steady": "Kira-kira {avg} kWh sehari tidak direkodkan, jauh di atas margin ralat (±{m} kWh) dan stabil berbanding minggu sebelumnya ({chg}).",
        "t_rising": "Kira-kira {avg} kWh sehari tidak direkodkan, di atas margin ralat (±{m} kWh) dan meningkat: {chg} berbanding minggu sebelumnya. Mulakan dengan zon di bahagian 3.",
        "t_falling": "Kira-kira {avg} kWh sehari tidak direkodkan, di atas margin ralat (±{m} kWh) tetapi menurun: {chg} berbanding minggu sebelumnya, mungkin kerana sambungan haram telah ditanggalkan atau pemeriksaan berkesan.",
        "t_flat": " Kebocoran yang stabil dan rata menunjukkan beban berterusan, bukan kejadian sekali sahaja.",
        "h_where": "3 · Di mana tenaga hilang?",
        "c_zones": "Tenaga yang tidak dapat dijelaskan bagi setiap zon minggu ini (kWh/hari)",
        "l_flagged": "zon ditandakan", "l_ok": "tidak ditandakan", "l_margin": "margin ralat", "l_thr": "ambang tanda bagi zon itu",
        "read_zones": "<b>Cara membacanya:</b> sesebuah zon ditandakan apabila tenaga yang tidak dapat dijelaskan kekal di atas tanda ambangnya ditambah margin ralat selama {k} hari berturut-turut. Ambang berbeza mengikut zon kerana ia berskala dengan tenaga yang dibekalkan setiap pengubah ({p} daripada bekalan, atau {g} kWh sehari, mana-mana yang lebih besar).",
        "th_zone": "Zon", "th_district": "Daerah", "th_kwh": "kWh/hari", "th_pct": "% bekalan", "th_margin": "Margin", "th_thr": "Ambang",
        "th_status": "Status", "th_started": "Kebocoran bermula", "th_pattern": "Corak harian", "th_priority": "Keutamaan", "th_open": "Kes terbuka",
        "st_flagged": "Ditandakan", "st_ok": "Tidak ditandakan", "since_start": "sejak data bermula", "flat": "rata 24/7 (CV {cv})", "varies": "berubah mengikut jam",
        "large": "Beban besar", "normal": "Biasa", "dash": "–",
        "t_priority": "{z} ialah keutamaan: kebocoran bertanda yang terbesar{large}{flat}.",
        "t_priority_large": ", melebihi {p} daripada bekalannya", "t_priority_flat": ", rata sepanjang masa",
        "t_inside_margin": " {g} kWh sehari bagi {z} berada di dalam margin ralatnya, jadi ia tidak ditandakan.",
        "t_below_thr": " {g} kWh sehari bagi {z} melebihi margin ralatnya tetapi di bawah ambang tandanya, jadi ia tidak ditandakan.",
        "t_no_flag": "Tiada zon ditandakan: tenaga yang tidak dapat dijelaskan bagi setiap zon kekal di bawah ambangnya ditambah margin ralat.",
        "no_balance_h": "Zon tanpa meter pengubah (tiada imbangan)",
        "no_balance": "{zones}: tiada meter pengubah, jadi imbangan tenaga tidak dapat dikira; premisnya disusun berdasarkan corak penggunaan sahaja, dengan keyakinan rendah. Calon untuk dipasang meter pengubah.",
        "h_value": "Nilai berisiko (anggaran)",
        "value": "{avg} kWh sehari × 30 hari ≈ <b>{month} kWh sebulan</b>. Dalam RM: {rm}. Ini mengira semua tenaga yang tidak dapat dijelaskan, termasuk margin ralat, jadi ia anggaran tertinggi; mengira hanya tenaga di atas ambang setiap zon memberi kira-kira <b>{above} kWh sebulan</b>{rm_above}.",
        "rm_unset": "[tarif TNB sekWh: akan dibekalkan]", "rm_set": "kira-kira RM {v} sebulan (anggaran, tarif RM {t}/kWh{src})",
        "rm_above": " (kira-kira RM {v})",
        "h_hits": "4 · Adakah pemeriksaan menemui kecurian?",
        "c_hits": "Kadar penemuan setakat ini, dengan julat 95% (% pemeriksaan)",
        "l_model": "pemeriksaan berdasarkan model", "l_random": "pemeriksaan rutin rawak", "l_range": "julat 95%",
        "model_ranked": "Berdasarkan model", "random_sample": "Sampel rawak",
        "hit_label": "{p} ({c} daripada {n}; julat {lo}–{hi}%)",
        "th_insp": "Pemeriksaan", "th_lab": "Berlabel", "th_conf": "Kecurian disahkan", "th_rate": "Kadar penemuan", "th_range": "Julat 95%", "th_means": "Maksudnya",
        "means_model": "Rumah yang dipilih oleh susunan VoltGuard", "means_random": "Rumah yang dipilih secara rawak dalam zon ditandakan: garis asas yang adil",
        "read_hits": "<b>Cara membacanya:</b> kadar penemuan ialah bahagian rumah yang diperiksa di mana kecurian disahkan. Pemeriksaan rutin rawak menunjukkan apa yang akan ditemui tanpa model, jadi jurang antara dua baris ialah nilai model. Julat 95% menunjukkan sejauh mana kadar itu boleh berubah secara kebetulan dengan bilangan pemeriksaan yang sedikit.",
        "h_none": "Belum ada pemeriksaan yang dilabel, jadi tiada kadar penemuan untuk dibandingkan.",
        "h_only_model": "{a} daripada {n} pemeriksaan berdasarkan model menemui kecurian; belum ada pemeriksaan rutin rawak untuk dibandingkan.",
        "h_only_random": "{b} daripada pemeriksaan rutin rawak menemui kecurian; belum ada pemeriksaan berdasarkan model yang dilabel.",
        "h_overlap": "Pemeriksaan berdasarkan model kelihatan {cmp} ({a} berbanding {b}), tetapi julatnya bertindih: {n} pemeriksaan rawak terlalu sedikit untuk membuktikan perbezaan.",
        "h_apart": "Pemeriksaan berdasarkan model menemui kecurian lebih kerap daripada pemeriksaan rawak ({a} berbanding {b}), dan julatnya tidak bertindih, jadi perbezaan itu tidak mungkin kebetulan.",
        "h_apart_worse": "Pemeriksaan berdasarkan model menemui kecurian kurang kerap daripada pemeriksaan rawak ({a} berbanding {b}), dan julatnya tidak bertindih: semak pemberat dan ambang model.",
        "cmp_better": "lebih baik", "cmp_worse": "lebih teruk", "cmp_same": "serupa",
        "h_no_week": " Tiada pemeriksaan direkodkan minggu ini.",
        "h_synthetic": " Keputusan setakat ini datang daripada kes simulasi, jadi ia menunjukkan cara pengukuran berfungsi, bukan prestasi sebenar.",
        "outcomes_h": "Keputusan pemeriksaan", "th_outcome": "Keputusan", "th_week": "Minggu ini", "th_all": "Keseluruhan",
        "o_confirmed_theft": "Kecurian disahkan", "o_false_alarm": "Amaran palsu", "o_inconclusive": "Tidak muktamad",
        "o_no_access": "Tiada akses (tidak digunakan untuk pembelajaran)",
        "status_h": "Kes mengikut status sekarang", "th_status_name": "Status", "th_cases": "Kes", "th_meaning": "Maksud",
        "s_new": "Baharu", "s_assigned": "Ditugaskan", "s_visited": "Dilawati", "s_reporting": "Pelaporan", "s_closed": "Ditutup",
        "m_new": "Menunggu penyelia", "m_assigned": "Pasukan dihantar", "m_visited": "Keputusan direkodkan",
        "m_reporting": "Kecurian disahkan, laporan dalam kelulusan", "m_closed": "Selesai",
        "h_trust": "5 · Bolehkah angka ini dipercayai?",
        "quality_h": "Kualiti data (minggu meter)", "q_complete": "Hari meter dengan ≥ 90% bacaan", "q_monthly": "Meter dibaca bulanan (anggaran harian)",
        "q_no_dtm": "Zon tanpa meter pengubah", "q_dup": "Bacaan pendua atau tidak tertib yang dibetulkan",
        "q_dup_v": "tidak direkodkan bagi sumber data ini", "q_fallbacks": "Sandaran yang digunakan", "q_none": "tiada",
        "f_AS-2": "tiada meter pengubah di {n} zon: disenaraikan tanpa imbangan (AS-2)",
        "f_AS-3-simulated": "voltan ialah simulasi (AS-3)", "f_AS-3": "tiada data voltan: pengesan voltan dimatikan (AS-3)",
        "f_AS-7": "fasa atau cabang tiada: bukti voltan berkeyakinan rendah (AS-7)",
        "f_AS-8": "parameter rangkaian tiada: kehilangan teknikal dibandingkan dengan zon serupa (AS-8)",
        "f_AS-9": "tiada pendaftaran solar: solar bumbung dikenal pasti daripada corak siang sahaja (AS-9)",
        "model_h": "Model yang digunakan", "m_scoring": "Versi pemarkahan", "m_retrained": "Latihan semula terakhir",
        "m_retrained_v": "{at}, versi {v}; {n} label tersedia", "m_not_retrained": "belum dilatih semula; {n} label tersedia",
        "m_alerts": "Amaran data atau hanyutan minggu ini", "m_thresholds": "Ambang",
        "m_thresholds_v": "{p} daripada bekalan atau {g} kWh/hari, {k} hari; beban besar melebihi {l}",
        "assume_h": "Andaian dan had",
        "a_sim": "<b>Data simulasi.</b> Prototaip ini berjalan pada wilayah simulasi yang dibina daripada profil isi rumah awam; voltan datang daripada model rangkaian, kerana data terbuka hanya mengandungi bacaan tenaga.",
        "a_loss": "<b>Kehilangan teknikal dianggarkan</b> oleh model kejuruteraan kabel dan pengubah; ralatnya sebahagian daripada margin ralat.",
        "a_monthly": "<b>Meter bacaan bulanan</b> ({p} daripada meter) diagihkan sepanjang bulan menggunakan corak harian rumah serupa; ini meluaskan margin.",
        "a_small": "<b>Kebocoran kecil boleh tersembunyi:</b> sambungan sekitar 1% daripada bekalan zon berada di dalam margin dan tidak akan menandakan zon itu.",
        "a_rank": "<b>Skor menyusun risiko;</b> ia bukan penemuan kecurian. Manusia membuat keputusan selepas pemeriksaan.",
        "a_tariff": "<b>Tarif belum dibekalkan,</b> jadi nilai berisiko ditunjukkan dalam kWh sahaja.",
        "a_zone": "<b>Peringkat zon sahaja:</b> laporan ini tidak mengandungi ID premis, nama atau alamat, dan meliputi wilayah {r} sahaja.",
        "steps_h": "6 · Langkah seterusnya yang disyorkan",
        "steps_note": "Langkah-langkah dijana daripada peraturan tetap ke atas angka di atas, bukan ditulis oleh model bahasa.",
        "steps_none": "Tiada tindakan yang menonjol daripada angka minggu ini.",
        "n_case_job": "Penyelia: jalankan tugas kes untuk {zones}; suspek utamanya belum ada kes terbuka.",
        "n_case_job_joint": "Penyelia: jalankan tugas kes untuk {zones}; cadangkan operasi bersama polis untuk {large} (beban besar dan rata).",
        "n_joint": "Penyelia: cadangkan operasi bersama polis untuk {large} (beban besar melebihi {p} daripada bekalan).",
        "n_overdue": "Penyelia: susuli {n} kes tertunggak yang ditugaskan lebih {h} jam lalu.",
        "n_alerts": "Pasukan data: semak {n} amaran data atau model yang terbuka.",
        "n_random": "Pengurus: tambah pemeriksaan rutin rawak: {have} setakat ini terlalu sedikit untuk mengukur kadar penemuan sebenar model (sasarkan sekurang-kurangnya {min}).",
        "n_tariff": "Pasukan data: sahkan tarif TNB supaya nilai berisiko boleh ditunjukkan dalam RM.",
        "glossary_h": "Glosari",
        "g": [("Tenaga tidak dapat dijelaskan", "Bekalan pengubah tolak penggunaan bermeter, tolak anggaran meter bacaan bulanan dan kehilangan teknikal yang dijangka."),
              ("Margin ralat (u)", "Sejauh mana tenaga yang tidak dapat dijelaskan boleh berubah secara kebetulan, daripada ketepatan meter, anggaran bacaan bulanan dan model kehilangan."),
              ("Zon ditandakan", "Tenaga yang tidak dapat dijelaskan melebihi ambang ditambah margin ralat selama 7 hari berturut-turut."),
              ("Rata 24/7", "Kebocoran hampir tidak berubah sepanjang hari (pekali variasi di bawah 0.2), lazim bagi rig perlombongan."),
              ("Kadar penemuan", "Bahagian rumah yang diperiksa di mana kecurian disahkan."),
              ("Pemeriksaan rutin rawak", "Pemeriksaan rumah yang dipilih secara rawak dalam zon ditandakan, digunakan sebagai garis asas yang adil.")],
        "foot": "VoltGuard AI · prototaip R0 · Pasukan F-35 · wilayah {r} · laporan {id} · data: {data} · pemarkahan: {model} · skor menyusun risiko; manusia membuat keputusan selepas pemeriksaan.",
        "data_sim": "simulasi", "data_upload": "dimuat naik",
        "page_label": "halaman {page} daripada {total}",
        "headline": "{n} zon ditandakan, {kwh} kWh/hari tidak dapat dijelaskan{chg}; {o} kes dibuka, {c} ditutup, {od} tertunggak{hr}.{step}",
        "hl_chg": " ({s} berbanding minggu sebelumnya)", "hl_hr": "; kadar penemuan berdasarkan model {p}", "hl_step": " Seterusnya: {s}",
        "empty": "Belum ada keputusan pengesanan.",
    },
}


def tr(lang: str) -> dict:
    return T.get(lang, T["en"])


# --------------------------------------------------------------------------- number and date formats

def num(x, digits: int = 0) -> str:
    if x is None:
        return "–"
    return f"{float(x):,.{digits}f}"


def pct(x) -> str:
    """Percentages get one decimal only when needed (e.g. 16%, 2.5%)."""
    if x is None:
        return "–"
    x = float(x)
    return f"{x:.0f}%" if abs(x) >= 10 or abs(x - round(x)) < 0.05 else f"{x:.1f}%"


def signed_pct(x) -> str:
    return "–" if x is None else ("+" if x > 0 else "−" if x < 0 else "±") + pct(abs(x))


def day_range(a: str, b: str, lang: str) -> str:
    d1, d2 = date.fromisoformat(a), date.fromisoformat(b)
    m = MONTHS.get(lang, MONTHS["en"])
    if (d1.year, d1.month) == (d2.year, d2.month):
        return f"{d1.day}–{d2.day} {m[d2.month - 1]} {d2.year}"
    if d1.year == d2.year:
        return f"{d1.day} {m[d1.month - 1]} – {d2.day} {m[d2.month - 1]} {d2.year}"
    return f"{d1.day} {m[d1.month - 1]} {d1.year} – {d2.day} {m[d2.month - 1]} {d2.year}"


def day_text(a: str, lang: str) -> str:
    d = date.fromisoformat(a)
    return f"{d.day} {MONTHS.get(lang, MONTHS['en'])[d.month - 1]} {d.year}"


def when_text(iso: str, lang: str) -> str:
    t = datetime.fromisoformat(iso)
    return f"{t.day} {MONTHS.get(lang, MONTHS['en'])[t.month - 1]} {t.year}, {t:%H:%M}"


# --------------------------------------------------------------------------- rules (pure, unit-tested)

def trend(d: dict) -> tuple[str, bool]:
    """('rising'|'falling'|'steady'|'none', average outside the margin of error)."""
    avg = d["week_average"]["this"]
    if avg is None:
        return "none", False
    change = d["kpis"]["unexplained_change_pct"]
    direction = "steady" if change is None or abs(change) < 10 else ("rising" if change > 0 else "falling")
    margin = d.get("region_margin_kwh") or 0
    return direction, avg > margin


def priority_zone(d: dict) -> dict | None:
    flagged = [z for z in d["zones"] if z["flagged"]]
    if not flagged:
        return None
    large = [z for z in flagged if z["priority"] == "large_load"]
    return max(large or flagged, key=lambda z: z["gap_kwh_per_day"])


def is_flat(z: dict | None, d: dict) -> bool:
    return bool(z and z["flatness_cv"] is not None and z["flatness_cv"] < d["thresholds"]["flat_cv"])


def hit_comparison(d: dict) -> str:
    """'none' | 'only_model' | 'only_random' | 'overlap' | 'apart' | 'apart_worse'."""
    m, r = d["hit_rates"].get("model_ranked"), d["hit_rates"].get("random_sample")
    if not m and not r:
        return "none"
    if not r:
        return "only_model"
    if not m:
        return "only_random"
    if m["ci_low_pct"] <= r["ci_high_pct"] and r["ci_low_pct"] <= m["ci_high_pct"]:
        return "overlap"
    return "apart" if m["hit_rate_pct"] > r["hit_rate_pct"] else "apart_worse"


def next_steps(d: dict) -> list[tuple[str, dict]]:
    """Up to three (rule, figures) pairs, in priority order, from fixed rules on the figures."""
    k, th = d["kpis"], d["thresholds"]
    flagged = [z for z in d["zones"] if z["flagged"]]
    waiting = [z["transformer_id"] for z in flagged if z["suspects_without_case"] > 0]
    large = [z["transformer_id"] for z in flagged if z["priority"] == "large_load"]
    steps: list[tuple[str, dict]] = []
    if waiting and large:
        steps.append(("n_case_job_joint", {"zones": waiting, "large": large}))
    elif waiting:
        steps.append(("n_case_job", {"zones": waiting}))
    elif large:
        steps.append(("n_joint", {"large": large}))
    if k["cases_overdue"]:
        steps.append(("n_overdue", {"n": k["cases_overdue"]}))
    if k["open_alerts"]:
        steps.append(("n_alerts", {"n": k["open_alerts"]}))
    have = (d["hit_rates"].get("random_sample") or {}).get("inspections", 0)
    if have < th["min_random_checks"]:
        steps.append(("n_random", {"have": have, "min": th["min_random_checks"]}))
    if d["value"]["rm_per_kwh"] is None:
        steps.append(("n_tariff", {}))
    return steps[:3]


def step_text(rule: str, figures: dict, d: dict, lang: str) -> str:
    t = tr(lang)
    joined = {key: _join(v, lang) if isinstance(v, list) else v for key, v in figures.items()}
    return t[rule].format(**joined, h=d["thresholds"]["escalation_hours"], p=pct(d["thresholds"]["large_load_share"] * 100))


def _join(items: list[str], lang: str) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + (" and " if lang == "en" else " dan ") + items[-1]


def summary(d: dict, lang: str = "en") -> tuple[list[str], list[str]]:
    """'This week in one paragraph': 3-4 sentences and up to two actions, from fixed rules."""
    t, k = tr(lang), d["kpis"]
    out = []
    avg = d["week_average"]["this"]
    direction, _ = trend(d)
    if avg is None:
        out.append(t["s1_none"])
    elif k["unexplained_change_pct"] is None:
        out.append(t["s1_nochange"].format(r=d["region"], avg=num(avg)))
    else:
        c = k["unexplained_change_pct"]
        word = t["lower" if c < 0 else "higher"].format(p=pct(abs(c)))
        out.append(t["s1"].format(r=d["region"], avg=num(avg), chg=word, trend=t[f"trend_{direction}"]))
    top = priority_zone(d)
    if top:
        total = sum(max(z["gap_kwh_per_day"], 0) for z in d["zones"]) or 1
        sentence = t["s2"].format(n=k["flagged_zones"], m=k["zones_with_balance"], top=top["transformer_id"],
                                  share=pct(max(top["gap_kwh_per_day"], 0) / total * 100))
        out.append(sentence + (t["s2_flat"] if is_flat(top, d) else "") + ".")
    else:
        out.append(t["s2_none"])
    visits = sum(d["outcomes_this_week"].values())
    if not (k["cases_opened"] or k["cases_closed"] or visits):
        out.append(t["s3_idle"])
    else:
        out.append(t["s3" if visits else "s3_novisit"].format(o=k["cases_opened"], c=k["cases_closed"], v=visits))
    actions = [step_text(rule, figs, d, lang) for rule, figs in next_steps(d)[:2]]
    return out, actions


def energy_takeaway(d: dict, lang: str = "en") -> str:
    t = tr(lang)
    direction, outside = trend(d)
    if direction == "none":
        return t["t_none"]
    avg, margin = num(d["week_average"]["this"]), num(d.get("region_margin_kwh"))
    if not outside:
        return t["t_inside"].format(avg=avg, m=margin)
    chg = signed_pct(d["kpis"]["unexplained_change_pct"]) if d["kpis"]["unexplained_change_pct"] is not None else t["k_none"]
    text = t[f"t_{direction}"].format(avg=avg, m=margin, chg=chg)
    if direction == "steady" and is_flat(priority_zone(d), d):
        text += t["t_flat"]
    return text


def zones_takeaway(d: dict, lang: str = "en") -> str:
    t = tr(lang)
    top = priority_zone(d)
    if not top:
        text = t["t_no_flag"]
    else:
        large = t["t_priority_large"].format(p=pct(d["thresholds"]["large_load_share"] * 100)) if top["priority"] == "large_load" else ""
        text = t["t_priority"].format(z=top["transformer_id"], large=large, flat=t["t_priority_flat"] if is_flat(top, d) else "")
    for z in d["zones"]:
        if z["flagged"] or z["gap_kwh_per_day"] <= 0:
            continue
        key = "t_inside_margin" if z["gap_kwh_per_day"] <= z["margin_kwh"] else "t_below_thr"
        text += t[key].format(z=z["transformer_id"], g=num(z["gap_kwh_per_day"]))
    return text


def hits_takeaway(d: dict, lang: str = "en") -> str:
    t = tr(lang)
    m, r = d["hit_rates"].get("model_ranked"), d["hit_rates"].get("random_sample")
    kind = hit_comparison(d)
    if kind == "none":
        text = t["h_none"]
    elif kind == "only_model":
        text = t["h_only_model"].format(a=pct(m["hit_rate_pct"]), n=m["inspections"])
    elif kind == "only_random":
        text = t["h_only_random"].format(b=pct(r["hit_rate_pct"]))
    else:
        a, b = pct(m["hit_rate_pct"]), pct(r["hit_rate_pct"])
        if kind == "overlap":
            cmp = "cmp_better" if m["hit_rate_pct"] > r["hit_rate_pct"] else "cmp_worse" if m["hit_rate_pct"] < r["hit_rate_pct"] else "cmp_same"
            text = t["h_overlap"].format(cmp=t[cmp], a=a, b=b, n=r["inspections"])
        else:
            text = t[f"h_{kind}"].format(a=a, b=b)
    if not sum(d["outcomes_this_week"].values()):
        text += t["h_no_week"]
    if d["data_mode"]["outcomes_simulated"] and kind != "none":
        text += t["h_synthetic"]
    return text


def why_two_dates(d: dict, lang: str = "en") -> str:
    t = tr(lang)
    text = t["why"].format(e=day_range(d["energy_window"]["from"], d["energy_window"]["to"], lang),
                           w=day_range(d["work_window"]["from"], d["work_window"]["to"], lang))
    gap = d["window_gap_days"]
    if gap > 3:
        key = "why_sim" if d["data_mode"]["simulated"] else "why_late"
        text += t[key].format(last=day_text(d["energy_window"]["to"], lang), n=gap)
    return text


def assumptions(d: dict, lang: str = "en") -> list[str]:
    t = tr(lang)
    items = []
    if d["data_mode"]["simulated"]:
        items.append(t["a_sim"])
    items.append(t["a_loss"])
    if (d["quality"]["monthly_read_pct"] or 0) > 0:
        items.append(t["a_monthly"].format(p=pct(d["quality"]["monthly_read_pct"])))
    items += [t["a_small"], t["a_rank"]]
    if d["value"]["rm_per_kwh"] is None:
        items.append(t["a_tariff"])
    items.append(t["a_zone"].format(r=html.escape(d["region"])))
    return items


def value_text(d: dict, lang: str = "en") -> str:
    t, v = tr(lang), d["value"]
    rate = v["rm_per_kwh"]
    if rate is None or v["kwh_per_month"] is None:
        rm, rm_above = t["rm_unset"], ""
    else:
        src = f"; {v['tariff_source']}" if v["tariff_source"] else ""
        rm = t["rm_set"].format(v=num(v["kwh_per_month"] * rate), t=f"{rate:g}", src=html.escape(src))
        rm_above = t["rm_above"].format(v=num(v["kwh_per_month_above_threshold"] * rate))
    return t["value"].format(avg=num(d["week_average"]["this"]), month=num(v["kwh_per_month"]), rm=rm,
                             above=num(v["kwh_per_month_above_threshold"]), rm_above=rm_above)


def headline(d: dict, lang: str = "en") -> str:
    """Telegram text: headline numbers and the top action; zone-level counts only."""
    t = tr(lang)
    if d.get("empty"):
        return t["empty"]
    k = d["kpis"]
    chg = "" if k["unexplained_change_pct"] is None else t["hl_chg"].format(s=signed_pct(k["unexplained_change_pct"]))
    hr = (d["hit_rates"].get("model_ranked") or {}).get("hit_rate_pct")
    steps = next_steps(d)
    step = t["hl_step"].format(s=step_text(*steps[0], d, lang)) if steps else ""
    return t["headline"].format(n=k["flagged_zones"], kwh=num(k["unexplained_kwh_per_day"]), chg=chg, o=k["cases_opened"],
                                c=k["cases_closed"], od=k["cases_overdue"], hr=t["hl_hr"].format(p=pct(hr)) if hr is not None else "",
                                step=step)


# --------------------------------------------------------------------------- charts (inline SVG)

def _ticks(lo: float, hi: float, n: int = 4) -> list[float]:
    span = max(hi - lo, 1e-9)
    raw = span / n
    mag = 10 ** len(str(int(raw))) / 10 if raw >= 1 else 1
    step = next(s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw)
    start = (lo // step) * step
    out, v = [], start
    while v <= hi + 1e-9:
        if v >= lo - 1e-9:
            out.append(round(v, 6))
        v += step
    return out


def chart_energy(d: dict, lang: str = "en") -> str:
    t, pts = tr(lang), d["daily_gap"]
    if len(pts) < 2:
        return f"<p class='cap'>{t['t_none']}</p>"
    W, H, x0, x1, y0, y1 = 680, 230, 52, 664, 18, 196
    lo = min(0.0, min(p["gap_kwh"] - p["margin_kwh"] for p in pts))
    hi = max(p["gap_kwh"] + p["margin_kwh"] for p in pts) * 1.08 or 1
    ticks = _ticks(lo, hi)
    lo, hi = min(lo, ticks[0]), max(hi, ticks[-1])
    X = lambda i: x0 + i * (x1 - x0) / (len(pts) - 1)  # noqa: E731
    Y = lambda v: y1 - (v - lo) / (hi - lo) * (y1 - y0)  # noqa: E731
    parts = []
    for v in ticks:
        parts.append(f"<line x1='{x0}' x2='{x1}' y1='{Y(v):.1f}' y2='{Y(v):.1f}' class='grid'/>"
                     f"<text x='{x0 - 8}' y='{Y(v) + 4:.1f}' text-anchor='end'>{num(v)}</text>")
    top = " ".join(f"{X(i):.1f},{Y(p['gap_kwh'] + p['margin_kwh']):.1f}" for i, p in enumerate(pts))
    bottom = " ".join(f"{X(i):.1f},{Y(p['gap_kwh'] - p['margin_kwh']):.1f}" for i, p in reversed(list(enumerate(pts))))
    parts.append(f"<polygon points='{top} {bottom}' class='band'/>")
    parts.append("<polyline points='" + " ".join(f"{X(i):.1f},{Y(p['gap_kwh']):.1f}" for i, p in enumerate(pts)) + "' class='series'/>")
    start = next((i for i, p in enumerate(pts) if p["date"] >= d["energy_window"]["from"]), len(pts) - 1)
    # Average labels sit outside the margin band (above for last week, below for this week), clear of the line.
    margin = d.get("region_margin_kwh") or 0
    for key, a, b, value, above in (("prev_avg", 0, start - 1, d["week_average"]["prev"], True),
                                    ("this_avg", start, len(pts) - 1, d["week_average"]["this"], False)):
        if value is None or b < a:
            continue
        label_y = Y(value + margin) - 6 if above else Y(value - margin) + 14
        parts.append(f"<line x1='{X(a):.1f}' x2='{X(b):.1f}' y1='{Y(value):.1f}' y2='{Y(value):.1f}' class='avg'/>"
                     f"<text x='{(X(a) + X(b)) / 2:.1f}' y='{min(max(label_y, y0 + 4), y1 - 4):.1f}' text-anchor='middle' class='lab'>{t[key].format(v=num(value))}</text>")
    if start > 0:
        wx = (X(start - 1) + X(start)) / 2
        parts.append(f"<line x1='{wx:.1f}' x2='{wx:.1f}' y1='{y0 - 4}' y2='{y1}' class='week'/>"
                     f"<text x='{wx + 5:.1f}' y='{y0 + 6}' class='lab'>{t['week_starts']}</text>")
    for i, p in enumerate(pts):
        if i % 2 == 0:
            parts.append(f"<text x='{X(i):.1f}' y='{y1 + 20}' text-anchor='middle'>{p['date'][5:]}</text>")
    parts.append(f"<text x='4' y='12' class='axis'>{t['axis_kwh']}</text>")
    return (f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='{html.escape(t['c_energy'])}'>" + "".join(parts) + "</svg>")


def chart_zones(d: dict, lang: str = "en") -> str:
    zones = d["zones"]
    if not zones:
        return ""
    W, x0, x1, row = 680, 120, 590, 40
    hi = max(max(z["gap_kwh_per_day"] + z["margin_kwh"], z["threshold_kwh"]) for z in zones) * 1.1 or 1
    X = lambda v: x0 + max(v, 0) / hi * (x1 - x0)  # noqa: E731
    H = 20 + row * len(zones) + 26
    parts = []
    for i, z in enumerate(zones):
        y = 14 + row * i
        g = z["gap_kwh_per_day"]
        cls = "bar-risk" if z["flagged"] else "bar-ok"
        parts.append(f"<text x='{x0 - 10}' y='{y + 13}' text-anchor='end' class='name'>{html.escape(z['transformer_id'])}</text>"
                     f"<rect x='{x0}' y='{y + 1}' width='{max(X(g) - x0, 2):.1f}' height='16' rx='3' class='{cls}'/>"
                     f"<line x1='{X(g - z['margin_kwh']):.1f}' x2='{X(g + z['margin_kwh']):.1f}' y1='{y + 9}' y2='{y + 9}' class='whisk'/>"
                     f"<line x1='{X(z['threshold_kwh']):.1f}' x2='{X(z['threshold_kwh']):.1f}' y1='{y - 3}' y2='{y + 21}' class='thr'/>"
                     f"<text x='{max(X(g + z['margin_kwh']), X(z['threshold_kwh'])) + 8:.1f}' y='{y + 13}' class='val'>{num(g)} kWh/day</text>")
    for v in _ticks(0, hi):
        parts.append(f"<text x='{X(v):.1f}' y='{H - 6}' text-anchor='middle'>{num(v)}</text>")
    t = tr(lang)
    return f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='{html.escape(t['c_zones'])}'>" + "".join(parts) + "</svg>"


def chart_hits(d: dict, lang: str = "en") -> str:
    t = tr(lang)
    rows = [(key, d["hit_rates"][key]) for key in ("model_ranked", "random_sample") if d["hit_rates"].get(key)]
    if not rows:
        return ""
    W, x0, x1 = 680, 150, 640
    X = lambda v: x0 + v / 100 * (x1 - x0)  # noqa: E731
    parts = []
    for i, (key, h) in enumerate(rows):
        y = 22 + 40 * i
        dot = "dot-risk" if key == "model_ranked" else "dot"
        label = t["hit_label"].format(p=pct(h["hit_rate_pct"]), c=h["confirmed_theft"], n=h["inspections"],
                                      lo=num(h["ci_low_pct"]), hi=num(h["ci_high_pct"]))
        parts.append(f"<text x='{x0 - 10}' y='{y + 5}' text-anchor='end' class='name'>{t[key]}</text>"
                     f"<line x1='{X(h['ci_low_pct']):.1f}' x2='{X(h['ci_high_pct']):.1f}' y1='{y}' y2='{y}' class='ci'/>"
                     f"<line x1='{X(h['ci_low_pct']):.1f}' x2='{X(h['ci_low_pct']):.1f}' y1='{y - 6}' y2='{y + 6}' class='ci'/>"
                     f"<line x1='{X(h['ci_high_pct']):.1f}' x2='{X(h['ci_high_pct']):.1f}' y1='{y - 6}' y2='{y + 6}' class='ci'/>"
                     f"<circle cx='{X(h['hit_rate_pct']):.1f}' cy='{y}' r='6' class='{dot}'/>"
                     f"<text x='{min(X(h['ci_high_pct']) + 8, x1 - 150):.1f}' y='{y - 9 if X(h['ci_high_pct']) + 8 > x1 - 150 else y + 5}' class='val'>{label}</text>")
    H = 22 + 40 * len(rows) + 14
    for v in (0, 25, 50, 75, 100):
        parts.append(f"<text x='{X(v):.1f}' y='{H - 2}' text-anchor='middle'>{v}%</text>")
    return f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='{html.escape(t['c_hits'])}'>" + "".join(parts) + "</svg>"


# --------------------------------------------------------------------------- page

CSS = """@page { size: A4; margin: 16mm 14mm 18mm; }
:root { --ink:#1B2433; --muted:#5B6676; --line:#DCE0E5; --navy:#0F1A2B; --amber:#C77714; --amber-soft:#FCEBD5; --teal:#0F766E; --teal-soft:#DDF3F0; --risk:#B4471B; --blue:#2563EB; }
* { box-sizing:border-box; }
body { font-family:'IBM Plex Sans','Segoe UI',Arial,sans-serif; color:var(--ink); font-size:10.5pt; line-height:1.45; margin:0; font-variant-numeric:tabular-nums; }
h1 { font-size:20pt; margin:0; letter-spacing:-.2px; }
h2 { break-after:avoid; font-size:13pt; margin:22px 0 6px; padding-top:6px; border-top:2px solid var(--navy); }
h3 { break-after:avoid; font-size:10.5pt; margin:12px 0 4px; }
p { margin:4px 0 8px; }
.banner { background:var(--amber-soft); color:#7A4306; border:1px solid #F2C894; padding:6px 10px; border-radius:6px; font-size:9pt; margin:8px 0 12px; }
.meta { color:var(--muted); font-size:9pt; }
.head { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; padding-bottom:8px; border-bottom:1px solid var(--line); }
.summary { background:var(--navy); color:#F6F7F4; border-radius:8px; padding:12px 16px; margin-top:12px; }
.summary b { color:#F2A33A; } .summary ul { margin:6px 0 0 18px; padding:0; }
.kpis { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:8px; }
.kpi { border:1px solid var(--line); border-radius:8px; padding:8px 10px; break-inside:avoid; }
.kpi .v { font-size:18pt; font-weight:700; } .kpi .l { font-weight:600; font-size:9.5pt; }
.kpi .d { color:var(--muted); font-size:8.5pt; } .kpi .c { font-size:8.5pt; color:var(--teal); font-weight:600; }
.read { border-left:3px solid var(--blue); background:#EEF3FD; padding:6px 10px; font-size:9.5pt; margin:6px 0; }
.take { border-left:3px solid var(--amber); background:var(--amber-soft); padding:6px 10px; font-size:9.5pt; margin:6px 0; }
.cap { color:var(--muted); font-size:8.5pt; }
svg { width:100%; height:auto; font-size:11px; fill:var(--muted); }
svg .grid { stroke:#E7EAEE; } svg .band { fill:rgba(37,99,235,.13); stroke:none; }
svg .series { fill:none; stroke:var(--blue); stroke-width:2.2; } svg .avg { stroke:var(--ink); stroke-dasharray:2 3; }
svg .week { stroke:var(--amber); stroke-dasharray:5 4; } svg .lab { fill:var(--ink); font-size:10.5px; } svg .axis { font-size:10.5px; }
svg .bar-risk { fill:var(--risk); } svg .bar-ok { fill:var(--teal); } svg .whisk { stroke:var(--ink); stroke-width:1.4; }
svg .thr { stroke:var(--amber); stroke-width:2.4; } svg .name { fill:var(--ink); font-weight:600; } svg .val { fill:var(--ink); }
svg .ci { stroke:var(--ink); stroke-width:1.6; } svg .dot-risk { fill:var(--amber); stroke:var(--ink); } svg .dot { fill:var(--teal); stroke:var(--ink); }
.legend { display:flex; gap:14px; flex-wrap:wrap; font-size:8.5pt; color:var(--muted); margin:2px 0 4px; }
.legend i { display:inline-block; width:14px; height:8px; margin-right:5px; vertical-align:middle; border-radius:2px; }
table { width:100%; border-collapse:collapse; font-size:9pt; margin:4px 0 6px; }
th { text-align:left; background:#F1F3F6; font-weight:600; padding:5px 6px; border-bottom:1px solid var(--line); }
td { padding:5px 6px; border-bottom:1px solid var(--line); vertical-align:top; } td.n, th.n { text-align:right; }
.pill { font-size:8pt; padding:1px 7px; border-radius:99px; font-weight:600; white-space:nowrap; border:1px solid currentColor; }
.pill.risk { background:#FBE3D8; color:var(--risk); } .pill.ok { background:var(--teal-soft); color:var(--teal); }
.cols { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
ol, ul { margin:4px 0 8px 18px; padding:0; } li { margin:2px 0; }
.foot { margin-top:18px; padding-top:8px; border-top:1px solid var(--line); color:var(--muted); font-size:8pt; }
.avoid { break-inside:avoid; }
"""


def _kpis(d: dict, t: dict, lang: str) -> str:
    k = d["kpis"]

    def change_int(now, before):
        if before is None:
            return t["k_none"]
        diff = (now or 0) - before
        return t["k_same"] if diff == 0 else t["k_diff"].format(s=("+" if diff > 0 else "−") + str(abs(diff)), p=before)

    kwh_change = (t["k_kwh_c"].format(s=signed_pct(k["unexplained_change_pct"]), p=num(k["unexplained_kwh_per_day_prev"]))
                  if k["unexplained_change_pct"] is not None else t["k_none"])
    rate = d["value"]["rm_per_kwh"]
    rm = f"RM {num(k['unexplained_kwh_per_month'] * rate)}" if rate and k["unexplained_kwh_per_month"] else t["rm_unset"]
    tiles = [
        (f"{k['flagged_zones']} <span class='cap'>{t['k_of'].format(m=k['zones_with_balance'])}</span>", t["k_flagged"],
         t["k_flagged_d"].format(k=d["thresholds"]["consecutive_days"]), change_int(k["flagged_zones"], k["flagged_zones_prev"])),
        (num(k["unexplained_kwh_per_day"]), t["k_kwh"], t["k_kwh_d"], kwh_change),
        (f"~{num(k['unexplained_kwh_per_month'])}", t["k_month"],
         t["k_month_d"].format(avg=num(k["unexplained_kwh_per_day"]), rm=rm), t["k_month_c"]),
        (f"{k['cases_opened']} / {k['cases_closed']}", t["k_cases"], t["k_cases_d"], t["k_cases_c"].format(n=k["cases_closed_total"])),
        (str(k["cases_overdue"]), t["k_overdue"], t["k_overdue_d"].format(h=d["thresholds"]["escalation_hours"]), "&nbsp;"),
        (f"{k['reports_exported']} · {k['open_alerts']}", t["k_rep"], t["k_rep_d"], t["k_rep_c"].format(n=k["alerts_this_week"])),
    ]
    return "".join(f"<div class='kpi'><div class='v'>{v}</div><div class='l'>{l}</div><div class='d'>{dd}</div><div class='c'>{c}</div></div>"
                   for v, l, dd, c in tiles)


def _zone_table(d: dict, t: dict) -> str:
    head = "".join(f"<th{' class=n' if c in ('th_kwh', 'th_pct', 'th_margin', 'th_thr', 'th_open') else ''}>{t[c]}</th>"
                   for c in ("th_zone", "th_district", "th_kwh", "th_pct", "th_margin", "th_thr", "th_status", "th_started",
                             "th_pattern", "th_priority", "th_open"))
    rows = []
    for z in d["zones"]:
        started = z["gap_start"] or (t["since_start"] if z["gap_since_start"] else t["dash"])
        if not z["flagged"]:
            started = t["dash"]
        pattern = (t["flat"].format(cv=f"{z['flatness_cv']:.2f}") if is_flat(z, d) else t["varies"]) if z["flagged"] else t["dash"]
        prio = (t["large"] if z["priority"] == "large_load" else t["normal"]) if z["flagged"] else t["dash"]
        status = f"<span class='pill risk'>{t['st_flagged']}</span>" if z["flagged"] else f"<span class='pill ok'>{t['st_ok']}</span>"
        rows.append(f"<tr><td><b>{html.escape(z['transformer_id'])}</b></td><td>{html.escape(z['district'])}</td>"
                    f"<td class='n'>{num(z['gap_kwh_per_day'])}</td><td class='n'>{pct(z['gap_pct'])}</td><td class='n'>±{num(z['margin_kwh'])}</td>"
                    f"<td class='n'>{num(z['threshold_kwh'])}</td><td>{status}</td><td>{started}</td><td>{pattern}</td><td>{prio}</td>"
                    f"<td class='n'>{z['open_cases']}</td></tr>")
    return f"<table><tr>{head}</tr>{''.join(rows)}</table>"


def _hits_table(d: dict, t: dict) -> str:
    rows = []
    for key, means in (("model_ranked", "means_model"), ("random_sample", "means_random")):
        h = d["hit_rates"].get(key)
        if not h:
            continue
        rows.append(f"<tr><td>{t[key]}</td><td class='n'>{h['inspections']}</td><td class='n'>{h['confirmed_theft']}</td>"
                    f"<td class='n'>{pct(h['hit_rate_pct'])}</td><td class='n'>{num(h['ci_low_pct'])}–{num(h['ci_high_pct'])}%</td><td>{t[means]}</td></tr>")
    if not rows:
        return ""
    head = (f"<tr><th>{t['th_insp']}</th><th class='n'>{t['th_lab']}</th><th class='n'>{t['th_conf']}</th><th class='n'>{t['th_rate']}</th>"
            f"<th class='n'>{t['th_range']}</th><th>{t['th_means']}</th></tr>")
    return f"<table>{head}{''.join(rows)}</table>"


def render_html(d: dict, lang: str = "en") -> str:
    lang = lang if lang in T else "en"
    t, esc = tr(lang), html.escape
    if d.get("empty"):
        return f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'><style>{CSS}</style></head><body><p>{t['empty']}</p></body></html>"
    sentences, actions = summary(d, lang)
    acts = "".join(f"<li><b>{t['action'].format(n=i + 1)}:</b> {esc(a)}</li>" for i, a in enumerate(actions))
    banner = f"<div class='banner'><b>{t['banner_sim']}</b></div>" if d["data_mode"]["simulated"] else ""
    leg_energy = (f"<div class='legend'><span><i style='background:#2563EB'></i>{t['l_series']}</span>"
                  f"<span><i style='background:rgba(37,99,235,.25)'></i>{t['l_band'].format(m=num(d.get('region_margin_kwh')))}</span>"
                  f"<span><i style='background:#1B2433;height:2px'></i>{t['l_avg']}</span><span><i style='background:#C77714;height:2px'></i>{t['l_week']}</span></div>")
    leg_zones = (f"<div class='legend'><span><i style='background:#B4471B'></i>{t['l_flagged']}</span><span><i style='background:#0F766E'></i>{t['l_ok']}</span>"
                 f"<span><i style='background:#1B2433;height:2px'></i>{t['l_margin']}</span><span><i style='background:#C77714;width:3px;height:12px'></i>{t['l_thr']}</span></div>")
    leg_hits = (f"<div class='legend'><span><i style='background:#C77714;border-radius:50%;width:9px;height:9px'></i>{t['l_model']}</span>"
                f"<span><i style='background:#0F766E;border-radius:50%;width:9px;height:9px'></i>{t['l_random']}</span>"
                f"<span><i style='background:#1B2433;height:2px'></i>{t['l_range']}</span></div>")
    th = d["thresholds"]
    no_bal = ""
    if d["no_balance_zones"]:
        no_bal = (f"<h3>{t['no_balance_h']}</h3><p>" + t["no_balance"].format(zones=esc(", ".join(z["transformer_id"] for z in d["no_balance_zones"]))) + "</p>")
    outcomes = "".join(f"<tr><td>{t['o_' + o]}</td><td class='n'>{d['outcomes_this_week'].get(o, 0)}</td><td class='n'>{d['outcomes_all_time'].get(o, 0)}</td></tr>"
                       for o in ("confirmed_theft", "false_alarm", "inconclusive", "no_access"))
    statuses = "".join(f"<tr><td>{t['s_' + s]}</td><td class='n'>{d['cases_by_status'].get(s, 0)}</td><td>{t['m_' + s]}</td></tr>"
                       for s in ("new", "assigned", "visited", "reporting", "closed"))
    q = d["quality"]
    fallbacks = "; ".join(t["f_" + f].format(n=q["zones_without_dtm"]) for f in q["fallbacks"]) or t["q_none"]
    m = d["model"]
    retrained = (t["m_retrained_v"].format(at=when_text(m["retrained_at"], lang), v=esc(m["retrained"]), n=m["labels"]) if m["retrained"]
                 else t["m_not_retrained"].format(n=m["labels"]))
    thresholds = t["m_thresholds_v"].format(p=pct(th["share_of_supply"] * 100), g=num(th["min_gap_kwh_per_day"]), k=th["consecutive_days"],
                                            l=pct(th["large_load_share"] * 100))
    steps = next_steps(d)
    steps_html = ("<ol>" + "".join(f"<li>{esc(step_text(r, f, d, lang))}</li>" for r, f in steps) + "</ol>") if steps else f"<p>{t['steps_none']}</p>"
    glossary = "".join(f"<tr><td style='width:26%'><b>{a}</b></td><td>{b}</td></tr>" for a, b in t["g"])
    data_word = t["data_sim"] if d["data_mode"]["simulated"] else t["data_upload"]
    foot = t["foot"].format(r=esc(d["region"]), id=esc(d["report_id"]), data=data_word, model=esc(m["scoring"] or "–"))
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{esc(t['title'].format(r=d['region']))}</title><style>{CSS}</style></head><body>
<div class="head"><div><h1>{esc(t['title'].format(r=d['region']))}</h1>
<div class="meta">{esc(t['meta'].format(id=d['report_id'], when=when_text(d['generated_myt'], lang), r=d['region']))}</div></div>
<div class="meta" style="text-align:right">{t['meter_data']}: {day_range(d['energy_window']['from'], d['energy_window']['to'], lang)}<br>{t['field_work']}: {day_range(d['work_window']['from'], d['work_window']['to'], lang)}</div></div>
{banner}
<div class="summary avoid"><b>{t['one_para']}</b> {esc(' '.join(sentences))}{f'<ul>{acts}</ul>' if acts else ''}</div>

<h2>{t['h_key']}</h2>
<div class="kpis">{_kpis(d, t, lang)}</div>
<div class="read"><b>{t['why_title']}</b> {esc(why_two_dates(d, lang))}</div>

<div class="avoid">
<h2>{t['h_energy']}</h2>
<h3>{t['c_energy']}</h3>{leg_energy}{chart_energy(d, lang)}
<div class="read">{t['read_energy']}</div>
<div class="take"><b>{t['take']}</b> {esc(energy_takeaway(d, lang))}</div>
</div>

<div class="avoid">
<h2>{t['h_where']}</h2>
<h3>{t['c_zones']}</h3>{leg_zones}{chart_zones(d, lang)}
<div class="read">{t['read_zones'].format(k=th['consecutive_days'], p=pct(th['share_of_supply'] * 100), g=num(th['min_gap_kwh_per_day']))}</div>
{_zone_table(d, t)}
<div class="take"><b>{t['take']}</b> {esc(zones_takeaway(d, lang))}</div>
{no_bal}
<h3>{t['h_value']}</h3>
<p>{value_text(d, lang)}</p>
</div>

<div class="avoid">
<h2>{t['h_hits']}</h2>
<h3>{t['c_hits']}</h3>{leg_hits if d['hit_rates'] else ''}{chart_hits(d, lang)}
{_hits_table(d, t)}
<div class="read">{t['read_hits']}</div>
<div class="take"><b>{t['take']}</b> {esc(hits_takeaway(d, lang))}</div>
</div>
<div class="cols avoid">
<div><h3>{t['outcomes_h']}</h3><table><tr><th>{t['th_outcome']}</th><th class="n">{t['th_week']}</th><th class="n">{t['th_all']}</th></tr>{outcomes}</table></div>
<div><h3>{t['status_h']}</h3><table><tr><th>{t['th_status_name']}</th><th class="n">{t['th_cases']}</th><th>{t['th_meaning']}</th></tr>{statuses}</table></div>
</div>

<h2>{t['h_trust']}</h2>
<div class="cols avoid">
<div><h3>{t['quality_h']}</h3><table>
<tr><td>{t['q_complete']}</td><td class="n">{pct(q['meter_days_complete_pct'])}</td></tr>
<tr><td>{t['q_monthly']}</td><td class="n">{pct(q['monthly_read_pct'])}</td></tr>
<tr><td>{t['q_no_dtm']}</td><td class="n">{q['zones_without_dtm']}</td></tr>
<tr><td>{t['q_dup']}</td><td>{t['q_dup_v']}</td></tr>
<tr><td>{t['q_fallbacks']}</td><td>{esc(fallbacks)}</td></tr></table></div>
<div><h3>{t['model_h']}</h3><table>
<tr><td>{t['m_scoring']}</td><td>{esc(m['scoring'] or '–')}</td></tr>
<tr><td>{t['m_retrained']}</td><td>{retrained}</td></tr>
<tr><td>{t['m_alerts']}</td><td class="n">{d['kpis']['alerts_this_week']}</td></tr>
<tr><td>{t['m_thresholds']}</td><td>{thresholds}</td></tr></table></div>
</div>
<div class="avoid"><h3>{t['assume_h']}</h3>
<ul>{''.join(f'<li>{a}</li>' for a in assumptions(d, lang))}</ul></div>

<div class="avoid"><h2>{t['steps_h']}</h2>
{steps_html}
<p class="cap">{t['steps_note']}</p></div>

<div class="avoid"><h3>{t['glossary_h']}</h3>
<table>{glossary}</table></div>

<div class="foot">{foot}</div>
</body></html>"""


def pdf_bytes(d: dict, lang: str = "en") -> bytes:
    t = tr(lang)
    footer = f"VoltGuard AI · {d.get('report_id', '')} · {d.get('region', '')}"
    data, _engine = pdf.html_to_pdf(render_html(d, lang), footer=footer, page_label=t["page_label"])
    return data


def check_document(data: bytes) -> None:
    """Output check on the PDF's own text before it leaves the system: no premise IDs or personal details."""
    try:
        from pypdf import PdfReader
        import io

        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
    except ImportError:  # pragma: no cover - pypdf is in requirements
        return
    if PREMISE_ID.search(text):
        raise guardrails.OutputBlocked("weekly PDF holds a premise ID")
    guardrails.check_output(text, presidio=False)
