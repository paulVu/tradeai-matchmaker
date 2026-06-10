#!/usr/bin/env python3
"""Build the static HTML report site (docs/) for GitHub Pages.

Runs the matchmaker engine for a set of demo queries and renders a
self-contained dashboard. Re-run whenever you want fresh numbers:

  python3 build_report.py
"""

import datetime
import html
import os

import matchmaker as mm

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

REPORTS = [
    {
        "id": "vn-coffee",
        "title": "Vietnamese coffee exporter — where to sell? (HS 0901)",
        "subtitle": "Cà phê Việt Nam: thị trường xuất khẩu tiềm năng",
        "hs": "0901", "mode": "buyers", "country": "VNM",
        "tariff_hs6": "090111",  # representative line: green coffee, not decaf
    },
    {
        "id": "us-furniture",
        "title": "US furniture importer — where to source? (HS 9403)",
        "subtitle": "Nhà nhập khẩu nội thất Mỹ: nguồn cung tốt nhất",
        "hs": "9403", "mode": "suppliers", "country": "USA",
    },
    {
        "id": "vn-grapes",
        "title": "Vietnamese fresh-grape importer — where to source? (HS 080610)",
        "subtitle": "Nho tươi (gồm Shine Muscat): nguồn cung cho nhà nhập khẩu Việt Nam",
        "hs": "080610", "mode": "suppliers", "country": "VNM",
    },
]

# Curated, source-linked shortlist — Phase 3 preview. Hand-written from public
# coverage (FreshPlaza, Produce Report, conference reports); refresh manually.
SHINE_MUSCAT_HTML = """
<div class="card" id="shine-muscat">
  <h2>🍇 Shine Muscat Trung Quốc — nhà vườn &amp; nhà xuất khẩu (sơ bộ)</h2>
  <div class="sub">Phase 3 preview — tổng hợp từ nguồn công khai, CHƯA thẩm định độc lập.</div>

  <p><b>Vùng trồng chính:</b></p>
  <ul style="margin:.4rem 0 .9rem 1.2rem">
    <li><b>Vân Nam (Binchuan/Tân Xuyên)</b> — vùng Shine Muscat lớn nhất, vụ sớm
        (thu hoạch T4–T10, xuất từ T6). Hội chợ trái cây Binchuan 2024 ký hợp đồng
        1,29 tỷ NDT với buyer Thái Lan, Việt Nam.</li>
    <li><b>Hồ Nam</b> — chiến dịch xuất 2025 mở màn sang Malaysia (mục tiêu ~5.000 tấn,
        10+ thị trường châu Á – châu Phi).</li>
    <li><b>Tân Cương</b> — vụ muộn, chất lượng cao, xuất sang Nga qua cửa khẩu Horgos.</li>
  </ul>

  <p><b>Ứng viên từ nguồn công khai (cần thẩm định trước khi giao dịch):</b></p>
  <table>
    <tr><th>Đơn vị</th><th>Vùng</th><th>Ghi nhận công khai</th></tr>
    <tr><td>Binchuan Lvzhiyuan Agricultural Development Co., Ltd.</td><td>Vân Nam (Binchuan)</td>
        <td>Chuyên trái cây đặc sản Binchuan, đã xuất sang Việt Nam (đưa tin hội chợ Binchuan)</td></tr>
    <tr><td>Zhengzhou Chen's Sun Fruit &amp; Vegetable Trade Co., Ltd.</td><td>Hà Nam (trader)</td>
        <td>Thương mại nho Vân Nam: Shine Muscat, Kyoho, Hongti</td></tr>
    <tr><td>Hai Shun Agri</td><td>Đa vùng</td>
        <td>Chào hàng Shine Muscat xuất khẩu 2025 (website công ty)</td></tr>
    <tr><td>Laiwu Manhing Vegetables Fruits Corp.</td><td>Sơn Đông</td>
        <td>Xuất rau quả 60+ quốc gia từ 2001 (gồm nho)</td></tr>
  </table>

  <div class="insights"><b>⚠️ Due diligence bắt buộc</b><ul>
    <li><b>Cảnh báo dư lượng thuốc BVTV:</b> Thai Consumers Council (2024) phát hiện
        Shine Muscat Trung Quốc tồn dư hóa chất vượt ngưỡng; hàng vào VN thường bán dưới
        tên "nho sữa/nho mẫu đơn". → Yêu cầu <b>kiểm nghiệm MRL từng lô</b> + COA.</li>
    <li>Kiểm tra <b>đăng ký GACC</b> của nhà xuất khẩu &amp; mã vùng trồng; yêu cầu
        phytosanitary certificate, ưu tiên GlobalGAP/HACCP.</li>
    <li>Giá Shine Muscat tại VN đang ở <b>đáy 4 năm</b> (nguồn cung TQ dư thừa) —
        lợi thế đàm phán cho buyer nhưng rủi ro chất lượng hàng giá rẻ.</li>
    <li>Xác minh tốt nhất: gặp trực tiếp tại hội chợ (Binchuan Fruit Conference,
        Asia Fruit Logistica HK) hoặc qua thương vụ/VCCI.</li>
  </ul></div>

  <p class="sub" style="margin-top:.8rem">Nguồn: FreshPlaza, Produce Report, Fruitnet,
  VnExpress, China Daily, EastFruit (2024–2025). Danh sách mang tính gợi ý ban đầu,
  không phải khuyến nghị thương mại.</p>
</div>"""
YEAR = 2023
TREND = 4
TOP = 12

