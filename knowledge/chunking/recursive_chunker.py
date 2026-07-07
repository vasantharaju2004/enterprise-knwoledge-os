def chunk_recursive(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """
    split text into overlapping chunks, trying to break at
    paragraph boundaries first, then sentences, then falling
    back to raw charcter slicing as a last resort.


    chunk_size: target max characters per chunk
    overlap: characters repeated at the start of the next chunk,
             so context isn't lost right at a cut point


    """

    separators = ["\n\n", "\n", ".", " "]

    def split_recursive(text: str, seps: list[str]) -> list[str]:
        if len(text) <= chunk_size:
            return [text]
        if not seps:
            return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        sep = seps[0]
        parts = [p for p in text.split(sep) if p.strip()]

        result = []

        for part in parts:
            if len(part) > chunk_size:
                # this price is still too big - recursive with the next separator
                result.extend(split_recursive(part, seps[1:]))
            else:
                result.append(part)

        return result

    # Try splitting on paragraphs first
    pieces = split_recursive(text, separators)

    chunks = []
    current = ""

    # main chunking according to size conditions-> logic
    for piece in pieces:
        if current:
            candidate = current + "\n\n" + piece
        else:
            candidate = piece

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            if current:
                overlap_text = current[-overlap:]
            else:
                overlap_text = ""
            current = (overlap_text + "\n\n" + piece).strip()

    # Don't forget to add the last chunk
    if current:
        chunks.append(current)

    return chunks
