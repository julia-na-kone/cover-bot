import io
import textwrap
from PIL import Image, ImageDraw, ImageFont

TEMPLATE_PATH = "template.png"
FONT_PATH = "font.ttf"


SYSTEM_FONTS = [
    FONT_PATH,
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in SYSTEM_FONTS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_centered_text(draw, text, y, font, color, img_width):
    """Draw text centered horizontally at given y position."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (img_width - text_width) // 2
    draw.text((x, y), text, fill=color, font=font)
    return bbox[3] - bbox[1]  # return line height


def generate_cover(course: str, name: str, status: str, schedule: str = None) -> io.BytesIO:
    img = Image.open(TEMPLATE_PATH).copy()
    draw = ImageDraw.Draw(img)

    width, height = img.size
    color = "#000000"

    font_course = _load_font(22)
    font_name = _load_font(26)
    font_status = _load_font(22)
    font_schedule = _load_font(20)

    # Wrap long course names (max ~30 chars per line)
    wrapped_lines = textwrap.wrap(course, width=30)

    line_height_course = 30
    total_course_height = len(wrapped_lines) * line_height_course

    # Start course text at ~58% of image height
    course_y = int(height * 0.58)

    for line in wrapped_lines:
        _draw_centered_text(draw, line, course_y, font_course, color, width)
        course_y += line_height_course

    name_y = course_y + 16
    name_h = _draw_centered_text(draw, name, name_y, font_name, color, width)

    status_y = name_y + name_h + 14
    status_h = _draw_centered_text(draw, status, status_y, font_status, color, width)

    if schedule:
        schedule_y = status_y + status_h + 12
        _draw_centered_text(draw, schedule, schedule_y, font_schedule, color, width)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
