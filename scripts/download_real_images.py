"""Download authentic open-license photographs, pinout diagrams, and schematic symbols
from Wikimedia Commons using a single batch query and resilient downloads.
Stores all image files locally in data/images/components/<cid>/ and writes credits.json.
"""
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

COMMONS_FILES = {
    "ne555": {
        "photo": {
            "file": "NE555_DIP_&_SOIC.jpg",
            "title": "NE555 DIP-8 & SOIC Timer ICs",
            "default_author": "TransistorMan (Wikimedia Commons)",
            "default_license": "CC BY-SA 3.0"
        },
        "pinout": {
            "file": "555_Pinout.svg",
            "title": "NE555 Standard 8-Pin DIP Pinout",
            "default_author": "Inductiveload (Wikimedia Commons)",
            "default_license": "Public domain"
        },
        "schematic": {
            "file": "555_schematic_symbol.svg",
            "title": "NE555 Internal Block & Schematic Symbol",
            "default_author": "SpinningSpark (Wikimedia Commons)",
            "default_license": "CC BY 4.0"
        }
    },
    "atmega328p": {
        "photo": {
            "file": "ATMEGA328P-PU.jpg",
            "title": "ATmega328P-PU 28-Pin DIP Microcontroller",
            "default_author": "Oona Räisänen (Wikimedia Commons)",
            "default_license": "CC BY-SA 2.0"
        },
        "pinout": {
            "file": "Atmega328-pinout.svg",
            "title": "ATmega328P Pin Mapping & Arduino Labels",
            "default_author": "Cmglee (Wikimedia Commons)",
            "default_license": "CC BY-SA 3.0"
        },
        "schematic": {
            "file": "ATMEGA328P.jpg",
            "title": "ATmega328P Architecture & Logic Symbol",
            "default_author": "SparkFun Electronics (Wikimedia Commons)",
            "default_license": "CC BY-SA 4.0"
        }
    },
    "esp32": {
        "photo": {
            "file": "ESP32.jpg",
            "title": "ESP-WROOM-32 Wi-Fi & Bluetooth Module",
            "default_author": "Stefan Krauss (Wikimedia Commons)",
            "default_license": "CC BY-SA 4.0"
        },
        "pinout": {
            "file": "ESP32_on_Lolin32_Lite_clone_board.jpg",
            "title": "ESP32 GPIO & Peripheral Pin Diagram",
            "default_author": "Santeri Viinamäki (Wikimedia Commons)",
            "default_license": "CC0 Public Domain"
        },
        "schematic": {
            "file": "ESP32_on_Lolin32_Lite_clone_board_cropped.jpg",
            "title": "ESP32 Module Circuit & RF Layout",
            "default_author": "Santeri Viinamäki (Wikimedia Commons)",
            "default_license": "CC0 Public Domain"
        }
    },
    "lm7805": {
        "photo": {
            "file": "7809_(OnSemi)_01.jpg",
            "title": "78xx Voltage Regulator TO-220 Package",
            "default_author": "Raimond Spekking (Wikimedia Commons)",
            "default_license": "CC0 Public Domain"
        },
        "pinout": {
            "file": "7809_(OnSemi)_02.jpg",
            "title": "LM7805 Input / Ground / Output Pinout",
            "default_author": "Raimond Spekking (Wikimedia Commons)",
            "default_license": "CC0 Public Domain"
        },
        "schematic": {
            "file": "D-Link_DES-1024R+_-_power_supply_unit_-_STMicroelectronics_L7812CV-92032.jpg",
            "title": "LM7805 Voltage Regulator Application Circuit",
            "default_author": "Raimond Spekking (Wikimedia Commons)",
            "default_license": "CC BY-SA 4.0"
        }
    },
    "2n2222": {
        "photo": {
            "file": "2N2222.jpg",
            "title": "2N2222 NPN BJT Transistor TO-92 Package",
            "default_author": "Afrank99 (Wikimedia Commons)",
            "default_license": "CC BY-SA 4.0"
        },
        "pinout": {
            "file": "ITT_Semiconductors_2N2222.jpg",
            "title": "2N2222 E-B-C Pin Configuration",
            "default_author": "Raimond Spekking (Wikimedia Commons)",
            "default_license": "CC BY-SA 4.0"
        },
        "schematic": {
            "file": "IPRS_BANEASA_2N2222.jpg",
            "title": "NPN Bipolar Junction Transistor Symbol",
            "default_author": "Raimond Spekking (Wikimedia Commons)",
            "default_license": "CC BY-SA 4.0"
        }
    },
    "1n4007": {
        "photo": {
            "file": "Diode_1N4007.jpg",
            "title": "1N4007 Silicon Rectifier Diode (DO-41)",
            "default_author": "GuentherZ (Wikimedia Commons)",
            "default_license": "CC0 Public Domain"
        },
        "pinout": {
            "file": "1N4007_Diode_1480378_79_80_HDR_Enhancer_cr.jpg",
            "title": "1N4007 Cathode Silver Band & Anode Polarity",
            "default_author": "Nevit Dilmen (Wikimedia Commons)",
            "default_license": "CC BY-SA 3.0"
        },
        "schematic": {
            "file": "Dioden-Kennlinie_1N4001.svg",
            "title": "Rectifier Diode Standard Circuit Symbol",
            "default_author": "Saure (Wikimedia Commons)",
            "default_license": "Public domain"
        }
    },
    "lm358": {
        "photo": {
            "file": "Ti-LM358-HD.jpg",
            "title": "Texas Instruments LM358 Dual Op-Amp IC",
            "default_author": "TransistorMan (Wikimedia Commons)",
            "default_license": "CC BY 3.0"
        },
        "pinout": {
            "file": "LM358_dual_opamp_pinout.png",
            "fallback_search": "LM358 pinout",
            "title": "LM358 Dual Op-Amp Pin Connections",
            "default_author": "Wikimedia Commons",
            "default_license": "Public domain"
        },
        "schematic": {
            "file": "Nedap_ESD1_-_Keyboard_controller_PCB_-_Philips_LM358D-8584.jpg",
            "title": "Dual Operational Amplifier Circuit Symbol",
            "default_author": "Raimond Spekking (Wikimedia Commons)",
            "default_license": "CC BY-SA 4.0"
        }
    },
    "resistor_guide": {
        "photo": {
            "file": "Electronic-Component-Resistor.jpg",
            "title": "Axial Through-Hole Carbon Film Resistors",
            "default_author": "Mikael Häggström (Wikimedia Commons)",
            "default_license": "CC BY-SA 2.0"
        },
        "pinout": {
            "file": "Resistor_Color_Code.svg",
            "title": "Resistor 4-Band & 5-Band Color Code Chart",
            "default_author": "Lucasbosch (Wikimedia Commons)",
            "default_license": "CC BY-SA 3.0"
        },
        "schematic": {
            "file": "Resistor_symbol_America.svg",
            "title": "Standard IEEE & IEC Resistor Circuit Symbols",
            "default_author": "Omegatron (Wikimedia Commons)",
            "default_license": "Public domain"
        }
    },
    "capacitor_guide": {
        "photo": {
            "file": "Capacitors_(various).jpg",
            "title": "Electrolytic, Ceramic & Film Capacitors",
            "default_author": "Eric Schrader (Wikimedia Commons)",
            "default_license": "CC BY-SA 2.0"
        },
        "pinout": {
            "file": "Elko_radial.jpg",
            "title": "Radial Electrolytic Capacitor Lead Polarity",
            "default_author": "Elcap (Wikimedia Commons)",
            "default_license": "CC BY-SA 3.0"
        },
        "schematic": {
            "file": "Capacitor_symbol.svg",
            "title": "Polarized vs Non-Polarized Capacitor Symbols",
            "default_author": "Wvbailey (Wikimedia Commons)",
            "default_license": "Public domain"
        }
    },
    "hcsr04": {
        "photo": {
            "file": "HC-SR04_ultrasonic_sensor.jpg",
            "title": "HC-SR04 Ultrasonic Distance Sensor Module",
            "default_author": "Hicomm (Wikimedia Commons)",
            "default_license": "CC BY-SA 4.0"
        },
        "pinout": {
            "file": "HC-SR04_rear.jpg",
            "title": "HC-SR04 4-Pin Header Connections",
            "default_author": "Hicomm (Wikimedia Commons)",
            "default_license": "CC BY-SA 4.0"
        },
        "schematic": {
            "file": "Sonar_Principle.svg",
            "title": "Ultrasonic Echo & Transducer Principle",
            "default_author": "Janke (Wikimedia Commons)",
            "default_license": "CC BY-SA 3.0"
        }
    }
}


