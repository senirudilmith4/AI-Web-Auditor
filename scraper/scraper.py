import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


def scrape_metrics(url: str) -> dict:
    """
    - Meta title and meta description
    - Heading counts (H1–H3)
    - Word count
    - Number of images and percentage missing alt text
    - Internal vs external links
    - Number of CTAs (buttons + primary action links)
    
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch URL: {e}")

    soup = BeautifulSoup(response.text, "html.parser")
    base_domain = urlparse(url).netloc

    # Meta tags 
    meta_title = soup.title.get_text(strip=True) if soup.title else ""

    meta_desc_tag = soup.find("meta", attrs={"name": "meta-description"}) or \
                    soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag["content"].strip() if meta_desc_tag else ""

    # Headings
    h1s = [tag.get_text(strip=True) for tag in soup.find_all("h1")]
    h2s = [tag.get_text(strip=True) for tag in soup.find_all("h2")]
    h3s = [tag.get_text(strip=True) for tag in soup.find_all("h3")]

    # Word count (visible text only)
    # Remove script and style tags before counting
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    visible_text = soup.get_text(separator=" ", strip=True)
    word_count = len(visible_text.split())

    # Images & alt text
    images = soup.find_all("img")
    total_images = len(images)
    missing_alt = sum(
        1 for img in images
        if not img.get("alt") or img.get("alt").strip() == ""
    )
    pct_missing_alt = (
        round((missing_alt / total_images) * 100, 1) if total_images > 0 else 0
    )

    # Links(internal vs external)
    all_links = soup.find_all("a", href=True)
    internal_links = []
    external_links = []

    for link in all_links:
        href = link["href"].strip()
        # Skip anchors, mailto, tel
        if href.startswith(("#", "mailto:", "tel:")):
            continue
        full_url = urljoin(url, href)
        parsed = urlparse(full_url)
        if parsed.netloc == base_domain or parsed.netloc == "":
            internal_links.append(full_url)
        else:
            external_links.append(full_url)

    # CTAs (buttons + action-like links)
    cta_keywords = [
        "get started", "contact", "buy", "sign up", "signup",
        "subscribe", "download", "request", "book", "schedule",
        "try", "start", "learn more", "get a quote", "free trial"
    ]

    buttons = soup.find_all("button")
    cta_links = [
        a for a in soup.find_all("a", href=True)
        if any(kw in a.get_text(strip=True).lower() for kw in cta_keywords)
    ]
    total_ctas = len(buttons) + len(cta_links)

    # Page text for AI context (capped at 3000 words to avoid token limits)
    page_text_for_ai = " ".join(visible_text.split()[:3000])

    return {
        "url": url,
        "meta": {
            "title": meta_title,
            "description": meta_description,
        },
        "headings": {
            "h1": h1s,
            "h1_count": len(h1s),
            "h2": h2s,
            "h2_count": len(h2s),
            "h3": h3s,
            "h3_count": len(h3s),
        },
        "content": {
            "word_count": word_count,
        },
        "images": {
            "total": total_images,
            "missing_alt": missing_alt,
            "pct_missing_alt": pct_missing_alt,
        },
        "links": {
            "internal_count": len(internal_links),
            "external_count": len(external_links),
        },
        "ctas": {
            "total": total_ctas,
        },
        # This goes to the AI only, not displayed as a metric
        "_page_text": page_text_for_ai,
    }
