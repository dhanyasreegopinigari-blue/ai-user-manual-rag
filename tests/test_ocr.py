from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

IMAGE_PATH = "test_hardware.jpg"


print("Opening image...")
image = Image.open(IMAGE_PATH).convert("RGB")

print(f"Original image size: {image.size}")

# --------------------------------------------------
# 1. Enlarge the image
# --------------------------------------------------
scale = 3

large = image.resize(
    (image.width * scale, image.height * scale),
    Image.Resampling.LANCZOS
)

# --------------------------------------------------
# 2. Convert to grayscale
# --------------------------------------------------
gray = ImageOps.grayscale(large)

# --------------------------------------------------
# 3. Improve contrast
# --------------------------------------------------
contrast = ImageEnhance.Contrast(gray).enhance(2.0)

# --------------------------------------------------
# 4. Sharpen
# --------------------------------------------------
sharp = contrast.filter(ImageFilter.SHARPEN)
sharp = sharp.filter(ImageFilter.SHARPEN)

# --------------------------------------------------
# OCR function
# --------------------------------------------------
def run_ocr(name, img):
    print(f"\n========== {name} ==========")

    text = pytesseract.image_to_string(
        img,
        config="--psm 11"
    )

    text = text.strip()

    if text:
        print(text)
    else:
        print("[No text detected]")


# Test different versions
run_ocr("ORIGINAL", image)
run_ocr("ENLARGED", large)
run_ocr("GRAYSCALE + CONTRAST + SHARPEN", sharp)

print("\n================================")
print("OCR preprocessing test completed.")