# Website Link Analysis API

A FastAPI service that reads a public website and returns a structured analysis of its business, competitors, search queries, SEO opportunities, services, and target audience. Built for the Dxora Technologies Python practical test.

The API fetches one page, extracts its visible content with BeautifulSoup, and sends that content to Groq for analysis. Pydantic validates the response before FastAPI returns it. The deployed API exposes an interactive Swagger UI at `/docs`.

## Quick start

Use Python 3.10 or newer. Run the commands from the repository root.

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

**macOS or Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Add your own key to the local `.env` file.

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

Start the app using the virtual environment. Open [Swagger UI](http://localhost:4000/docs) when Uvicorn is running.

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 4000 --env-file .env
```

```bash
.venv/bin/python -m uvicorn app.main:app --reload --port 4000 --env-file .env
```

Keep `.env` out of Git. Commit `.env.example` with an empty key value so reviewers can configure their own environment.

## API

`POST /link-analysis` accepts a JSON object with one field, `url`. Use a public HTTP or HTTPS website with readable HTML.

```json
{
  "url": "https://www.apple.com/in/"
}
```

In Swagger, open **POST /link-analysis**, select **Try it out**, paste the request, and select **Execute**. You can also call the API from the terminal.

**Windows PowerShell**

```powershell
Invoke-RestMethod -Uri "http://localhost:4000/link-analysis" `
  -Method Post -ContentType "application/json" `
  -Body '{"url":"https://www.apple.com/in/"}'
```

**macOS or Linux**

```bash
curl -sS http://localhost:4000/link-analysis \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.apple.com/in/"}'
```

### Successful response

The response contains `success`, `website`, `brand`, and `analysis`. The `brand` object includes the name, category, summary, and main products and services. Download the [full Apple India response](examples/apple-analysis.json) for an example of the five analysis sections.

| Analysis field | Contents |
| --- | --- |
| `competitor_analysis` | Brand strengths, positioning opportunities, and AI-suggested competitors with areas of overlap, potential strengths, and possible gaps. |
| `target_search_queries` | Five distinct search queries with platform, intent, business relevance, and audience. Together they cover Google, Facebook, Instagram, LinkedIn, and X. |
| `seo_improvements` | Primary, secondary, and long-tail keywords, a suggested page title and meta description, and ideas for supporting content. |
| `top_services` | Up to five main services or offerings, with a description, target industry, target customer, benefit, and evidence label. |
| `target_audience` | Primary and secondary audiences, industries, business types, customer profiles, geography when available, needs, interests, and suggested marketing segments. |

Competitor entries are unverified AI suggestions. Search terms are recommendations based on the page. Service entries use `website_content` for offerings supported by the page and `inferred` for model inferences.

### Errors

| HTTP status | Meaning |
| --- | --- |
| `400` | The URL passed the request format check but points to a disallowed destination or port. |
| `422` | The request body or URL format is invalid, or the fetched page contains no readable text. |
| `502` | The website or Groq request failed, or the generated analysis failed validation. |
| `503` | The Groq API key is missing from the application environment. |

The application returns a short `detail` message for failures it handles. Provider diagnostics stay in server logs.

## How it works

1. **Validate and fetch.** FastAPI validates the request shape. The fetcher accepts HTTP and HTTPS on standard ports, resolves the hostname, checks the resolved address, and connects directly to a checked public IP. It repeats the check for redirect destinations and retains the original hostname for HTTPS verification. These checks reduce the risk of server-side request forgery, where a supplied URL could otherwise cause the server to fetch internal resources.
2. **Extract and limit content.** BeautifulSoup reads the title, meta description, headings, and main page text. The fetcher limits redirects and HTML size, and the extractor caps the main text at 12,000 characters.
3. **Generate and validate.** One Groq request uses JSON Object Mode and includes the expected schema in the prompt. Pydantic checks the five analysis sections, distinct query count, supported platform coverage, and service evidence labels.

The application analyzes one HTML page per request. Sites that build their content in JavaScript or restrict automated access may yield limited text or a fetch error. Analysis quality depends on the content available from that page.

## Verification

| Check | Result |
| --- | --- |
| Apple India homepage | Local request returned HTTP `200` and all five analysis sections in **6,957 ms**. |
| Internal loopback URL `http://127.0.0.1` | Local endpoint returned HTTP `400`. |
| Invalid URL such as `not-a-url` | Local endpoint returned HTTP `422`. |

The Apple timing is one local end-to-end observation, including website fetching and the LLM call. The response identified Apple and included products visible in the extracted page. The test establishes that the pipeline worked for that input. Broader accuracy and latency measurements require a shared set of test pages across providers.

Run the extractor test after installing `pytest` in the virtual environment.

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

## LLM comparison

Prices are standard paid text rates in USD per million tokens, checked on **18 November 2026**. Each cost estimate assumes **2,000 input tokens and 1,000 output tokens**. Token usage and per-request costs vary with the page and response length.

| Provider and model | Input limit or context window | Input / output price | Estimated cost per analysis | JSON support and evidence |
| --- | ---: | ---: | ---: | --- |
| Groq · `openai/gpt-oss-20b` | 131,072 context | $0.075 / $0.30 | $0.00045 | JSON Object Mode with local Pydantic validation in this project. The Apple test succeeded in 6.957 s end to end. [Model and pricing](https://console.groq.com/docs/model/openai/gpt-oss-20b) · [JSON modes](https://console.groq.com/docs/structured-outputs) |
| Google · `gemini-3.5-flash-lite` | 1,048,576 input | $0.30 / $2.50 | $0.00310 | Structured output supported. Google describes it as a low-latency model. The project’s Prepay balance blocked generation during local testing, so application latency and quality remain unmeasured. [Model](https://aistudio.google.com/docs/models/gemini-3.5-flash-lite) · [Pricing](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite) |
| OpenAI · `gpt-5.4-mini` | 400,000 context | $0.75 / $4.50 | $0.00600 | Structured Outputs supported. OpenAI positions it for efficient, high-volume workloads. Application latency and quality remain unmeasured. [Model and pricing](https://developers.openai.com/api/docs/models/gpt-5.4-mini) |

**Recommendation.** Use Groq for this demo because it produced a valid response in the live test and has the lowest estimated paid cost among the three models. Gemini Flash-Lite is a fallback candidate for a project with active API access. To compare accuracy, use the same set of pages for each model and check whether the reported services appear on the page, inferred entries are marked correctly, and search queries reflect the business.

**Cost controls.** Extract readable text before calling the LLM, cap the amount of text sent, and generate all five sections in one request. Keep the output concise. If repeated requests become common, caching validated analyses for a short time can reduce repeat calls.

## Deployment

For a [Render Web Service](https://render.com/docs/deploy-fastapi), connect the repository and use the following settings.

| Setting | Value |
| --- | --- |
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Environment | Set `GROQ_API_KEY` and `GROQ_MODEL` in the hosting dashboard. |

Open `/docs` on the deployed service and repeat the sample request. Use the public Swagger URL as the demo link.

## Project structure

| Path | Purpose |
| --- | --- |
| `app/main.py` | FastAPI route and HTTP error handling |
| `app/fetcher.py` | URL checks, bounded fetches, and redirect handling |
| `app/extractor.py` | HTML parsing and text extraction |
| `app/llm.py` | Groq request, prompt, and response parsing |
| `app/schemas.py` | Pydantic request and response models |
| `tests/test_extractor.py` | Extraction unit test |
| `examples/apple-analysis.json` | Saved live response from the Apple India test |