CSS = """
:root { --bg:#0f172a; --card:#1e293b; --text:#e2e8f0; --muted:#94a3b8;
        --accent:#38bdf8; --new:#f472b6; --grow:#34d399; --est:#64748b; }
* { box-sizing:border-box; margin:0; }
body { background:var(--bg); color:var(--text);
       font:15px/1.6 -apple-system,'Segoe UI',Roboto,sans-serif; padding:2rem 1rem; }
.wrap { max-width:1000px; margin:0 auto; }
h1 { font-size:1.7rem; margin-bottom:.3rem; }
h2 { font-size:1.2rem; margin:0 0 .2rem; }
.sub { color:var(--muted); margin-bottom:1.5rem; }
.card { background:var(--card); border-radius:12px; padding:1.3rem 1.5rem;
        margin-bottom:1.6rem; overflow-x:auto; }
table { border-collapse:collapse; width:100%; margin-top:.8rem; font-size:.92rem; }
th { text-align:left; color:var(--muted); font-weight:600; padding:.4rem .6rem;
     border-bottom:1px solid #334155; white-space:nowrap; }
td { padding:.45rem .6rem; border-bottom:1px solid #273349; white-space:nowrap; }
td.num, th.num { text-align:right; }
.bar { background:#0c4a6e; border-radius:3px; height:10px; display:inline-block;
       vertical-align:middle; margin-right:.5rem; }
.tag { font-size:.75rem; font-weight:700; padding:.1rem .5rem; border-radius:99px; }
.tag.NEW { background:var(--new); color:#500724; }
.tag.GROW { background:var(--grow); color:#064e3b; }
.tag.ESTABLISHED { background:var(--est); color:#f1f5f9; }
.insights { background:#172554; border-left:4px solid var(--accent);
            border-radius:8px; padding:.9rem 1.1rem; margin-top:1rem; }
.insights li { margin-left:1.1rem; margin-bottom:.3rem; }
.pos { color:var(--grow); } .neg { color:#f87171; }
footer { color:var(--muted); font-size:.85rem; margin-top:2rem; }
a { color:var(--accent); }
"""


