"""Visual Reference Generator & Image Attachment Service.

Provides:
- Retrieval of manual diagrams and extracted figures for RAG answers.
- Crisp schematic and pinout diagrams for standard components.
- Attachment of user-captured hardware photos.
"""
import os
import re
from PIL import Image, ImageDraw, ImageFont

import config
import database as db
import services.components as comp_service


def get_manual_images_for_pages(manual_id, pages, max_images=3):
    """Retrieve extracted diagrams and high-res page illustrations for specific manual pages."""
    if not manual_id or not pages:
        return []

    images = []
    seen_paths = set()

    for pno in pages:
        # 1. First look for extracted figure/illustration images
        try:
            fig_rows = db.query(
                "SELECT image_path FROM manual_images WHERE manual_id=? AND page_number=?",
                (manual_id, pno)
            )
            for r in fig_rows:
                p = r.get("image_path")
                if p and os.path.isfile(p) and p not in seen_paths:
                    seen_paths.add(p)
                    images.append({
                        "path": p,
                        "caption": f"Manual Figure - Page {pno}",
                        "page": pno,
                        "kind": "illustration"
                    })
                    if len(images) >= max_images:
                        return images
        except Exception as e:
            print(f"[VISUAL_REF] Query error: {e}")

        # 2. If no embedded figures, check page render snapshot
        if len(images) < max_images:
            try:
                vis_path, kind = db.get_page_visual(manual_id, pno)
                if vis_path and os.path.isfile(vis_path) and vis_path not in seen_paths:
                    seen_paths.add(vis_path)
                    images.append({
                        "path": vis_path,
                        "caption": f"Manual Schematic / Page {pno}",
                        "page": pno,
                        "kind": kind or "page"
                    })
                    if len(images) >= max_images:
                        return images
            except Exception:
                pass

    return images


def get_component_reference_image(comp_id_or_name):
    """Generate or retrieve a crisp, styled reference visual (pinout & schematic) for a component."""
    config.ensure_dirs()
    comp = comp_service.find_component_match(comp_id_or_name)
    if not comp:
        return None

    cid = comp.get("id", "comp")
    out_path = os.path.join(config.IMAGES_DIR, f"ref_visual_{cid}.png")
    if os.path.isfile(out_path):
        return {
            "path": out_path,
            "caption": f"{comp.get('name')} - Pinout & Architecture",
            "kind": "component_reference"
        }

    # Render a high quality dark-emerald technical card (720x420)
    width, height = 760, 440
    img = Image.new("RGB", (width, height), color=(10, 15, 12))
    draw = ImageDraw.Draw(img)

    # Emerald border and accent header bar
    draw.rounded_rectangle([1, 1, width - 2, height - 2], radius=16, outline=(0, 255, 133), width=2)
    draw.rectangle([2, 2, width - 3, 56], fill=(16, 32, 22))
    draw.line([2, 56, width - 3, 56], fill=(0, 255, 133), width=1)

    # Use default or basic font safely across OS platforms
    font_large = ImageFont.load_default()
    font_med = ImageFont.load_default()
    font_mono = ImageFont.load_default()

    # Title & Category Badge
    name_str = comp.get("name", "Electronic Component").upper()
    cat_str = f"[{comp.get('category', 'Hardware')}]"
    draw.text((20, 18), name_str, fill=(0, 255, 133), font=font_large)
    draw.text((width - 240, 20), cat_str, fill=(167, 189, 174), font=font_med)

    # Specs & Function
    func_text = comp.get("function", "")[:95]
    draw.text((20, 68), f"FUNCTION: {func_text}", fill=(243, 251, 245), font=font_med)
    specs_text = comp.get("key_specs", "")[:95]
    draw.text((20, 92), f"SPECS: {specs_text}", fill=(107, 130, 115), font=font_med)

    # Symbol / Schematic Box
    sym = comp.get("symbol", "").strip()
    draw.rectangle([20, 120, 360, 410], fill=(4, 7, 5), outline=(23, 56, 34), width=1)
    draw.text((32, 130), "SCHEMATIC / PIN MAP", fill=(0, 255, 133), font=font_large)
    sym_lines = sym.splitlines()[:14]
    for idx, sl in enumerate(sym_lines):
        draw.text((32, 160 + idx * 16), sl, fill=(0, 255, 102), font=font_mono)

    # Pinout Description Box
    draw.rectangle([380, 120, width - 20, 410], fill=(4, 7, 5), outline=(23, 56, 34), width=1)
    draw.text((392, 130), "PIN ASSIGNMENTS & SIGNALS", fill=(0, 255, 133), font=font_large)
    pinout_text = comp.get("pinout", "").strip()
    pin_lines = [p.strip() for p in pinout_text.splitlines() if p.strip()][:12]
    for idx, pl in enumerate(pin_lines):
        draw.text((392, 160 + idx * 18), pl[:46], fill=(243, 251, 245), font=font_mono)

    try:
        img.save(out_path, format="PNG")
        return {
            "path": out_path,
            "caption": f"{comp.get('name')} · Pinout & Architecture",
            "kind": "component_reference"
        }
    except Exception as e:
        print(f"[VISUAL_REF] Failed to save component visual: {e}")
        return None
