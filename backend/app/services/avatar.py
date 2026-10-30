from io import BytesIO
from threading import Lock

from backend.app.errors import api_error

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 64_000_000
MAX_RESULT_BYTES = 256 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "HEIF"}
_image_lock = Lock()


def normalize_avatar(raw: bytes) -> bytes:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise api_error(413, "AVATAR_TOO_LARGE", "Фото перевищує 5 MiB")
    if not raw:
        raise api_error(422, "INVALID_AVATAR", "Фото порожнє")
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
        from pillow_heif import register_heif_opener

        with _image_lock:
            register_heif_opener()
            with Image.open(BytesIO(raw)) as original:
                if original.format not in ALLOWED_FORMATS:
                    raise api_error(422, "INVALID_AVATAR", "Непідтримуваний формат фото")
                width, height = original.size
                if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                    raise api_error(
                        422, "INVALID_AVATAR", "Зображення має завелику роздільність"
                    )
                original.seek(0)
                rotated = ImageOps.exif_transpose(original)
                rotated.thumbnail((512, 512), Image.Resampling.LANCZOS)
                if rotated.mode in {"RGBA", "LA"} or "transparency" in rotated.info:
                    image = Image.new("RGB", rotated.size, (255, 255, 255))
                    if rotated.mode != "RGBA":
                        rotated = rotated.convert("RGBA")
                    image.paste(rotated, mask=rotated.getchannel("A"))
                else:
                    image = rotated.convert("RGB")

                for quality in (88, 80, 72, 64, 56, 48):
                    out = BytesIO()
                    image.save(out, format="JPEG", quality=quality, optimize=True)
                    if out.tell() <= MAX_RESULT_BYTES:
                        return out.getvalue()
    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        OSError,
        ValueError,
        SyntaxError,
    ) as exc:
        raise api_error(422, "INVALID_AVATAR", "Не вдалося прочитати фото") from exc
    raise api_error(422, "INVALID_AVATAR", "Фото неможливо стиснути до 256 KiB")
