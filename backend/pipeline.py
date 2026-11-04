from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from dotenv import load_dotenv
import re, time
load_dotenv()

STAGES = ("search", "reader", "writer", "critic")


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
        try:
            out = fn()
        except Exception as e:
            emit(name, "failed", str(e))
            raise
        emit(name, "completed")
        print(out)
        return out

    # step 1 - search agent
    def search():
        agent = build_search_agent()
        r = agent.invoke({"messages": [{"role": "user", "content":
            f"Find recent, reliable and detailed information about the topic :{topic}"}]})
        return r["messages"][-1].content
    state["search_results"] = stage("search", "step 1 : search agent working", search)

    # step 2 - reader agent
    def read():
        agent = build_reader_agent()
        r = agent.invoke({"messages": [{"role": "user", "content":
            f"based on the following research about the topic :{topic},"
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"search results:{state['search_results'][:800]}"}]})
        return r["messages"][-1].content
    state["scraped_content"] = stage("reader", "step 2 : reader agent is scraping top resources", read)

    # step 3 - writer chain
    research_combined = (
        f"Search Results:\n {state['search_results']} \n\n"
        f"Detailed scraped content:\n {state['scraped_content']}"
    )
    state["report"] = stage("writer", "step 3 : writer is drafting the report",
        lambda: writer_chain.invoke({"topic": topic, "research": research_combined}))

    # step 4 - critic chain
    state["feedback"] = stage("critic", "step 4 : critic is reviewing the report",
        lambda: critic_chain.invoke({"report": state["report"]}))

    return state


if __name__ == "__main__":
    topic = input("\n Enter research topic:\n")
    run_research_pipeline(topic)
