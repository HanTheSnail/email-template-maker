import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, datetime as dt, math

st.set_page_config(page_title="Image Template Certificate (Demo)", page_icon="🖼️")

# -------- Helpers --------
def get_font(size_px, bold=False):
    try:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
        return ImageFont.truetype(path, size=size_px)
    except Exception:
        return ImageFont.load_default()

def draw_wrapped(draw, text, x, y, max_w, font, fill="black", line_spacing=6):
    if not text:
        return y
    words = text.split()
    line = ""
    lines = []
    for w in words:
        test = (line + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    # draw lines
    _, line_h = font.getbbox("Ay")[2:]
    ypos = y
    for ln in lines:
        draw.text((x, ypos), ln, font=font, fill=fill)
        ypos += line_h + line_spacing
    return ypos

def paste_logo(base, logo, box):
    # box: (left, top, width, height)
    l, t, w, h = box
    if logo is None:
        return
    # keep aspect ratio and center
    logo = logo.copy()
    logo = logo.convert("RGBA")
    ratio_logo = logo.width / logo.height
    ratio_box = (w / h) if h else 1
    if ratio_logo > ratio_box:
        new_w = int(w)
        new_h = max(1, int(new_w / ratio_logo))
    else:
        new_h = int(h)
        new_w = max(1, int(new_h * ratio_logo))
    resized = logo.resize((max(1,new_w), max(1,new_h)))
    x = int(l + (w - new_w) / 2)
    y = int(t + (h - new_h) / 2)
    base.paste(resized, (x, y), mask=resized)

# -------- UI --------
st.title("Demo: Use an Image Template (from PowerPoint)")

st.markdown("""
Upload a **background image** exported from PowerPoint (e.g., PNG of your slide).  
Then add your logo, pick colors, type the text, and position elements with sliders.
""")

template_file = st.file_uploader("Upload background image (PNG/JPG)", type=["png","jpg","jpeg","webp"])
logo_file = st.file_uploader("Upload brand logo (optional; PNG with transparency preferred)", type=["png","jpg","jpeg","webp"])

with st.sidebar:
    st.header("Brand & Styles")
    brand = st.text_input("Brand", "Shell")
    accent = st.color_picker("Border / Accent color", "#D32F2F")
    border_px = st.slider("Border thickness (px)", 0, 24, 6)
    text_color = st.color_picker("Text color", "#000000")

    st.header("Typography")
    title_size = st.slider("Header font size (px)", 16, 96, 44)
    body_size = st.slider("Body font size (px)", 12, 64, 28)
    small_size = st.slider("Small font size (px)", 10, 48, 22)

st.subheader("Content")
header_text = st.text_input("Header", "CONGRATULATIONS!")
subhead_text = st.text_area("Subheader", "You have provided outstanding customer service and a customer has shared the details via our Customer Satisfaction Survey.", height=90)
comment_text = st.text_area("Customer comment", "“The staff were extremely helpful, especially Faye! They happily helped me pick out the things I was looking for, thank you!!”", height=120)

col1, col2, col3 = st.columns(3)
with col1:
    visit_date = st.text_input("Visit Date (DD/MM/YYYY)", dt.date.today().strftime("%d/%m/%Y"))
with col2:
    survey_date = st.text_input("Survey Date (DD/MM/YYYY)", dt.date.today().strftime("%d/%m/%Y"))
with col3:
    id_label = st.text_input("ID Label", "Restaurant ID")
id_value = st.text_input("ID Value", "12345")

footer_text = st.text_area("Footer", "Congratulations from {brand} for providing outstanding customer service. Please share this with your team to celebrate!", height=80)

st.subheader("Positions (percentages relative to image size)")
st.caption("Tip: Start with rough positions, then fine-tune. Width controls wrapping for text blocks.")

def pos_controls(prefix, default):
    c1, c2, c3 = st.columns(3)
    with c1:
        x = st.slider(f"{prefix} X (%)", 0, 100, default[0])
        w = st.slider(f"{prefix} Width (%)", 1, 100, default[2])
    with c2:
        y = st.slider(f"{prefix} Y (%)", 0, 100, default[1])
    with c3:
        h = st.slider(f"{prefix} Height (%)", 1, 100, default[3])
    return x, y, w, h

logo_pos = pos_controls("Logo box", (5, 4, 20, 10))
title_pos = pos_controls("Header box", (28, 6, 60, 10))
subhead_pos = pos_controls("Subheader box", (8, 22, 84, 12))
comment_pos = pos_controls("Comment box", (8, 40, 84, 30))
meta_pos = pos_controls("Meta (dates/id) box", (8, 72, 60, 12))
footer_pos = pos_controls("Footer box", (8, 85, 84, 10))

def percent_to_box(img_w, img_h, pos):
    x_pct, y_pct, w_pct, h_pct = pos
    l = int(img_w * x_pct / 100.0)
    t = int(img_h * y_pct / 100.0)
    w = int(img_w * w_pct / 100.0)
    h = int(img_h * h_pct / 100.0)
    return l, t, w, h

if template_file is not None:
    bg = Image.open(template_file).convert("RGB")
    W, H = bg.size
    img = bg.copy()
    draw = ImageDraw.Draw(img)

    # Border (over the background)
    if border_px > 0:
        try:
            col = tuple(int(accent.strip("#")[i:i+2], 16) for i in (0,2,4))
        except Exception:
            col = (0,0,0)
        draw.rectangle((0,0,W-1,H-1), outline=col, width=border_px)

    # Paste logo
    logo_img = Image.open(logo_file).convert("RGBA") if logo_file else None
    paste_logo(img, logo_img, percent_to_box(W,H,logo_pos))

    # Text colors & fonts
    try:
        col_txt = tuple(int(text_color.strip("#")[i:i+2], 16) for i in (0,2,4))
    except Exception:
        col_txt = (0,0,0)
    f_title = get_font(title_size, bold=True)
    f_body = get_font(body_size, bold=False)
    f_small = get_font(small_size, bold=False)

    # Header
    l,t,w,h = percent_to_box(W,H,title_pos)
    draw_wrapped(draw, header_text, l, t, w, f_title, fill=col_txt)

    # Subheader
    l,t,w,h = percent_to_box(W,H,subhead_pos)
    draw_wrapped(draw, subhead_text, l, t, w, f_body, fill=col_txt)

    # Comment
    l,t,w,h = percent_to_box(W,H,comment_pos)
    draw_wrapped(draw, comment_text, l, t, w, f_body, fill=col_txt)

    # Meta (dates/id)
    l,t,w,h = percent_to_box(W,H,meta_pos)
    meta = f"Visit Date:  {visit_date}\nSurvey Date: {survey_date}\n{id_label}: {id_value}"
    draw_wrapped(draw, meta, l, t, w, f_small, fill=col_txt)

    # Footer
    l,t,w,h = percent_to_box(W,H,footer_pos)
    draw_wrapped(draw, footer_text.format(brand=brand), l, t, w, f_body, fill=col_txt)

    st.image(img, caption="Preview", use_column_width=True)

    # Downloads
    buf_png = io.BytesIO()
    img.save(buf_png, format="PNG")
    st.download_button("⬇️ Download PNG", data=buf_png.getvalue(), file_name=f"{brand}_certificate.png", mime="image/png")

    buf_pdf = io.BytesIO()
    img.convert("RGB").save(buf_pdf, format="PDF")
    st.download_button("⬇️ Download PDF", data=buf_pdf.getvalue(), file_name=f"{brand}_certificate.pdf", mime="application/pdf")

else:
    st.info("Upload a background image exported from your PowerPoint template to begin.")
    
st.markdown("---")
st.caption("Export a PowerPoint slide as PNG: File → Save As → PNG → choose the slide → upload here as your background.")
