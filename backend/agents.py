from dotenv import load_dotenv
load_dotenv()
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url

#model setup
llm=init_chat_model("groq:openai/gpt-oss-120b",temperature=0)


#agent 1
def build_search_agent():
    return create_agent(
        llm,
        tools=[web_search]
    )

#agent 2
def build_reader_agent():
    return create_agent(
        llm,
        tools=[scrape_url]
    )

#write chain
writer_prompt=ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Formatting rules:
- Write Key Findings as numbered points. Give each point a short bold heading, followed by a full explanatory paragraph.
- Do not use tables anywhere in the report. Use paragraphs and simple lists only.

Be detailed, factual and professional."""),
])

writer_chain= writer_prompt | llm | StrOutputParser()

critic_prompt=ChatPromptTemplate([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])
#critic chain
critic_chain=critic_prompt | llm | StrOutputParser()
