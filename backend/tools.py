from langchain.tools import tool
import requests
from bs4 import BeautifulSoup  #web scraping
from tavily import TavilyClient
import os
from rich import print
from dotenv import load_dotenv
import ipaddress, socket
from urllib.parse import urlparse

load_dotenv()

tavily=TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query:str)->str:
    """Search the web for recent and reliable information on a topic. Returns titles, urls, snippet"""
    results=tavily.search(query=query,max_results=3)
    out=[]

    for r in results['results']:
        out.append(f"Title:{r['title']}\n URL:{r['url']}\n Snippet={r['content'][:300]}\n")
    return "\n-------\n".join(out)

def _is_public(url: str) -> bool:
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        return False
    try:
        ips = {ai[4][0] for ai in socket.getaddrinfo(p.hostname, None)}
    except (socket.gaierror, ValueError):
        return False
    return all(ipaddress.ip_address(ip).is_global for ip in ips)

@tool
def scrape_url(url:str)->str:
    """Scrape and return clean text content from a given URL for deeper reading"""
    if not _is_public(url):
        return "Could not scrape url: address not allowed"
    try:
        resp=requests.get(url,timeout=8,headers={"User-Agent":"Mozilla/5.0"})
        soup=BeautifulSoup(resp.text,"html.parser")

        for tag in soup(["script","nav","footer","style"]):
            tag.decompose()
        return soup.get_text(separator=" ",strip=True)[:3000]
    except Exception as e:
        return f"Could not scrape url:{str(e)}"