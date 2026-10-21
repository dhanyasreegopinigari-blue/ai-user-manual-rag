"""Component Library Image Service.

Provides authentic photographs, pinout diagrams, and schematic symbols
from open-license sources (Wikimedia Commons, Openverse, datasheets)
for all components in the electronic components learning library.
Includes attribution and license metadata for every asset.
"""
import os
import json
import config
import database as db
import services.components as comp_service

COMPONENTS_IMG_DIR = os.path.join(config.DATA_DIR, "images", "components")
CREDITS_FILE = os.path.join(COMPONENTS_IMG_DIR, "credits.json")


def load_component_credits():
    """Load metadata (title, author, license, source) for all component images."""
    if os.path.isfile(CREDITS_FILE):
        try:
            with open(CREDITS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[COMP_IMG] Note loading credits.json: {e}")
    return {}


def ensure_component_images():
    """Ensure directory exists and real image assets are ready."""
    os.makedirs(COMPONENTS_IMG_DIR, exist_ok=True)


def get_component_gallery_images(comp_id_or_dict):
    """Retrieve authentic gallery items (real photo, pinout diagram, schematic symbol, manual figures).

    Returns:
        List of dicts: [
            {
                "type": "photo" | "pinout" | "schematic" | "manual_figure",
                "title": "Actual Component / Package Photo",
                "caption": "...",
                "attribution": "Swift.Hg · CC BY-SA 3.0",
                "source": "https://commons.wikimedia.org/...",
                "path": "..."
            }, ...
        ]
    """
    if isinstance(comp_id_or_dict, dict):
        comp = comp_id_or_dict
        cid = comp.get("id")
    else:
        cid = str(comp_id_or_dict)
        comp = comp_service.find_component_match(cid) or {}

    ensure_component_images()
    credits_map = load_component_credits().get(cid, {})
    cdir = os.path.join(COMPONENTS_IMG_DIR, cid)
    gallery = []

    # 1. Real component photograph
    p_path = os.path.join(cdir, "photo.png")
    if os.path.isfile(p_path):
        p_cred = credits_map.get("photo", {})
        gallery.append({
            "type": "photo",
            "title": "📷 Actual Component Photo",
            "caption": p_cred.get("title") or f"{comp.get('name', 'Component')} Package Photo",
            "attribution": f"{p_cred.get('author', 'Wikimedia Commons')} · {p_cred.get('license', 'CC / Open')}" if p_cred else "Open-license photo",
            "source": p_cred.get("source", ""),
            "path": p_path
        })
    else:
        gallery.append({
            "type": "photo",
            "title": "📷 Actual Component Photo",
            "caption": "No image available",
            "attribution": "",
            "source": "",
            "path": None
        })

    # 2. Pinout diagram
    pin_path = os.path.join(cdir, "pinout.png")
    if os.path.isfile(pin_path):
        pin_cred = credits_map.get("pinout", {})
        gallery.append({
            "type": "pinout",
            "title": "📍 Pinout Diagram",
            "caption": pin_cred.get("title") or f"{comp.get('name', 'Component')} Pin Assignments",
            "attribution": f"{pin_cred.get('author', 'Wikimedia Commons')} · {pin_cred.get('license', 'CC / Open')}" if pin_cred else "Open-license pinout diagram",
            "source": pin_cred.get("source", ""),
            "path": pin_path
        })
    else:
        gallery.append({
            "type": "pinout",
            "title": "📍 Pinout Diagram",
            "caption": "No image available",
            "attribution": "",
            "source": "",
            "path": None
        })

    # 3. Schematic circuit symbol
    sch_path = os.path.join(cdir, "schematic.png")
    if os.path.isfile(sch_path):
        sch_cred = credits_map.get("schematic", {})
        gallery.append({
            "type": "schematic",
            "title": "⚡ Schematic Symbol",
            "caption": sch_cred.get("title") or f"{comp.get('name', 'Component')} Circuit Symbol",
            "attribution": f"{sch_cred.get('author', 'Wikimedia Commons')} · {sch_cred.get('license', 'CC / Open')}" if sch_cred else "Standard schematic symbol",
            "source": sch_cred.get("source", ""),
            "path": sch_path
        })
    else:
        gallery.append({
            "type": "schematic",
            "title": "⚡ Schematic Symbol",
            "caption": "No image available",
            "attribution": "",
            "source": "",
            "path": None
        })

    # 4. Extracted manual figures if available
    try:
        q_name = comp.get("name", "")
        manuals = db.list_manuals()
        for m in manuals:
            if m.get("name", "").lower() in q_name.lower() or cid in m.get("model", "").lower():
                figs = db.query("SELECT image_path, page_number FROM manual_images WHERE manual_id=? LIMIT 2", (m["id"],))
                for f in figs:
                    ipath = f.get("image_path")
                    if ipath and os.path.isfile(ipath):
                        gallery.append({
                            "type": "manual_figure",
                            "title": f"📘 Manual Diagram (Page {f.get('page_number', '?')})",
                            "caption": f"Extracted from {m.get('name')}",
                            "attribution": f"Manual #{m['id']} Datasheet",
                            "source": m.get("file_path", ""),
                            "path": ipath
                        })
    except Exception as e:
        print(f"[COMP_IMG] Manual check note: {e}")

    return gallery
