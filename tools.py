from langchain.tools import tool
import requests
from bs4 import BeautifulSoup  #web scraping
from tavily import TavilyClient
import os
from rich import print
from dotenv import load_dotenv

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

