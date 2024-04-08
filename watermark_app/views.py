from django.shortcuts import render
from PIL import Image, ImageOps
import math
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.files.storage import default_storage


def resize_watermark(image_size, watermark):
    """Resize the watermark to the specified dimensions."""
    resized_watermark = watermark.resize(image_size, Image.Resampling.LANCZOS)
    return resized_watermark


def rotate_watermark(watermark, angle, original_size):
    """
    Rotate the watermark by the given angle without cropping edges, 
    and resize it to maintain the original size as closely as possible.
    
    :param watermark: PIL.Image object of the watermark.
    :param angle: Rotation angle in degrees.
    :param original_size: A tuple (width, height) specifying the desired dimensions 
                          to which the rotated image should be scaled.
    """
    rotated_watermark = watermark.rotate(angle, expand=True)
    original_ratio = min(original_size[0] / rotated_watermark.width, original_size[1] / rotated_watermark.height)
    new_size = (int(rotated_watermark.width * original_ratio), int(rotated_watermark.height * original_ratio))
    resized_rotated_watermark = rotated_watermark.resize(new_size, Image.ANTIALIAS)

    return resized_rotated_watermark


def adjust_opacity(watermark, opacity):
    """Adjust the opacity of the watermark."""
    assert 0 <= opacity <= 255, "Opacity must be between 0 and 255"
    if opacity < 255:
        alpha = watermark.split()[3]
        alpha = alpha.point(lambda p: p * opacity / 255)
        watermark.putalpha(alpha)
    return watermark


def apply_watermark(request):
    if request.method == "POST":
        image_file = request.FILES.get("image")
        if not image_file or not image_file.content_type.startswith("image"):
            return HttpResponseBadRequest(
                "Error: No image file provided or file is not an image"
            )

        watermark_file = request.FILES["watermark"]
        opacity = int(request.POST["opacity"])
        rotation_angle = -int(request.POST.get("rotation", 0))

        watermark_path = default_storage.save(
            "temp/" + watermark_file.name, watermark_file
        )
        watermark = Image.open(watermark_path).convert("RGBA")
        watermark = adjust_opacity(watermark, opacity)
        watermark = rotate_watermark(watermark, rotation_angle, watermark.size)

        image_path = default_storage.save("temp/" + image_file.name, image_file)
        image = Image.open(image_path)

        watermark_size_x = int(request.POST["sizeX"])
        watermark_size_y = int(request.POST["sizeY"])
        watermark_resized = resize_watermark(
            (watermark_size_x, watermark_size_y), watermark
        )

        x_position = int(request.POST["watermarkX"])
        y_position = int(request.POST["watermarkY"])

        transparent = Image.new("RGBA", (image.width, image.height), (0, 0, 0, 0))
        transparent.paste(image, (0, 0))
        transparent.paste(
            watermark_resized, (x_position, y_position), mask=watermark_resized
        )
        final_image = transparent.convert("RGB")

        response = HttpResponse(content_type="image/png")
        final_image.save(response, "PNG")
        response["Content-Disposition"] = 'attachment; filename="watermarked_image.png"'

        default_storage.delete(image_path)
        default_storage.delete(watermark_path)

        return response
    else:
        return render(request, "watermark_app/index.html")
