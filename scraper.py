from bs4 import BeautifulSoup
import requests


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Extract webpage text while removing known navigation
    and irrelevant interface elements.
    Truncate to 2,000 characters.
    """

    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    title = (
        soup.title.get_text(strip=True)
        if soup.title
        else "No title found"
    )

    # Remove known navigation containers
    selectors_to_remove = [
        "header",
        "nav",
        "footer",
        "#main-header",
        "#header-909787930b",
        ".meganavigation",
        ".global-nav",
        ".geo-locator",
        ".common-header",
        ".navbar",
        "script",
        "style",
        "img",
        "input",
        "button",
        "svg",
        "form",
        "noscript"
    ]

    for selector in selectors_to_remove:
        for element in soup.select(selector):
            element.decompose()

    # Extract the remaining body content
    if soup.body:
        text = soup.body.get_text(
            separator="\n",
            strip=True
        )
    else:
        text = ""

    # Remove empty and consecutive duplicate lines
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    cleaned_lines = []
    previous_line = None

    for line in lines:
        if line != previous_line:
            cleaned_lines.append(line)

        previous_line = line

    text = "\n".join(cleaned_lines)

    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
