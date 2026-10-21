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
    win.resize(1360, 880)
    win.show()

    os.makedirs("screenshots", exist_ok=True)

    # 1. Component Library with Realistic Images & Attributions
    win.navigate_to(2)
    # Expand first card details so gallery is visible
    if win.cards_lay.count() > 1:
        first_card = win.cards_lay.itemAt(0).widget()
        if hasattr(first_card, "toggle_details"):
            first_card.toggle_details()
    app.processEvents()
    time.sleep(0.4)
    app.processEvents()
    win.grab().save("screenshots/10_realistic_component_library.png")
    print("Saved 10_realistic_component_library.png")

    # 2. Chat with clearly visible sidebar toggle button (Expanded)
    win.navigate_to(1)
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    win.grab().save("screenshots/11_sidebar_expanded.png")
    print("Saved 11_sidebar_expanded.png")

    # 2b. Chat with collapsed sidebar
    win.toggle_sidebar()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    win.grab().save("screenshots/12_sidebar_collapsed.png")
    print("Saved 12_sidebar_collapsed.png")
    win.toggle_sidebar() # expand back

    # 3. Light Theme Component Library
    win.toggle_theme() # switch to light
    win.navigate_to(2)
    app.processEvents()
    time.sleep(0.4)
    app.processEvents()
    win.grab().save("screenshots/13_light_theme_library.png")
    print("Saved 13_light_theme_library.png")
    win.toggle_theme() # switch back to dark

    # 4. Lightbox Side-by-Side Comparison
    photo_path = comp_img_service.get_component_gallery_images("ne555")[0]["path"]
    schem_path = comp_img_service.get_component_gallery_images("ne555")[2]["path"]
    lightbox = ZoomableLightboxDialog(win, photo_path, title="NE555 Timer Photo", compare_path=schem_path, compare_title="NE555 Schematic Symbol")
    lightbox.resize(1100, 720)
    lightbox.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    lightbox.grab().save("screenshots/14_lightbox_comparison.png")
    print("Saved 14_lightbox_comparison.png")
    lightbox.close()

    win.close()
    print("All verification screenshots captured successfully!")

if __name__ == "__main__":
    capture()