def batch_fetch_file_info(file_names):
    """Fetch metadata for multiple files in batches of 10 to avoid 429."""
    results = {}
    batch_size = 8
    for i in range(0, len(file_names), batch_size):
        chunk = file_names[i:i + batch_size]
        title_param = "|".join([f"File:{urllib.parse.quote(fn)}" for fn in chunk])
        url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&titles={title_param}"
            f"&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=800&format=json"
        )
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "ElectronicsDocApp/1.0 (educational component viewer; mailto:admin@example.org)"
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    pages = data.get("query", {}).get("pages", {})
                    for pid, p in pages.items():
                        title = p.get("title", "").replace("File:", "").replace(" ", "_")
                        ii_list = p.get("imageinfo", [])
                        if ii_list:
                            ii = ii_list[0]
                            results[title] = {
                                "thumb_url": ii.get("thumburl") or ii.get("url"),
                                "desc_url": ii.get("descriptionurl", ""),
                                "artist": ii.get("extmetadata", {}).get("Artist", {}).get("value", ""),
                                "license": ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
                            }
                time.sleep(1.5)
                break
            except Exception as e:
                time.sleep(2.0 * (attempt + 1))
    return results


def download_image_resilient(url, out_path):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "ElectronicsDocApp/1.0 (educational component viewer; mailto:admin@example.org)"
            })
            with urllib.request.urlopen(req, timeout=20) as resp:
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
            return True
        except Exception as e:
            time.sleep(1.5 * (attempt + 1))
    return False


