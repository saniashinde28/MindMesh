from agents import build_search_agent,build_reader_agent,writer_chain,critic_chain
from dotenv import load_dotenv
load_dotenv()

def run_research_pipeline(topic:str)->dict:
    state={}

    #search agent
    print("\n"+"="*50)
    print("step 1 : search agent working")
    print("\n"+"="*50)

    search_agent=build_search_agent()
    search_result=search_agent.invoke({
        "messages":[{"role":"user","content":f"Find recent, reliable and detailed information about the topic :{topic}"}]
    })

    state["search_results"]=search_result['messages'][-1].content

    print("\n"+"="*50)
    print("Search Results:",state["search_results"])

    #step 2 - reader agent
    print("\n"+"="*50)
    print("step 1 : search agent is scraping top resources")
    print("\n"+"="*50)
    
    reader_agent=build_reader_agent()
    reader_result=reader_agent.invoke({
        "messages":[{"role":"user",
                     "content":f"based on the following research about the topic :{topic},"
                     f"pick the most relevant URL and scrape it for deeper content.\n\n"
                     f"search results:{state['search_results'][:800]}"}]
    })
    
    state["scraped_content"]=reader_result['messages'][-1].content
    
    print("\n"+"="*50)
    print("Scraped content:",state["scraped_content"])

    #step 3 - writer chain
    print("\n"+"="*50)
    print("step 3:writer is drafting the report :\n")
    print("\n"+"="*50)

    research_combined=(
        f"Search Results:\n {state['search_results']} \n\n"
        f"Detailed scraped content:\n {state['scraped_content']}"
    )

    state["report"]=writer_chain.invoke({
        "topic":topic,
        "research":research_combined
    })

    print("\n Final report\n",state["report"])

    #critic chain
    print("\n"+"="*50)
    print("step 4:Critic is reviewing the report :\n")
    print("\n"+"="*50)

    state["feedback"]=critic_chain.invoke({
        "report":state["report"]
    })

    print("\nCritic report\n",state["feedback"])

    return state


if __name__=="__main__":
    topic=input("\n Enter research topic:\n")
    run_research_pipeline(topic)