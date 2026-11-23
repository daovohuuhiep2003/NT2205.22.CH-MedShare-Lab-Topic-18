"""
Script tạo file PowerPoint Proposal cho đề tài MedShare-Lab
NT2205.11.CH – Đề tài 18
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from lxml import etree

# ─── Màu sắc chủ đề ─────────────────────────────────────────────────────────
C_NAVY      = RGBColor(0x0D, 0x2F, 0x5E)
C_TEAL      = RGBColor(0x00, 0x7A, 0x8A)
C_LIGHTBLUE = RGBColor(0xD6, 0xEA, 0xF8)
C_WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
C_RED       = RGBColor(0xC0, 0x39, 0x2B)
C_RED_LIGHT = RGBColor(0xF9, 0xEB, 0xEA)
C_GREEN     = RGBColor(0x1A, 0x8A, 0x4A)
C_GREEN_LT  = RGBColor(0xD5, 0xE8, 0xD4)
C_ORANGE    = RGBColor(0xE6, 0x7E, 0x22)
C_DARKGRAY  = RGBColor(0x2C, 0x3E, 0x50)
C_LIGHTGRAY = RGBColor(0xEC, 0xF0, 0xF1)
C_GOLD      = RGBColor(0xF3, 0x9C, 0x12)
C_YELLOW_LT = RGBColor(0xFF, 0xF2, 0xCC)
C_PURPLE    = RGBColor(0x76, 0x4F, 0x8C)
C_PURPLE_LT = RGBColor(0xE1, 0xD5, 0xE7)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


# ─── Hàm tiện ích ────────────────────────────────────────────────────────────

def add_rect(slide, x, y, w, h, fill=None, line=None, line_w=Pt(0)):
    shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = line
        shape.line.width = line_w
    else:
        shape.line.fill.background()
    return shape


def add_text(slide, text, x, y, w, h,
             font_size=18, bold=False, color=C_WHITE,
             align=PP_ALIGN.LEFT, italic=False, wrap=True):
    txBox = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    txBox.word_wrap = wrap
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txBox


def add_multiline(slide, lines, x, y, w, h,
                  font_size=14, bold=False, color=C_DARKGRAY,
                  align=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    txBox.word_wrap = True
    tf = txBox.text_frame
    tf.word_wrap = True
    first = True
    for item in lines:
        if isinstance(item, str):
            txt, b, c = item, bold, color
        else:
            txt = item[0]
            b   = item[1] if len(item) > 1 else bold
            c   = item[2] if len(item) > 2 else color
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        run = p.add_run()
        run.text = txt
        run.font.size = Pt(font_size)
        run.font.bold = b
        run.font.color.rgb = c
    return txBox


def slide_header(slide, title, subtitle=None):
    add_rect(slide, 0, 0, 13.33, 1.2, fill=C_NAVY)
    add_rect(slide, 0, 1.2, 13.33, 0.06, fill=C_TEAL)
    add_text(slide, title, 0.4, 0.1, 12.5, 0.7,
             font_size=28, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)
    if subtitle:
        add_text(slide, subtitle, 0.4, 0.72, 12.5, 0.42,
                 font_size=14, color=RGBColor(0xAA, 0xD4, 0xF5),
                 align=PP_ALIGN.LEFT)


def card(slide, x, y, w, h, title, body_lines,
         hdr_fill=C_TEAL, body_fill=C_LIGHTBLUE,
         title_color=C_WHITE, body_color=C_DARKGRAY,
         font_size=13, title_size=14):
    add_rect(slide, x, y, w, 0.42, fill=hdr_fill)
    add_text(slide, title, x+0.1, y+0.04, w-0.2, 0.36,
             font_size=title_size, bold=True, color=title_color)
    bh = h - 0.42
    add_rect(slide, x, y+0.42, w, bh, fill=body_fill,
             line=hdr_fill, line_w=Pt(1.2))
    add_multiline(slide, body_lines, x+0.12, y+0.52, w-0.24, bh-0.18,
                  font_size=font_size, color=body_color)


def box_node(slide, label, sublabel, x, y, w, h,
             fill=C_NAVY, border=None, lbl_color=C_WHITE,
             sub_color=None, font_size=13, sub_size=10):
    """Vẽ node hình chữ nhật bo góc (rounded) cho sơ đồ."""
    # Dùng shape rounded rectangle (freeform style via shape type 5 = rounded rect)
    shape = slide.shapes.add_shape(
        5,  # MSO_SHAPE_TYPE.ROUNDED_RECTANGLE
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if border:
        shape.line.color.rgb = border
        shape.line.width = Pt(1.5)
    else:
        shape.line.fill.background()
    # Adjust corner rounding
    shape.adjustments[0] = 0.05

    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = label
    run.font.size = Pt(font_size)
    run.font.bold = True
    run.font.color.rgb = lbl_color

    if sublabel:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = sublabel
        r2.font.size = Pt(sub_size)
        r2.font.color.rgb = sub_color if sub_color else RGBColor(0xCC, 0xCC, 0xFF)
    return shape


def arrow_h(slide, x1, x2, y, color=C_DARKGRAY, label="", label_color=None):
    """Vẽ mũi tên ngang từ x1→x2 tại y."""
    lc = label_color if label_color else color
    # Thân mũi tên
    mid_y = y + 0.015
    add_rect(slide, x1, mid_y, x2-x1-0.12, 0.03, fill=color)
    # Đầu mũi tên (tam giác nhỏ)
    tip = slide.shapes.add_shape(
        5, Inches(x2-0.18), Inches(y-0.06), Inches(0.18), Inches(0.12)
    )
    tip.fill.solid(); tip.fill.fore_color.rgb = color
    tip.line.fill.background()
    if label:
        add_text(slide, label, x1, y-0.22, x2-x1, 0.2,
                 font_size=9, color=lc, align=PP_ALIGN.CENTER, italic=True)


def arrow_v(slide, x, y1, y2, color=C_DARKGRAY, label=""):
    """Vẽ mũi tên dọc từ y1→y2 tại x."""
    mid_x = x + 0.015
    add_rect(slide, mid_x, y1, 0.03, y2-y1-0.1, fill=color)
    tip = slide.shapes.add_shape(
        5, Inches(x-0.06), Inches(y2-0.15), Inches(0.15), Inches(0.15)
    )
    tip.fill.solid(); tip.fill.fore_color.rgb = color
    tip.line.fill.background()
    if label:
        add_text(slide, label, x+0.08, (y1+y2)/2-0.15, 1.2, 0.28,
                 font_size=9, color=color, italic=True)


def badge(slide, text, x, y, w, h, fill, text_color=C_WHITE, font_size=10):
    add_rect(slide, x, y, w, h, fill=fill)
    add_text(slide, text, x+0.05, y+0.03, w-0.1, h-0.06,
             font_size=font_size, bold=True, color=text_color, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
#  SLIDE 1 – Trang bìa
# ════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill=C_NAVY)
add_rect(sl, 0, 0, 0.55, 7.5, fill=C_TEAL)
add_rect(sl, 0.55, 2.6, 9.5, 0.06, fill=C_GOLD)
add_rect(sl, 1.0, 0.6, 2.2, 0.9, fill=C_TEAL)
add_text(sl, "Đề tài 18", 1.05, 0.65, 2.1, 0.8,
         font_size=20, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
add_text(sl, "NT2205.11.CH – Bảo mật Cơ sở Dữ liệu Nâng cao",
         1.0, 1.6, 10.5, 0.5, font_size=15,
         color=RGBColor(0xAA, 0xD4, 0xF5), align=PP_ALIGN.LEFT)
add_text(sl, "MedShare-Lab", 1.0, 2.1, 11.5, 1.0,
         font_size=46, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)
add_text(sl, "Hệ thống quản lý hồ sơ bệnh án điện tử đa thuê bao\n"
             "với bảo mật tầng trường dữ liệu trên Cloud DBMS",
         1.0, 3.1, 11.0, 1.0, font_size=18,
         color=RGBColor(0xD6, 0xEA, 0xF8), align=PP_ALIGN.LEFT)
add_rect(sl, 1.0, 4.3, 3.2, 0.55, fill=C_GOLD)
add_text(sl, "PROPOSAL REPORT", 1.05, 4.33, 3.1, 0.5,
         font_size=17, bold=True, color=C_NAVY, align=PP_ALIGN.CENTER)
add_text(sl, "Học kỳ 1 – Năm học 2025–2026   |   UIT – Trường Đại học Công nghệ Thông tin",
         1.0, 6.6, 11.5, 0.5, font_size=12,
         color=RGBColor(0x88, 0xAA, 0xCC), align=PP_ALIGN.LEFT)


# ════════════════════════════════════════════════════════════════════════════
#  SLIDE 2 – Agenda
# ════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill=C_LIGHTGRAY)
slide_header(sl, "Nội dung trình bày", "Proposal – MedShare-Lab")

items = [
    ("01", "Ngữ cảnh bài toán",          "Bối cảnh EHR & Cloud DBMS"),
    ("02", "Bên liên quan",               "Stakeholders & Adversary Model"),
    ("03", "Vấn đề đặt ra",               "Các véc-tơ tấn công & điểm yếu"),
    ("04", "Giải pháp đề xuất",           "Kỹ thuật & Kiến trúc bảo mật"),
    ("05", "Sơ đồ hệ thống TRƯỚC",       "Baseline B0 – Điểm yếu trực quan"),
    ("06", "Sơ đồ hệ thống SAU",         "Profile P1 – Kiến trúc hoàn thiện"),
]
for i, (num, title, sub) in enumerate(items):
    row = i // 2; col = i % 2
    bx = 0.5 + col * 6.4; by = 1.55 + row * 1.78
    add_rect(sl, bx, by, 6.1, 1.55, fill=C_NAVY)
    add_rect(sl, bx, by, 1.1, 1.55, fill=C_TEAL)
    add_text(sl, num, bx+0.05, by+0.35, 1.0, 0.9,
             font_size=28, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
    add_text(sl, title, bx+1.2, by+0.15, 4.7, 0.65,
             font_size=17, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)
    add_text(sl, sub,   bx+1.2, by+0.82, 4.7, 0.6,
             font_size=12, color=RGBColor(0xAA, 0xD4, 0xF5), align=PP_ALIGN.LEFT)


# ════════════════════════════════════════════════════════════════════════════
#  SLIDE 3 – Ngữ cảnh bài toán
# ════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill=C_LIGHTGRAY)
slide_header(sl, "01 · Ngữ cảnh bài toán",
             "Hồ sơ bệnh án điện tử (EHR) trên nền tảng Cloud DBMS")
contexts = [
    ("📋  EHR & Số hoá Y tế",
     ["• Hồ sơ bệnh án chuyển từ giấy → điện tử (EHR).",
      "• Nhiều bệnh viện dùng chung hạ tầng Cloud DBMS.",
      "• Dữ liệu: chẩn đoán, thuốc, ghi chú lâm sàng."]),
    ("☁️  Multi-tenant Cloud DBMS",
     ["• Hospital A (60%) + Hospital B (40%) cùng 1 DB.",
      "• Dữ liệu các tenant lưu chung → nguy cơ rò rỉ.",
      "• DBA của Cloud có quyền SELECT * trên mọi bảng."]),
    ("⚖️  Yêu cầu pháp lý",
     ["• HIPAA / GDPR: dữ liệu y tế cần bảo mật đặc biệt.",
      "• Nguyên tắc 'need-to-know': chỉ ai có chức năng mới xem.",
      "• Mọi truy cập phải được ghi audit log đầy đủ."]),
]
for i, (title, lines) in enumerate(contexts):
    bx = 0.35 + i * 4.3
    card(sl, bx, 1.55, 4.1, 5.6, title,
         [(l, False, C_DARKGRAY) for l in lines],
         hdr_fill=C_NAVY, body_fill=C_WHITE, font_size=13, title_size=14)
add_rect(sl, 0, 7.0, 13.33, 0.5, fill=C_NAVY)
add_text(sl, "💡  Bài toán: Bảo vệ dữ liệu bệnh nhân ngay cả khi Cloud DBA, "
             "snapshot ổ đĩa hoặc kẻ tấn công có quyền truy cập vật lý vào DB.",
         0.3, 7.03, 12.7, 0.42,
         font_size=13, bold=True, color=C_GOLD, align=PP_ALIGN.LEFT)


# ════════════════════════════════════════════════════════════════════════════
#  SLIDE 4 – Bên liên quan
# ════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill=C_LIGHTGRAY)
slide_header(sl, "02 · Bên liên quan", "Stakeholders & Adversary Model")

headers = ["Bên liên quan", "Vai trò", "Mức tin cậy"]
col_w = [3.2, 6.2, 2.6]; col_x = [0.35, 3.6, 9.85]; row_h = 0.62

for j, (h, cw, cx) in enumerate(zip(headers, col_w, col_x)):
    add_rect(sl, cx, 1.45, cw, row_h, fill=C_NAVY)
    add_text(sl, h, cx+0.1, 1.48, cw-0.2, row_h-0.08,
             font_size=13, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

rows = [
    ("👨‍⚕️ Bác sĩ / Điều dưỡng",
     "Người dùng lâm sàng – đọc/ghi hồ sơ bệnh nhân",
     "✅ Tin cậy (có điều kiện)", C_GREEN),
    ("🏥 Bệnh viện / Tổ chức",
     "Data Controller – quản lý chính sách truy cập & tuân thủ pháp lý",
     "✅ Tin cậy cao", C_GREEN),
    ("🖥️ DBA (Cloud)",
     "Vận hành DB – có quyền SELECT * nhưng KHÔNG được xem bản rõ",
     "⚠️ Bán tin cậy", C_ORANGE),
    ("☁️ Cloud DBMS Provider",
     "Hạ tầng lưu trữ – kiểm soát vật lý ổ đĩa (nguy cơ snapshot theft)",
     "⚠️ Bán tin cậy", C_ORANGE),
    ("🏦 KMS / Vault Provider",
     "Quản lý khoá mã hoá – nằm trong Zone Z1 do bệnh viện kiểm soát",
     "✅ Tin cậy (Z1)", C_GREEN),
    ("👤 Bệnh nhân",
     "Chủ thể dữ liệu – quyền riêng tư & bảo mật thông tin y tế cá nhân",
     "— Không truy cập trực tiếp", C_DARKGRAY),
    ("☠️ Kẻ tấn công",
     "M0: ngoài mạng  |  M2: DBA nội bộ  |  M3: tenant khác  |  M4: replay",
     "❌ Không tin cậy", C_RED),
]
for i, (name, role, trust, tc) in enumerate(rows):
    by = 1.45 + (i+1)*row_h
    bg = C_WHITE if i % 2 == 0 else C_LIGHTBLUE
    for cw, cx in zip(col_w, col_x):
        add_rect(sl, cx, by, cw, row_h, fill=bg,
                 line=RGBColor(0xCC,0xCC,0xCC), line_w=Pt(0.5))
    for j, (txt, cw, cx) in enumerate(zip([name, role, trust], col_w, col_x)):
        fc = tc if j == 2 else C_DARKGRAY
        add_text(sl, txt, cx+0.08, by+0.08, cw-0.16, row_h-0.12,
                 font_size=11, color=fc, bold=(j==2))


# ════════════════════════════════════════════════════════════════════════════
#  SLIDE 5 – Vấn đề đặt ra
# ════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill=C_LIGHTGRAY)
slide_header(sl, "03 · Vấn đề đặt ra",
             "Các điểm yếu & véc-tơ tấn công trong hệ thống EHR cơ bản")
problems = [
    ("🔴", "DBA đọc bản rõ",
     "DBA có quyền SELECT * → xem toàn bộ\nchẩn đoán, thuốc, ghi chú lâm sàng."),
    ("🔴", "Snapshot ổ đĩa",
     "Cloud provider sao chép ổ đĩa vật lý\n→ toàn bộ dữ liệu bị lộ tức thì."),
    ("🔴", "Không phân tách Tenant",
     "Hospital A có thể query được dữ liệu\ncủa Hospital B (cross-tenant leak)."),
    ("🔴", "Không kiểm soát Trường",
     "Không có ABAC: mọi role đọc được\nmọi trường dù không có nhu cầu."),
    ("🔴", "Query lộ bản rõ",
     "Index trực tiếp trên plaintext\n→ frequency inference attack."),
    ("🔴", "Hoán đổi Ciphertext",
     "Không có AAD binding → ciphertext\ncó thể bị swap giữa các bản ghi."),
]
for i, (icon, title, desc) in enumerate(problems):
    row = i // 3; col = i % 3
    bx = 0.35 + col * 4.3; by = 1.55 + row * 2.6
    add_rect(sl, bx, by, 4.1, 2.3, fill=C_WHITE, line=C_RED, line_w=Pt(2.0))
    add_rect(sl, bx, by, 4.1, 0.55, fill=C_RED)
    add_text(sl, f"{icon}  {title}", bx+0.12, by+0.05, 3.86, 0.48,
             font_size=14, bold=True, color=C_WHITE)
    add_text(sl, desc, bx+0.15, by+0.68, 3.8, 1.5,
             font_size=13, color=C_DARKGRAY, wrap=True)
add_rect(sl, 0, 7.0, 13.33, 0.5, fill=C_RED)
add_text(sl, "⚠️  Hệ thống EHR cơ bản KHÔNG đủ bảo vệ khi Cloud DBA là bán tin cậy. "
             "Cần bảo mật TẦNG TRƯỜNG DỮ LIỆU độc lập với tầng DB.",
         0.3, 7.03, 12.7, 0.42,
         font_size=13, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)


# ════════════════════════════════════════════════════════════════════════════
#  SLIDE 6 – Giải pháp đề xuất
# ════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill=C_LIGHTGRAY)
slide_header(sl, "04 · Giải pháp đề xuất", "Kỹ thuật bảo mật & mục đích")
solutions = [
    ("🔑 AES-256-GCM\nField Encryption",
     "Mã hoá từng trường lâm sàng\nriêng lẻ bằng DEK 256-bit.",
     "DBA/snapshot chỉ thấy ciphertext"),
    ("🏷️ AAD Context Binding",
     "Ràng buộc ciphertext vào tenant\n+ record_id + field_name.",
     "Chống hoán đổi ciphertext (M4)"),
    ("🏦 HashiCorp Vault\nTransit KMS",
     "Bọc/giải bọc DEK; xoay KEK;\ntách biệt Zone Z1 ≠ Z2.",
     "DEK không bao giờ ra ngoài Z1"),
    ("🛡️ ABAC Policy Engine",
     "Deny-by-default:\nRole + Dept + Tenant + Time.",
     "Ngăn truy cập trái phép (M3)"),
    ("🔍 Blind Index\nHKDF + HMAC-SHA256",
     "Tìm kiếm bình đẳng trên dữ liệu\nmã hoá không cần giải mã.",
     "Chống frequency inference"),
    ("📋 Audit Log (Z3)",
     "Ghi metadata mọi truy cập:\nactor + action + timestamp.",
     "Phát hiện & truy vết xâm phạm"),
]
for i, (tech, desc, benefit) in enumerate(solutions):
    row = i // 3; col = i % 3
    bx = 0.35 + col * 4.3; by = 1.55 + row * 2.7
    add_rect(sl, bx, by, 4.1, 2.5, fill=C_WHITE, line=C_TEAL, line_w=Pt(2.0))
    add_rect(sl, bx, by, 4.1, 0.6, fill=C_NAVY)
    add_text(sl, tech, bx+0.12, by+0.06, 3.86, 0.52,
             font_size=13, bold=True, color=C_WHITE)
    add_text(sl, desc, bx+0.15, by+0.72, 3.8, 1.0,
             font_size=12, color=C_DARKGRAY, wrap=True)
    add_rect(sl, bx+0.1, by+1.82, 3.9, 0.48, fill=C_GREEN_LT)
    add_text(sl, "✅ " + benefit, bx+0.15, by+1.85, 3.8, 0.42,
             font_size=11, bold=True, color=C_GREEN, wrap=True)


# ════════════════════════════════════════════════════════════════════════════
#  SLIDE 7 – Sơ đồ hệ thống TRƯỚC bảo mật
# ════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill=C_LIGHTGRAY)
slide_header(sl, "05 · Sơ đồ hệ thống TRƯỚC bảo mật",
             "Baseline B0 – Dữ liệu lưu bản rõ, không phân vùng, không kiểm soát trường")

# ── Tầng 1: Người dùng ──────────────────────────────────────────────────────
add_rect(sl, 0.3, 1.38, 12.7, 0.3, fill=RGBColor(0xCC,0xCC,0xCC))
add_text(sl, "TẦNG NGƯỜI DÙNG", 0.35, 1.39, 5.0, 0.28,
         font_size=10, bold=True, color=C_DARKGRAY)

box_node(sl, "👨‍⚕️ Bác sĩ",   "", 0.5,  1.75, 1.8, 0.85,
         fill=RGBColor(0x21,0x6D,0xB0), lbl_color=C_WHITE, font_size=13)
box_node(sl, "👩‍⚕️ Điều dưỡng","", 2.5,  1.75, 1.8, 0.85,
         fill=RGBColor(0x21,0x6D,0xB0), lbl_color=C_WHITE, font_size=13)
box_node(sl, "🖥️ DBA",        "Toàn quyền DB", 9.8, 1.75, 2.2, 0.85,
         fill=C_RED, lbl_color=C_WHITE, sub_color=RGBColor(0xFF,0xBB,0xBB),
         font_size=13)
box_node(sl, "☠️ Kẻ tấn công","Snapshot / Breach", 12.1, 1.75, 1.0, 0.85,
         fill=RGBColor(0x6D,0x06,0x06), lbl_color=C_WHITE,
         sub_color=RGBColor(0xFF,0xAA,0xAA), font_size=10)

# ── Tầng 2: App Server ──────────────────────────────────────────────────────
add_rect(sl, 0.3, 2.78, 12.7, 0.28, fill=RGBColor(0xCC,0xCC,0xCC))
add_text(sl, "TẦNG ỨNG DỤNG  (Không có ABAC · Không có KMS · Không phân tách Tenant)",
         0.35, 2.79, 12.0, 0.26, font_size=10, bold=True, color=C_DARKGRAY)

box_node(sl, "🖥️ App Server", "Không xác thực trường", 4.5, 3.12, 4.0, 0.9,
         fill=RGBColor(0xD3,0x7A,0x00), lbl_color=C_WHITE,
         sub_color=RGBColor(0xFF,0xE0,0xAA), font_size=14)

# Badge: No ABAC
badge(sl, "✘ No ABAC",    1.0, 3.18, 1.8, 0.38, fill=C_RED)
badge(sl, "✘ No Tenant",  2.9, 3.18, 1.5, 0.38, fill=C_RED)
badge(sl, "✘ No KMS",     8.6, 3.18, 1.4, 0.38, fill=C_RED)
badge(sl, "✘ No Blind Idx",10.1,3.18, 1.6, 0.38, fill=C_RED)

# ── Mũi tên user → app ──────────────────────────────────────────────────────
arrow_v(sl, 1.35, 2.6,  3.12, color=RGBColor(0x21,0x6D,0xB0), label="HTTP")
arrow_v(sl, 3.35, 2.6,  3.12, color=RGBColor(0x21,0x6D,0xB0))

# ── Tầng 3: Database ────────────────────────────────────────────────────────
add_rect(sl, 0.3, 4.2, 12.7, 0.28, fill=RGBColor(0xCC,0xCC,0xCC))
add_text(sl, "TẦNG CƠ SỞ DỮ LIỆU  (Bản rõ – Plaintext – Không mã hoá trường)",
         0.35, 4.21, 12.0, 0.26, font_size=10, bold=True, color=C_RED)

# DB box
add_rect(sl, 3.2, 4.55, 6.6, 2.4, fill=C_RED_LIGHT, line=C_RED, line_w=Pt(2.5))
add_rect(sl, 3.2, 4.55, 6.6, 0.5, fill=C_RED)
add_text(sl, "🗄️  PostgreSQL  –  Bản rõ (Plaintext)", 3.3, 4.57, 6.4, 0.44,
         font_size=14, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

# DB fields – plaintext
fields = [
    ("patient_id",   "12345",             0.15),
    ("diagnosis",    "E11 – Tiểu đường",  0.15),
    ("medication",   "Metformin 500mg",   0.15),
    ("notes",        "Bệnh nhân ổn định", 0.15),
    ("tenant_id",    "hospital_a",        0.15),
]
for fi, (fname, fval, _) in enumerate(fields):
    col = fi % 2; row2 = fi // 2
    fx = 3.4 + col * 3.1; fy = 5.12 + row2 * 0.42
    add_rect(sl, fx, fy, 2.95, 0.36, fill=C_WHITE,
             line=RGBColor(0xDD,0x88,0x88), line_w=Pt(0.8))
    add_text(sl, f"{fname}: {fval}", fx+0.08, fy+0.04, 2.8, 0.28,
             font_size=10, color=C_DARKGRAY)

# Mũi tên App → DB
arrow_v(sl, 6.45, 4.02, 4.55, color=RGBColor(0xD3,0x7A,0x00), label="SQL plain")

# Mũi tên DBA → DB trực tiếp (đỏ đậm)
add_rect(sl, 10.0, 2.6, 0.04, 2.5, fill=C_RED)   # đường thẳng đứng
add_rect(sl, 9.5,  5.1, 0.55, 0.04, fill=C_RED)   # ngang vào DB
add_text(sl, "SELECT *\n→ Bản rõ", 10.12, 3.3, 1.7, 0.5,
         font_size=10, bold=True, color=C_RED, italic=True)

# Mũi tên kẻ tấn công → DB (đứt đoạn)
add_rect(sl, 12.35, 2.6, 0.04, 2.5, fill=RGBColor(0x6D,0x06,0x06))
add_rect(sl, 9.8,   5.1, 2.6,  0.04, fill=RGBColor(0x6D,0x06,0x06))
add_text(sl, "Snapshot\n→ 100% lộ", 11.7, 3.3, 1.5, 0.5,
         font_size=10, bold=True, color=RGBColor(0x6D,0x06,0x06), italic=True)

# Attack badges bên phải
attacks = [
    "🔴 DBA: SELECT * = bản rõ",
    "🔴 Snapshot ổ đĩa = lộ 100%",
    "🔴 Cross-tenant không chặn",
    "🔴 Không Blind Index",
    "🔴 Không AAD binding",
]
for ai, atxt in enumerate(attacks):
    add_rect(sl, 0.32, 4.6 + ai*0.38, 2.8, 0.33, fill=C_RED_LIGHT,
             line=C_RED, line_w=Pt(0.8))
    add_text(sl, atxt, 0.38, 4.63 + ai*0.38, 2.68, 0.28,
             font_size=9, bold=True, color=C_RED)


# ════════════════════════════════════════════════════════════════════════════
#  SLIDE 8 – Sơ đồ hệ thống SAU bảo mật
# ════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill=C_LIGHTGRAY)
slide_header(sl, "06 · Sơ đồ hệ thống SAU bảo mật",
             "Profile P1 – Phân vùng tin cậy · Field Encryption · ABAC · Vault KMS · Blind Index")

# ─── Zone Z0 ────────────────────────────────────────────────────────────────
add_rect(sl, 0.25, 1.38, 13.0, 1.22, fill=C_LIGHTBLUE,
         line=RGBColor(0x21,0x6D,0xB0), line_w=Pt(1.5))
add_text(sl, "Zone Z0 – Internet / Client", 0.35, 1.4, 5.0, 0.3,
         font_size=10, bold=True, color=RGBColor(0x21,0x6D,0xB0))
box_node(sl, "👨‍⚕️ Bác sĩ",   "Hospital A/B", 0.45, 1.72, 1.9, 0.75,
         fill=RGBColor(0x21,0x6D,0xB0), lbl_color=C_WHITE,
         sub_color=RGBColor(0xCC,0xDD,0xFF), font_size=12, sub_size=9)
box_node(sl, "👩‍⚕️ Điều dưỡng","Hospital A/B", 2.5,  1.72, 1.9, 0.75,
         fill=RGBColor(0x21,0x6D,0xB0), lbl_color=C_WHITE,
         sub_color=RGBColor(0xCC,0xDD,0xFF), font_size=12, sub_size=9)
# DBA blocked
box_node(sl, "🖥️ DBA","❌ Bị từ chối", 10.9, 1.72, 2.1, 0.75,
         fill=RGBColor(0x88,0x22,0x22), lbl_color=C_WHITE,
         sub_color=RGBColor(0xFF,0xBB,0xBB), font_size=12, sub_size=9)

# ─── Zone Z1 ────────────────────────────────────────────────────────────────
add_rect(sl, 0.25, 2.72, 13.0, 1.88, fill=C_GREEN_LT,
         line=C_GREEN, line_w=Pt(2.0))
add_text(sl, "Zone Z1 – Trusted Application Layer  (Kiểm soát bởi Bệnh viện)",
         0.35, 2.74, 10.0, 0.3, font_size=10, bold=True, color=C_GREEN)

box_node(sl, "🔒 API Gateway", "mTLS / JWT",   0.45,  3.1, 2.1, 0.9,
         fill=C_NAVY, lbl_color=C_WHITE, sub_color=RGBColor(0xAA,0xD4,0xF5),
         font_size=12, sub_size=9)
box_node(sl, "🛡️ ABAC PDP", "Role+Dept\n+Tenant+Time", 2.72, 3.1, 2.1, 0.9,
         fill=C_NAVY, lbl_color=C_WHITE, sub_color=RGBColor(0xAA,0xD4,0xF5),
         font_size=12, sub_size=9)
box_node(sl, "🔑 Key Broker", "AES-256-GCM\nWrap/Unwrap", 5.0, 3.1, 2.1, 0.9,
         fill=C_NAVY, lbl_color=C_WHITE, sub_color=RGBColor(0xAA,0xD4,0xF5),
         font_size=12, sub_size=9)
box_node(sl, "🏦 Vault KMS", "Transit\nKEK Rotation", 7.28, 3.1, 2.1, 0.9,
         fill=C_NAVY, lbl_color=C_WHITE, sub_color=RGBColor(0xAA,0xD4,0xF5),
         font_size=12, sub_size=9)
box_node(sl, "🔍 Blind Engine","HKDF+HMAC\nSHA-256", 9.55, 3.1, 2.1, 0.9,
         fill=C_NAVY, lbl_color=C_WHITE, sub_color=RGBColor(0xAA,0xD4,0xF5),
         font_size=12, sub_size=9)

# Block DBA at Z1
add_rect(sl, 10.88, 2.85, 2.28, 1.62, fill=RGBColor(0xF9,0xEB,0xEA),
         line=C_RED, line_w=Pt(2.0))
add_text(sl, "🚫 Chặn tại Z1\nChỉ thấy ciphertext\nKhông có DEK", 10.92, 3.0, 2.15, 1.28,
         font_size=10, bold=True, color=C_RED, align=PP_ALIGN.CENTER)

# Arrows inside Z1
for ax in [2.55, 4.83, 7.1]:
    add_rect(sl, ax, 3.52, 0.2, 0.03, fill=C_TEAL)
    add_text(sl, "▶", ax+0.01, 3.43, 0.2, 0.2,
             font_size=9, color=C_TEAL, align=PP_ALIGN.CENTER)

# ─── Zone Z2 ────────────────────────────────────────────────────────────────
add_rect(sl, 0.25, 4.72, 9.8, 2.3, fill=C_YELLOW_LT,
         line=RGBColor(0xD6,0x8B,0x00), line_w=Pt(2.0))
add_text(sl, "Zone Z2 – Cloud DBMS  (Bán tin cậy · Chỉ chứa Ciphertext · Không có DEK)",
         0.35, 4.74, 12.0, 0.3, font_size=10, bold=True,
         color=RGBColor(0x99,0x66,0x00))

box_node(sl, "🗄️ PostgreSQL 16","Encrypted Fields\nRLS per Tenant",
         0.45, 5.1, 2.5, 1.6,
         fill=RGBColor(0x99,0x66,0x00), lbl_color=C_WHITE,
         sub_color=RGBColor(0xFF,0xEE,0xBB), font_size=13, sub_size=9)
box_node(sl, "🔐 Capsule Store","Wrapped DEK\n(per record)",
         3.15, 5.1, 2.3, 1.6,
         fill=RGBColor(0x99,0x66,0x00), lbl_color=C_WHITE,
         sub_color=RGBColor(0xFF,0xEE,0xBB), font_size=12, sub_size=9)
box_node(sl, "🔍 search_index","blind_token HMAC\nKhông bản rõ",
         5.65, 5.1, 2.3, 1.6,
         fill=RGBColor(0x99,0x66,0x00), lbl_color=C_WHITE,
         sub_color=RGBColor(0xFF,0xEE,0xBB), font_size=12, sub_size=9)
box_node(sl, "🗄️ MongoDB 7.0","Encrypted Docs\nSemi-structured",
         8.15, 5.1, 1.7, 1.6,
         fill=RGBColor(0x99,0x66,0x00), lbl_color=C_WHITE,
         sub_color=RGBColor(0xFF,0xEE,0xBB), font_size=12, sub_size=9)

# ─── Zone Z3 ────────────────────────────────────────────────────────────────
add_rect(sl, 10.25, 4.72, 3.0, 2.3, fill=C_PURPLE_LT,
         line=C_PURPLE, line_w=Pt(2.0))
add_text(sl, "Zone Z3 – Audit Log", 10.35, 4.74, 2.8, 0.3,
         font_size=10, bold=True, color=C_PURPLE)
box_node(sl, "📋 Audit Log","actor+action+ts\nImmutable\nKhông bản rõ",
         10.35, 5.1, 2.8, 1.6,
         fill=C_PURPLE, lbl_color=C_WHITE,
         sub_color=RGBColor(0xEE,0xDD,0xFF), font_size=12, sub_size=9)

# ─── Mũi tên Z0 → Z1 ────────────────────────────────────────────────────────
arrow_v(sl, 1.4,  2.47, 3.1, color=RGBColor(0x21,0x6D,0xB0), label="HTTPS")
arrow_v(sl, 3.47, 2.47, 3.1, color=RGBColor(0x21,0x6D,0xB0))

# ─── Mũi tên Z1 → Z2 ────────────────────────────────────────────────────────
arrow_v(sl, 1.65, 4.0, 5.1, color=RGBColor(0xD6,0x8B,0x00), label="Ciphertext")
arrow_v(sl, 4.27, 4.0, 5.1, color=RGBColor(0xD6,0x8B,0x00), label="Capsule")
arrow_v(sl, 6.72, 4.0, 5.1, color=RGBColor(0xD6,0x8B,0x00), label="Token")

# ─── Mũi tên Z1 → Z3 ────────────────────────────────────────────────────────
arrow_v(sl, 11.72, 4.0, 5.1, color=C_PURPLE, label="Audit")

# ─── Protection badges bên phải ─────────────────────────────────────────────
protections = [
    "🟢 AES-256-GCM  →  DBA chỉ thấy ciphertext",
    "🟢 Vault KMS Z1 →  DEK không bao giờ ra DB",
    "🟢 ABAC deny-by-default  →  Chặn truy cập trái phép",
    "🟢 Blind Index HMAC  →  Tìm kiếm không lộ bản rõ",
    "🟢 AAD binding  →  Chống ciphertext swap",
    "🟢 Audit Log Z3 →  Truy vết mọi truy cập",
]
# Không còn chỗ bên phải vì Z3 đã chiếm; đặt dọc theo cạnh dưới
add_rect(sl, 0.25, 7.08, 13.0, 0.36, fill=C_NAVY)
prot_txt = "  |  ".join(["🟢 AES-GCM", "🟢 Vault KMS", "🟢 ABAC", "🟢 Blind Index", "🟢 AAD Binding", "🟢 Audit Z3"])
add_text(sl, prot_txt, 0.35, 7.10, 12.8, 0.3,
         font_size=11, bold=True, color=C_GOLD, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
#  SLIDE 9 – So sánh Trước / Sau
# ════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill=C_LIGHTGRAY)
slide_header(sl, "07 · Trước & Sau khi áp dụng bảo mật",
             "Baseline B0 vs Profile P1 – MedShare-Lab")

add_rect(sl, 0.3, 1.45, 6.0, 0.55, fill=C_RED)
add_text(sl, "❌  Trước (Baseline B0)", 0.4, 1.48, 5.8, 0.48,
         font_size=17, bold=True, color=C_WHITE)
before = [
    "• Dữ liệu lưu bản rõ trong PostgreSQL",
    "• DBA: SELECT * → xem toàn bộ hồ sơ",
    "• Snapshot ổ đĩa = lộ 100% dữ liệu",
    "• Không phân tách tenant",
    "• Không ABAC – mọi role đều đọc được",
    "• Không Blind Index – query lộ bản rõ",
    "• Không AAD – ciphertext có thể bị swap",
]
add_rect(sl, 0.3, 2.0, 6.0, 5.0, fill=C_WHITE, line=C_RED, line_w=Pt(1.5))
add_multiline(sl, [("  " + b, False, C_RED if i < 2 else C_DARKGRAY)
                   for i, b in enumerate(before)],
              0.45, 2.1, 5.7, 4.8, font_size=13)

add_rect(sl, 7.0, 1.45, 6.0, 0.55, fill=C_GREEN)
add_text(sl, "✅  Sau (Profile P1)", 7.1, 1.48, 5.8, 0.48,
         font_size=17, bold=True, color=C_WHITE)
after = [
    "• AES-256-GCM: DBA chỉ thấy ciphertext",
    "• Vault KMS (Z1): DEK không bao giờ ra DB",
    "• LUKS + Field Encrypt: 2 lớp at-rest",
    "• RLS + ABAC: phân tách tenant chặt chẽ",
    "• ABAC deny-by-default theo Role+Dept",
    "• Blind Index: tìm kiếm không lộ bản rõ",
    "• AAD Binding: chống hoán đổi ciphertext",
]
add_rect(sl, 7.0, 2.0, 6.0, 5.0, fill=C_WHITE, line=C_GREEN, line_w=Pt(1.5))
add_multiline(sl, [("  " + a, False, C_GREEN if i < 2 else C_DARKGRAY)
                   for i, a in enumerate(after)],
              7.15, 2.1, 5.7, 4.8, font_size=13)

add_rect(sl, 6.4, 1.7, 0.5, 5.5, fill=C_NAVY)
add_text(sl, "VS", 6.38, 4.2, 0.55, 0.6,
         font_size=16, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
#  SLIDE 10 – Q&A / Cảm ơn
# ════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill=C_NAVY)
add_rect(sl, 0, 0, 0.55, 7.5, fill=C_TEAL)
add_rect(sl, 0.55, 3.5, 12.78, 0.06, fill=C_GOLD)
add_text(sl, "Cảm ơn!", 1.5, 1.0, 10.0, 1.4,
         font_size=64, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
add_text(sl, "MedShare-Lab – Đề tài 18 – NT2205.11.CH",
         1.5, 2.5, 10.0, 0.6,
         font_size=20, color=RGBColor(0xAA,0xD4,0xF5), align=PP_ALIGN.CENTER)
add_rect(sl, 2.5, 3.8, 8.33, 0.7, fill=C_TEAL)
add_text(sl, "Q & A", 2.5, 3.82, 8.33, 0.65,
         font_size=28, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
summary = [
    "🔑  Field-level AES-256-GCM + Vault KMS → DBA không đọc được bản rõ",
    "🛡️  ABAC deny-by-default → kiểm soát truy cập chính xác đến từng trường",
    "🔍  Blind Index HMAC-SHA256 → tìm kiếm an toàn không lộ bản rõ",
    "📋  Audit Log Z3 (immutable) → mọi truy cập đều được truy vết",
]
add_multiline(sl, [(s, False, RGBColor(0xD6,0xEA,0xF8)) for s in summary],
              1.5, 4.75, 10.5, 2.3, font_size=14)

# ─── Lưu ─────────────────────────────────────────────────────────────────────
OUTPUT = "/media/howie/Data/Documents/HK1/MH-UD/NT2205.11.CH_Project/PROPOSAL_MedShare_Lab.pptx"
prs.save(OUTPUT)
print(f"✅  Đã tạo: {OUTPUT}")
print(f"    Tổng số slide: {len(prs.slides)}")