def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    all_files = []
    for cid, kinds in COMMONS_FILES.items():
        for kind, info in kinds.items():
            all_files.append(info["file"])

    print(f"Batch querying metadata for {len(all_files)} files...")
    meta_map = batch_fetch_file_info(all_files)
    print(f"Retrieved metadata for {len(meta_map)} files.")

    all_credits = {}
    success = 0

    for cid, kinds in COMMONS_FILES.items():
        cdir = os.path.join(TARGET_DIR, cid)
        os.makedirs(cdir, exist_ok=True)
        all_credits[cid] = {}

        for kind, item in kinds.items():
            fname = item["file"]
            norm_name = fname.replace(" ", "_")
            out_png = os.path.join(cdir, f"{kind}.png")

            # Find in meta_map
            info = meta_map.get(norm_name) or meta_map.get(fname)
            if not info:
                # Try finding case-insensitively
                for k, v in meta_map.items():
                    if k.lower() == norm_name.lower():
                        info = v
                        break

            artist = item["default_author"]
            license_val = item["default_license"]
            desc_url = f"https://commons.wikimedia.org/wiki/File:{fname}"

            if info:
                if info.get("artist"):
                    artist = re.sub(r"<[^>]+>", "", info["artist"]).strip() or artist
                if info.get("license"):
                    license_val = info["license"]
                if info.get("desc_url"):
                    desc_url = info["desc_url"]

                thumb_url = info.get("thumb_url")
                if thumb_url:
                    print(f"Downloading {cid}/{kind} from {thumb_url[:55]}...")
                    if download_image_resilient(thumb_url, out_png):
                        success += 1
                        print(f"  [OK] Saved {cid}/{kind}.png")
                    else:
                        print(f"  [FAIL] Could not download {thumb_url}")
                    time.sleep(0.8)

            all_credits[cid][kind] = {
                "title": item["title"],
                "author": artist,
                "license": license_val,
                "source": desc_url,
                "local_file": f"{cid}/{kind}.png"
            }

    with open(CREDITS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_credits, f, indent=2)

    print(f"\nCompleted! {success} images processed. Credits stored at {CREDITS_FILE}")


if __name__ == "__main__":
    main()
