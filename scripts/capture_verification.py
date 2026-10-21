import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import time

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from ui.controller import MainWindow
from ui.view import ManualPickerDialog, ZoomableLightboxDialog
import services.component_images as comp_img_service

def capture():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.resize(1280, 850)
    win.show()

    os.makedirs("screenshots", exist_ok=True)

    # 1. Dashboard with hardware result and large images
    photo_path = comp_img_service.get_component_gallery_images("ne555")[0]["path"]
    schem_path = comp_img_service.get_component_gallery_images("ne555")[2]["path"]
    win.show_hardware({
        "preview": photo_path,
        "hardware": {
            "product_name": "NE555 Precision Timer",
            "model": "NE555P",
            "part_number": "NE555",
            "hardware_type": "Integrated Circuit (Timer)"
        },
        "match_info": {
            "source": "visual_image",
            "matched_image_path": schem_path,
            "page": 4,
            "score_pct": 98
        }
    })
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    win.grab().save("screenshots/1_dashboard_large_images.png")
    print("Saved 1_dashboard_large_images.png")

    # 1b. Dashboard stacked vertical layout
    win.toggle_dash_images_layout()
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()
    win.grab().save("screenshots/1b_dashboard_stacked_layout.png")
    print("Saved 1b_dashboard_stacked_layout.png")
    win.toggle_dash_images_layout() # toggle back

    # 2. Chat with Manual Button
    win.navigate_to(1)
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()
    win.grab().save("screenshots/2_chat_with_manual_button.png")
    print("Saved 2_chat_with_manual_button.png")

    # 2b. Manual Picker Dialog
    dlg = ManualPickerDialog(win, active_manual_id=None)
    dlg.resize(640, 520)
    dlg.show()
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()
    dlg.grab().save("screenshots/2b_manual_picker_dialog.png")
    print("Saved 2b_manual_picker_dialog.png")
    dlg.close()

    # 3. Component Library with Visual Gallery
    win.navigate_to(2)
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    win.grab().save("screenshots/3_component_library_gallery.png")
    print("Saved 3_component_library_gallery.png")

    # 4. Lightbox Side-by-Side Comparison
    lightbox = ZoomableLightboxDialog(win, photo_path, title="NE555 Timer Photo", compare_path=schem_path, compare_title="NE555 Schematic Symbol")
    lightbox.resize(1100, 720)
    lightbox.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    lightbox.grab().save("screenshots/4_lightbox_comparison.png")
    print("Saved 4_lightbox_comparison.png")
    lightbox.close()

    win.close()
    print("All verification screenshots captured successfully!")

if __name__ == "__main__":
    capture()