VN_FRUIT_IMPORTERS_HTML = """
<div class="card" id="vn-fruit-importers">
  <h2>🍎 Nhà nhập khẩu trái cây uy tín tại Việt Nam (sơ bộ)</h2>
  <div class="sub">Phase 3 preview — tiêu chí: sản lượng nhập, đa dạng mặt hàng, kênh phân phối.
  Tổng hợp từ nguồn công khai, CHƯA thẩm định độc lập.</div>

  <p><b>Bối cảnh thị trường (UN Comtrade, VN nhập khẩu 2023):</b></p>
  <ul style="margin:.4rem 0 .9rem 1.2rem">
    <li>Trái cây tươi tiêu dùng (HS 0805–0810): táo &amp; lê <b>$270M</b> ·
        nho <b>$158M</b> · cam quýt <b>$104M</b> · kiwi/berries <b>$70M</b> ·
        đào/mận/cherry <b>$60M</b>.</li>
    <li>Nguồn cung chính: Trung Quốc <b>$219.6M</b> &gt; New Zealand <b>$120.3M</b>
        &gt; Mỹ <b>$91.4M</b> &gt; Úc <b>$82.6M</b> &gt; Nam Phi <b>$47.6M</b>.</li>
    <li>(Hạt điều thô HS 0801 ~$2.76B là nguyên liệu chế biến xuất khẩu,
        không tính vào trái cây tiêu dùng.)</li>
  </ul>

  <p><b>Ứng viên theo 3 tiêu chí (từ nguồn công khai):</b></p>
  <table>
    <tr><th>Đơn vị</th><th>Đa dạng mặt hàng</th><th>Kênh phân phối</th></tr>
    <tr><td><b>Klever Group</b> (Klever Fruit, Bonnie Fruit, Hoàng Giang Fruit)</td>
        <td>Nhập trực tiếp Mỹ, Nhật, Úc, Hàn, Pháp; trái cây cao cấp</td>
        <td>~59 cửa hàng HN + HCM (chuỗi bán lẻ trái cây NK lớn nhất VN), tổng kho sỉ
            Hoàng Giang, cấp sỉ cho đại lý/siêu thị/F&amp;B; phái đoàn nông nghiệp Mỹ
            từng thăm trực tiếp (2024)</td></tr>
    <tr><td><b>Fuji Fruit</b></td>
        <td>50+ loại từ New Zealand, Mỹ, Nam Phi, EU (táo Envy, kiwi Zespri, cherry)</td>
        <td>Chuỗi cửa hàng + kênh sỉ toàn quốc</td></tr>
    <tr><td><b>Homefarm</b></td>
        <td>Trái cây + thực phẩm nhập khẩu đa dạng (Nam Phi, Hàn, Pháp...)</td>
        <td>Hệ thống bán lẻ thực phẩm NK quy mô lớn + phân phối sỉ</td></tr>
    <tr><td><b>Kamereo</b></td>
        <td>Danh mục rộng phục vụ F&amp;B</td>
        <td>Nền tảng B2B online, 4.000+ doanh nghiệp F&amp;B, kho lạnh riêng</td></tr>
    <tr><td><b>Cevis</b></td>
        <td>Mỹ, Úc, NZ, Hàn (cam Navel/Sunkist, cherry, kiwi vàng, dâu Hàn)</td>
        <td>Phân phối sỉ cao cấp</td></tr>
    <tr><td><b>Phúc Lộc Thọ Fruits</b></td>
        <td>Trái cây NK phổ thông – cao cấp</td>
        <td>Sỉ cho cửa hàng/siêu thị TP.HCM &amp; phía Nam</td></tr>
    <tr><td><b>Khối siêu thị nhập trực tiếp</b> (MM Mega Market, Central Retail/GO!,
        WinCommerce, Saigon Co.op)</td>
        <td>Volume lớn nhất theo mùa vụ (táo, cam, nho)</td>
        <td>Hàng trăm điểm bán toàn quốc — kênh modern trade mạnh nhất</td></tr>
  </table>

  <div class="insights"><b>⚠️ Lưu ý phương pháp</b><ul>
    <li>Hải quan VN <b>không công bố số liệu nhập khẩu theo từng công ty</b> — xếp hạng
        trên dựa vào độ phủ kênh phân phối &amp; ghi nhận báo chí, không phải số liệu
        kim ngạch chính thức của từng đơn vị.</li>
    <li>Muốn xác minh sản lượng thật: yêu cầu đối tác cung cấp tờ khai hải quan mẫu,
        hoặc tra cứu qua VCCI / dữ liệu manifest thương mại (Phase 3 đầy đủ).</li>
    <li>Nếu mục tiêu là <b>bán hàng vào VN</b> (exporter tìm buyer): nhóm chuỗi bán lẻ
        + nhà sỉ B2B ở trên chính là danh sách tiếp cận đầu tiên, kèm hội chợ
        Vietfood &amp; Beverage, Fruit Logistica Asia.</li>
  </ul></div>

  <p class="sub" style="margin-top:.8rem">Nguồn: Dân Việt, Kamereo, Nông sản Dũng Hà,
  website doanh nghiệp (2024–2026) + UN Comtrade 2023. Danh sách gợi ý ban đầu,
  không phải khuyến nghị thương mại.</p>
</div>"""


def fmt_usd(v):
    return mm.fmt_usd(v)


def insights_for(rows, mode):
    """Rule-based written analysis: rank by opportunity score."""
    scored = []
    for r in rows:
        growth = (r.get("cagr_pct") or 0) / 100
        score = r["market_usd"] * (1 - min(r["penetration_pct"], 100) / 100) * (1 + max(growth, 0))
        scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    word = "thị trường" if mode == "buyers" else "nguồn cung"
    out = []
    for score, r in scored[:3]:
        cagr = r.get("cagr_pct")
        trend_txt = f", tăng trưởng {cagr:+.1f}%/năm" if cagr is not None else ""
        out.append(
            f"<b>{html.escape(r['country'])}</b> — {word} {fmt_usd(r['market_usd'])}"
            f"{trend_txt}; mức thâm nhập hiện tại {r['penetration_pct']:.1f}% "
            f"({r['opportunity']}) → dư địa lớn nhất."
            if score == scored[0][0] else
            f"<b>{html.escape(r['country'])}</b> — {fmt_usd(r['market_usd'])}"
            f"{trend_txt}; thâm nhập {r['penetration_pct']:.1f}% ({r['opportunity']})."
        )
    decl = [r for r in rows if (r.get("cagr_pct") or 0) < 0]
    if decl:
        names = ", ".join(html.escape(r["country"]) for r in decl[:3])
        out.append(f"⚠️ Thị trường đang thu hẹp (CAGR âm): {names} — cân nhắc trước khi đầu tư.")
    return out


