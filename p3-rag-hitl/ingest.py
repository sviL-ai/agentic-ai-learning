# ingest.py
import time
from urllib.parse import urljoin, urlparse

import requests
import time
from openai import RateLimitError
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from config import get_embeddings

BASE = "https://www.ileafsolutions.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (internal RAG learning project)"}

# Headings that mark "the real content is over"
STOP_MARKERS = {
    "Take this case study with you",
    "Have a system that needs to do this?",
    "More work",
}

# ---------- SOURCE 1: the website ----------
def get_case_study_urls():
    """Open /work and collect every link shaped like /work/<slug>."""
    html = requests.get(f"{BASE}/work", headers=HEADERS, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    urls = set()
    for a in soup.find_all("a", href=True):
        u = urlparse(urljoin(BASE, a["href"]))
        parts = [p for p in u.path.split("/") if p]
        if u.netloc.endswith("ileafsolutions.com") and len(parts) == 2 and parts[0] == "work":
            urls.add(f"{BASE}/work/{parts[1]}")   # drops ?topic=... and #anchors
    return sorted(urls)


def load_page(url):
    soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=30).text, "html.parser")
    h1 = soup.find("h1")
    title = (h1 or soup.title).get_text(strip=True)

    # remove things that are never content
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "noscript", "svg", "form", "button", "img"]):
        tag.decompose()

    root = soup.find("main") or soup.body
    lines = [l for l in root.get_text("\n", strip=True).split("\n") if l]

    # start at the title line (drops "All work", category tag)
    start = lines.index(title) if title in lines else 0
    # stop at the first junk heading
    end = next((i for i, l in enumerate(lines) if i > start and l in STOP_MARKERS), len(lines))

    # Button/link labels that sometimes sit inside the article
    NOISE_LINES = {"contact us", "get in touch", "read more", "learn more", "book a call"}

    body = [l for l in lines[start:end] if l.lower() not in NOISE_LINES]

    # trailing leftovers: a real article never ends on a 1-3 word line
    while body and len(body[-1].split()) <= 3:
        body.pop()

    text = "\n".join(body)
    return Document(page_content=text, metadata={"source": url, "title": title})


def load_web():
    urls = get_case_study_urls()
    print(f"found {len(urls)} case study links")   # expect ~43
    docs = []
    for i, url in enumerate(urls, 1):
        docs.append(load_page(url))
        print(f"  [{i}/{len(urls)}] {docs[-1].metadata['title'][:60]}")
        time.sleep(0.5)                       # be polite to the server
    return docs

def make_chunks(docs, size=800, overlap=100):
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
    chunks = splitter.split_documents(docs)
    for c in chunks:
        c.page_content = f"{c.metadata['title']}\n\n{c.page_content}"
    return chunks

def add_in_batches(store, chunks, batch=20, pause=2.0, retries=5):
    for i in range(0, len(chunks), batch):
        part = chunks[i:i + batch]
        for attempt in range(retries):
            try:
                store.add_documents(part)
                break
            except RateLimitError:
                wait = 20 * (attempt + 1)
                print(f"  429 at chunk {i}, waiting {wait}s ({attempt + 1}/{retries})")
                time.sleep(wait)
        else:
            raise RuntimeError(f"gave up at chunk {i}: quota is probably exhausted")
        print(f"  embedded {min(i + batch, len(chunks))}/{len(chunks)}")
        time.sleep(pause)

if __name__ == "__main__":
    docs = load_web()
    chunks = make_chunks(docs)
    print(f"{len(docs)} documents -> {len(chunks)} chunks")
    store = Chroma(collection_name="ileaf", embedding_function=get_embeddings(),
                   persist_directory="chroma_db")
    store.reset_collection()
    add_in_batches(store, chunks)
    print("stored.")

# # ---------- SPLIT, EMBED, STORE ----------
# docs = load_web()
# # for d in docs:
# #     tail = d.page_content[-120:].replace("\n", " ")
# #     flag = "  <-- CHECK" if any(w in d.page_content for w in
# #            ["Download the PDF", "More work", "Talk to a solutions lead"]) else ""
# #     print(f"{d.metadata['title'][:45]:45} | ...{tail}{flag}")

# splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
# chunks = splitter.split_documents(docs)
# print(f"{len(docs)} documents -> {len(chunks)} chunks")

# store = Chroma(
#     collection_name="ileaf",
#     embedding_function=get_embeddings(),
#     persist_directory="chroma_db",
# )
# store.reset_collection()
# store.add_documents(chunks)
# print("stored.")