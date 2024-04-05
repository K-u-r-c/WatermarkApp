from django.shortcuts import render
from PIL import Image
from django.http import HttpResponse, HttpResponseBadRequest
from django.core.files.storage import default_storage
import io
from zipfile import ZipFile


def resize_watermark(image_size, watermark):
    """
    Resize the watermark to fit the image size while maintaining its aspect ratio.
    If the watermark is larger than the image, it will be scaled down to fit.
    """
    image_width, image_height = image_size
    watermark_width, watermark_height = watermark.size

    # Calculate the scaling factors for width and height
    width_ratio = image_width / watermark_width
    height_ratio = image_height / watermark_height
    scale_ratio = min(width_ratio, height_ratio)

    # If the scale ratio is less than 1, the watermark needs to be scaled down
    if scale_ratio < 1:
        new_width = int(watermark_width * scale_ratio)
        new_height = int(watermark_height * scale_ratio)
        resized_watermark = watermark.resize(
            (new_width, new_height), Image.Resampling.LANCZOS
        )
    else:
        # If the watermark is smaller than the image and doesn't need scaling,
        # it's returned as is.
        resized_watermark = watermark

    return resized_watermark


def apply_watermark(request):
    if request.method == "POST":
        image_files = request.FILES.getlist("images")

        # Validate each image file
        for image_file in image_files:
            if not image_file.content_type.startswith("image"):
                return HttpResponseBadRequest("Error: Only image files are allowed.")

        image_files = request.FILES.getlist(
            "images"
        )  # Adjusted to handle multiple files
        watermark_file = request.FILES["watermark"]
        opacity = int(request.POST["opacity"])  # Get the opacity value from the form

        # Create a ZIP file in memory for storing all the watermarked images
        in_memory_zip = io.BytesIO()

        with ZipFile(in_memory_zip, "w") as zipfile:
            watermark_path = default_storage.save(
                "temp/" + watermark_file.name, watermark_file
            )
            watermark = Image.open(watermark_path).convert("RGBA")
            watermark = adjust_opacity(watermark, opacity)

            for image_file in image_files:
                image_path = default_storage.save("temp/" + image_file.name, image_file)
                image = Image.open(image_path)

                # Resize watermark for each image
                watermark_resized = resize_watermark(
                    (image.width, image.height), watermark
                )

                # Calculate the position to paste the watermark so it's centered
                x_position = (image.width - watermark_resized.width) // 2
                y_position = (image.height - watermark_resized.height) // 2

                # Combine the image with the watermark
                transparent = Image.new(
                    "RGBA", (image.width, image.height), (0, 0, 0, 0)
                )
                transparent.paste(image, (0, 0))
                transparent.paste(
                    watermark_resized, (x_position, y_position), mask=watermark_resized
                )
                final_image = transparent.convert("RGB")

                # Save the watermarked image to the ZIP file
                img_byte_arr = io.BytesIO()
                final_image.save(img_byte_arr, format="JPEG")
                img_byte_arr = img_byte_arr.getvalue()
                zipfile.writestr(image_file.name, img_byte_arr)

                # Clean up temporary image file
                default_storage.delete(image_path)

            # Clean up temporary watermark file
            default_storage.delete(watermark_path)

        # Prepare the ZIP file to be sent in the response
        in_memory_zip.seek(0)
        response = HttpResponse(in_memory_zip, content_type="application/zip")
        response["Content-Disposition"] = (
            'attachment; filename="watermarked_images.zip"'
        )

        return response
    else:
        return render(request, "watermark_app/index.html")


def adjust_opacity(watermark, opacity):
    """Adjust the opacity of the watermark."""
    assert 0 <= opacity <= 255, "Opacity must be between 0 and 255"
    if opacity < 255:
        alpha = watermark.split()[3]
        alpha = alpha.point(lambda p: p * opacity / 255)
        watermark.putalpha(alpha)
    return watermark
