from io import BytesIO

import pytest
from fastapi import HTTPException
from PIL import Image

from backend.app.services.avatar import normalize_avatar


def make_image(mode="RGB", image_format="PNG", size=(900, 700)):
    image = Image.new(mode, size, (32, 115, 78))
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


@pytest.mark.parametrize(
    "image_format,mode",
    [("JPEG", "RGB"), ("PNG", "RGB"), ("WEBP", "RGB"), ("PNG", "RGBA")],
)
def test_avatar_normalizes_allowed_images_to_small_jpeg(image_format, mode):
    raw = make_image(mode=mode, image_format=image_format)
    result = normalize_avatar(raw)
    with Image.open(BytesIO(result)) as saved:
        assert saved.format == "JPEG"
        assert saved.mode == "RGB"
        assert max(saved.size) <= 512
        assert len(result) <= 256 * 1024
        assert saved.info.get("exif") is None


def test_avatar_respects_exif_rotation():
    image = Image.new("RGB", (900, 600), "#246d51")
    exif = Image.Exif()
    exif[274] = 6
    output = BytesIO()
    image.save(output, "JPEG", exif=exif)
    result = normalize_avatar(output.getvalue())
    with Image.open(BytesIO(result)) as saved:
        assert saved.height > saved.width
        assert saved.getexif().get(274) is None


@pytest.mark.parametrize(
    "raw",
    [b"", b"not-an-image", b"X" * (5 * 1024 * 1024 + 1)],
    ids=["empty", "malformed", "oversized"],
)
def test_avatar_rejects_empty_malformed_or_oversized_files(raw):
    with pytest.raises(HTTPException) as error:
        normalize_avatar(raw)
    assert error.value.status_code == (413 if len(raw) > 5 * 1024 * 1024 else 422)


def test_avatar_does_not_accept_gif_disguised_as_image():
    output = BytesIO()
    Image.new("RGB", (32, 32), "#125835").save(output, format="GIF")
    with pytest.raises(HTTPException) as error:
        normalize_avatar(output.getvalue())
    assert error.value.detail["code"] == "INVALID_AVATAR"
