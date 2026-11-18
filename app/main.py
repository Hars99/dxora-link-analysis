from fastapi import FastAPI, HTTPException

from app.extractor import extract_content
from app.fetcher import InvalidWebsiteURL, WebsiteFetchError, fetch_html
from app.llm import LLMError, LLMNotConfigured, analyze_website
from app.schemas import LinkAnalysisRequest, LinkAnalysisResponse


app = FastAPI(title="Website Link Analysis")


@app.post("/link-analysis", response_model=LinkAnalysisResponse)
def analyze_link(request: LinkAnalysisRequest) -> LinkAnalysisResponse:
    website = str(request.url)

    try:
        html = fetch_html(website)
        content = extract_content(html)
        if not content["text"]:
            raise HTTPException(422, "The website has no readable page text.")

        result = analyze_website(website, content)
    except InvalidWebsiteURL as exc:
        raise HTTPException(400, str(exc)) from exc
    except WebsiteFetchError as exc:
        raise HTTPException(502, str(exc)) from exc
    except LLMNotConfigured as exc:
        raise HTTPException(503, str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(502, str(exc)) from exc

    return LinkAnalysisResponse(
        success=True,
        website=website,
        brand=result.brand,
        analysis=result.analysis,
    )