def render_report(spec, rows):
    max_market = max(r["market_usd"] for r in rows) or 1
    trs = []
    has_tariff = bool(spec.get("tariff_hs6"))
    for i, r in enumerate(rows, 1):
        w = max(4, int(r["market_usd"] / max_market * 120))
        cagr = r.get("cagr_pct")
        cagr_html = (f"<span class='{'pos' if cagr >= 0 else 'neg'}'>{cagr:+.1f}%</span>"
                     if cagr is not None else "<span class='sub'>n/a</span>")
        up = r.get("unit_price_usd_kg")
        up_html = f"${up:.2f}" if up is not None else "<span class='sub'>n/a</span>"
        tariff_html = ""
        if has_tariff:
            tp = r.get("mfn_tariff_pct")
            tariff_html = (f"<td class='num'>{tp:.1f}%</td>" if tp is not None
                           else "<td class='num'><span class='sub'>n/a</span></td>")
        trs.append(
            f"<tr><td>{i}</td><td>{html.escape(r['country'])}</td>"
            f"<td class='num'><span class='bar' style='width:{w}px'></span>"
            f"{fmt_usd(r['market_usd'])}</td>"
            f"<td class='num'>{fmt_usd(r['current_trade_usd'])}</td>"
            f"<td class='num'>{r['penetration_pct']:.1f}%</td>"
            f"<td class='num'>{cagr_html}</td>"
            f"<td class='num'>{up_html}</td>"
            f"{tariff_html}"
            f"<td><span class='tag {r['opportunity']}'>{r['opportunity']}</span></td></tr>"
        )
    market_col = "Import market" if spec["mode"] == "buyers" else "Export supply"
    your_col = "Your exports" if spec["mode"] == "buyers" else "Your imports"
    tariff_th = (f"<th class='num'>MFN tariff (HS {spec['tariff_hs6']})</th>"
                 if has_tariff else "")
    ins = "".join(f"<li>{t}</li>" for t in insights_for(rows, spec["mode"]))
    return f"""
<div class="card" id="{spec['id']}">
  <h2>{html.escape(spec['title'])}</h2>
  <div class="sub">{html.escape(spec['subtitle'])} · {YEAR}, trend window {YEAR - TREND}–{YEAR}</div>
  <table>
    <tr><th>#</th><th>Country</th><th class="num">{market_col} ({YEAR})</th>
        <th class="num">{your_col}</th><th class="num">Penetration</th>
        <th class="num">CAGR {TREND}y</th><th class="num">$/kg</th>{tariff_th}<th>Status</th></tr>
    {''.join(trs)}
  </table>
  <div class="insights"><b>💡 Phân tích nhanh / Key insights</b><ul>{ins}</ul></div>
</div>"""


def main():
    countries = mm.load_countries()

    def cname(cid):
        iso, label = countries.get(str(cid), ("", f"#{cid}"))
        return f"{label} ({iso})" if iso else label

    sections = []
    for spec in REPORTS:
        me = mm.iso_to_code(spec["country"], countries)
        print(f"running {spec['id']} …")
        rows = mm.market_analysis(spec["hs"], YEAR, me, spec["mode"],
                                  top=TOP, trend_years=TREND,
                                  tariff_hs6=spec.get("tariff_hs6"),
                                  countries=countries)
        for r in rows:
            r["country"] = cname(r["code"])
        sections.append(render_report(spec, rows))
        if spec["id"] == "vn-grapes":
            sections.append(SHINE_MUSCAT_HTML)
            sections.append(VN_FRUIT_IMPORTERS_HTML)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TradeAI Matchmaker — Global Supply/Demand Reports</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<h1>🌏 TradeAI Matchmaker</h1>
<div class="sub">Global supply &amp; demand matching — kết nối nhà xuất khẩu và nhập khẩu
qua dữ liệu hải quan chính thức (UN Comtrade). Generated {now} (ICT).</div>
{''.join(sections)}
<footer>
Data: <a href="https://comtradeapi.un.org">UN Comtrade</a> — official customs
statistics reported by ~200 governments. CAGR computed over {TREND} years.
Status: NEW = no current presence · GROW = &lt;5% penetration · ESTABLISHED = ≥5%.
Mirror-data caveat: partner-reported values (CIF) can exceed reporter values (FOB),
so penetration can exceed 100% in suppliers mode.<br>
Built by TradeAI (koi fleet) · Phase 1–2 prototype · analysis is informational,
not investment or trading advice.
</footer>
</div></body></html>"""

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(page)
    print(f"wrote {os.path.join(OUT, 'index.html')}")


if __name__ == "__main__":
    main()
