import os
import sys
import json
import time
import re
import urllib.request
import urllib.parse
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

TARGET_DIR = os.path.join(config.DATA_DIR, "images", "components")
CREDITS_FILE = os.path.join(TARGET_DIR, "credits.json")

SEARCH_QUERIES = {
    ("atmega328p", "pinout"): "Atmega328 pinout",
    ("lm358", "pinout"): "LM358 pinout DIP-8",
    ("resistor_guide", "photo"): "electronic resistors photo",
    ("capacitor_guide", "photo"): "electrolytic capacitor",
    ("capacitor_guide", "pinout"): "radial capacitor pinout",
    ("hcsr04", "photo"): "HC-SR04 ultrasonic",
    ("hcsr04", "pinout"): "ultrasonic sensor module",
    ("hcsr04", "schematic"): "sonar principle diagram"
}

def search_one(query):
    api_url = (
        f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
        f"&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6&gsrlimit=3"
        f"&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=800&format=json"
    )
    req = urllib.request.Request(api_url, headers={
        "User-Agent": "ElectronicsDocApp/1.0 (educational component viewer; mailto:admin@example.org)"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for pid, p in pages.items():
                title = p.get("title", "")
                ii_list = p.get("imageinfo", [])
                if ii_list:
                    ii = ii_list[0]
                    thumb = ii.get("thumburl") or ii.get("url")
                    meta = ii.get("extmetadata", {})
                    artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip() or "Wikimedia Commons"
                    license_name = meta.get("LicenseShortName", {}).get("value", "CC / Open")
                    desc = ii.get("descriptionurl", "")
                    return {
                        "thumb_url": thumb,
                        "desc_url": desc,
                        "artist": artist,
                        "license": license_name,
                        "title": title
                    }
    except Exception as e:
        print(f"Error searching {query}: {e}")
    return None

def download_and_save(url, out_path):
    req = urllib.request.Request(url, headers={
        "User-Agent": "ElectronicsDocApp/1.0 (educational component viewer; mailto:admin@example.org)"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    temp_path = out_path + ".tmp"
    with open(temp_path, "wb") as f:
        f.write(data)
    img = Image.open(temp_path)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.paste(img, (0, 0), img.convert("RGBA"))
        bg.convert("RGB").save(out_path, "PNG")
    else:
        img.convert("RGB").save(out_path, "PNG")
    if os.path.isfile(temp_path):
        os.remove(temp_path)

def main():
    with open(CREDITS_FILE, "r", encoding="utf-8") as f:
        credits_data = json.load(f)

    for (cid, kind), q in SEARCH_QUERIES.items():
        out_png = os.path.join(TARGET_DIR, cid, f"{kind}.png")
        print(f"Searching for {cid}/{kind} with query '{q}'...")
        res = search_one(q)
        time.sleep(1.0)
        if res and res.get("thumb_url"):
            print(f"  Found: {res['title']} -> {res['thumb_url'][:60]}...")
            try:
                download_and_save(res["thumb_url"], out_png)
                print(f"  [OK] Saved {cid}/{kind}.png")
                if cid not in credits_data:
                    credits_data[cid] = {}
                credits_data[cid][kind] = {
                    "title": res["title"].replace("File:", "").replace(".jpg", "").replace(".png", "").replace(".svg", ""),
                    "author": res["artist"],
                    "license": res["license"],
                    "source": res["desc_url"],
                    "local_file": f"{cid}/{kind}.png"
                }
            except Exception as e:
                print(f"  [ERROR] {e}")
        else:
            print(f"  [WARN] No result for {q}")

    with open(CREDITS_FILE, "w", encoding="utf-8") as f:
        json.dump(credits_data, f, indent=2)
    print("Done finding remaining images!")

if __name__ == "__main__":
    main()
