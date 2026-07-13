import trafilatura


def extract_url(url):
    downloaded = trafilatura.fetch_url(url)

    if not downloaded:
        return []

    text = trafilatura.extract(downloaded)

    return [{"page": 1, "text": text, "needs_ocr": False}]


# print(extract_url("https://en.wikipedia.org/wiki/Rabindranath_Tagore"))
