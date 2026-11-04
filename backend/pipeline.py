from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from dotenv import load_dotenv
import re, time
load_dotenv()

STAGES = ("search", "reader", "writer", "critic")

# --- malformed tool calls (gpt-oss sometimes calls tools that don't exist) ---
MAX_ATTEMPTS = 3
RETRY_HINT = ("\n\nNote: your previous tool call was rejected because it was malformed. Call the tool "
              "again using exactly its documented arguments (web_search takes one string argument "
              "named `query`; scrape_url takes one string argument named `url`).")


def _is_tool_call_error(e: Exception) -> bool:
    msg = str(e)
    return "tool_use_failed" in msg or "Tool call validation failed" in msg


# --- Groq rate limits (tokens per minute): wait as long as Groq asks, then retry ---
RATE_LIMIT_ATTEMPTS = 5
MAX_WAIT_S = 60


def _is_rate_limit(e: Exception) -> bool:
    msg = str(e)
    return "rate_limit_exceeded" in msg or "Error code: 429" in msg


def _retry_after(e: Exception, default: float = 20.0) -> float:
    """Groq says e.g. 'try again in 15.78s', '1m5.2s' or '850ms'."""
    m = re.search(r"try again in\s*((?:\d+(?:\.\d+)?(?:ms|s|m|h))+)", str(e))
    if not m:
        return default
    scale = {"ms": 0.001, "s": 1, "m": 60, "h": 3600}
    return sum(float(n) * scale[u] for n, u in re.findall(r"(\d+(?:\.\d+)?)(ms|s|m|h)", m.group(1)))


def run_research_pipeline(topic: str, on_event=None) -> dict:
    """Runs the pipeline. If on_event is given it receives
    {"stage": ..., "status": "running|completed|failed", "content": ...}
    at each real stage boundary. Terminal usage is unchanged."""
    state = {}

    def emit(stage, status, content=None):
        if on_event:
            on_event({"stage": stage, "status": status, "content": content})

    def stage(name, label, fn):
        print("\n" + "=" * 50 + f"\n{label}\n" + "=" * 50)
        emit(name, "running")
        hint, tool_tries, rate_tries = "", 0, 0
        while True:
            try:
                out = fn(hint)
                break
            except Exception as e:
                if _is_rate_limit(e) and rate_tries < RATE_LIMIT_ATTEMPTS:
                    wait = _retry_after(e) + 1
                    if wait <= MAX_WAIT_S:  # a daily-quota error asks for hours: fail instead
                        rate_tries += 1
                        print(f"[{name}] rate limited, waiting {wait:.0f}s ({rate_tries}/{RATE_LIMIT_ATTEMPTS})")
                        time.sleep(wait)
                        continue
                tool_tries += 1
                if _is_tool_call_error(e) and tool_tries < MAX_ATTEMPTS:
                    print(f"[{name}] malformed tool call (attempt {tool_tries}/{MAX_ATTEMPTS}), retrying: {e}")
                    hint = RETRY_HINT
                    continue
                emit(name, "failed", str(e))
                raise
        emit(name, "completed")
        print(out)
        return out

    # step 1 - search agent
    def search(hint=""):
        agent = build_search_agent()
        r = agent.invoke({"messages": [{"role": "user", "content":
            f"Find recent, reliable and detailed information about the topic :{topic}" + hint}]})
        return r["messages"][-1].content
    state["search_results"] = stage("search", "step 1 : search agent working", search)

    # step 2 - reader agent
    def read(hint=""):
        agent = build_reader_agent()
        r = agent.invoke({"messages": [{"role": "user", "content":
            f"based on the following research about the topic :{topic},"
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"search results:{state['search_results'][:800]}" + hint}]})
        return r["messages"][-1].content
    state["scraped_content"] = stage("reader", "step 2 : reader agent is scraping top resources", read)

    # step 3 - writer chain
    research_combined = (
        f"Search Results:\n {state['search_results']} \n\n"
        f"Detailed scraped content:\n {state['scraped_content']}"
    )
    state["report"] = stage("writer", "step 3 : writer is drafting the report",
        lambda hint="": writer_chain.invoke({"topic": topic, "research": research_combined}))

    # step 4 - critic chain
    state["feedback"] = stage("critic", "step 4 : critic is reviewing the report",
        lambda hint="": critic_chain.invoke({"report": state["report"]}))

    return state


if __name__ == "__main__":
    topic = input("\n Enter research topic:\n")
    run_research_pipeline(topic)