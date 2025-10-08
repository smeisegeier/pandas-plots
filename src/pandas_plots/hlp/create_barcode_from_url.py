import re
from io import BytesIO

import requests
from matplotlib import pyplot as plt
from PIL import Image

# from devtools import debug

URL_REGEX = r"^(?:http|ftp)s?://"

def create_barcode_from_url(
    url: str,
    output_path: str | None = None,
    show_image: bool = False,
):
    """
    Create a barcode from the given URL. Uses "QR Code" from DENSO WAVE INCORPORATED.

    Args:
        url (str): The URL to encode in the barcode.
        output_path (str | None, optional): The path to save the barcode image. Defaults to None.
        show_image (bool, optional): Whether to display the barcode image. Defaults to False.
    """
    WIDTH = 400
    HEIGHT = 400

    if not re.match(URL_REGEX, url):
        print("💡 Not a valid URL")

    image = requests.get(
        # f"https://chart.googleapis.com/chart?chs={WIDTH}x{HEIGHT}&cht=qr&chl={url}"
        f"https://api.qrserver.com/v1/create-qr-code/?size={WIDTH}x{HEIGHT}&data={url}"
    )
    image.raise_for_status()

    # * write binary content to file
    if output_path:
        with open(output_path, "wb") as qr:
            qr.write(image.content)

    # * Load the image from the response content
    if show_image:
        img = Image.open(BytesIO(image.content))
        plt.imshow(img)
        # plt.axis('off')  # Turn off axis numbers
        plt.show()