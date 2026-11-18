from bs4 import BeautifulSoup


def extract_content(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = description_tag.get("content", "").strip() if description_tag else ""

    for element in soup.select("script, style, noscript, nav, footer"):
        element.decompose()

    content = soup.find("main") or soup.find("article") or soup.body or soup
    headings = [
        heading.get_text(" ", strip=True)
        for heading in content.select("h1, h2, h3", limit=25)
    ]
    text = " ".join(content.get_text(" ", strip=True).split())

    return {
        "title": title,
        "description": description,
        "headings": headings,
        "text": text[:12_000],
    }