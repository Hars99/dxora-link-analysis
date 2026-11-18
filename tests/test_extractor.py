from app.extractor import extract_content


def test_extract_content_keeps_business_text():
    html = """
    <html>
      <head>
        <title>Example Studio</title>
        <meta name="description" content="Web design for small businesses">
      </head>
      <body>
        <nav>Home | Contact</nav>
        <main>
          <h1>Web Design</h1>
          <h2>E-commerce Development</h2>
          <p>We build online stores for local retailers.</p>
          <script>console.log("tracking")</script>
        </main>
      </body>
    </html>
    """

    result = extract_content(html)

    assert result["title"] == "Example Studio"
    assert result["description"] == "Web design for small businesses"
    assert result["headings"] == ["Web Design", "E-commerce Development"]
    assert "We build online stores for local retailers." in result["text"]
    assert "Home | Contact" not in result["text"]
    assert "tracking" not in result["text"]