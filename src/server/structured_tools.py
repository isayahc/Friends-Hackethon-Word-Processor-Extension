from langchain.tools import BaseTool, StructuredTool, tool
from langchain_community.retrievers import ArxivRetriever
#from langchain_community.utilities import SerpAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
#from langchain.tools import Tool
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_community.vectorstores import Chroma
import arxiv
import ast
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv
import os
from langchain_community.llms import HuggingFaceEndpoint
from langchain.tools.render import render_text_description

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActJsonSingleInputOutputParser
# Import things that are needed generically
from langchain.tools.render import render_text_description
from langchain.prompts import PromptTemplate
from src.server.react_json_with_memory import template_system
from src.server.utils import format_arxiv_documents, parse_list_to_dicts, format_search_results, format_wiki_summaries
from src.server.source_container import all_sources
from langchain_community.chat_models.anthropic import (
    ChatAnthropic
    )
load_dotenv()



# import chromadb

# hacky and should be replaced with a database
# from innovation_pathfinder_ai.source_container.container import (
#     all_sources
# )
# from innovation_pathfinder_ai.utils.utils import (
#     parse_list_to_dicts, format_wiki_summaries, format_arxiv_documents, format_search_results
# )
# from innovation_pathfinder_ai.database.db_handler import (
#     add_many
# )

# from innovation_pathfinder_ai.vector_store.chroma_vector_store import (
#     add_pdf_to_vector_store
# )
# from innovation_pathfinder_ai.utils.utils import (
#     create_wikipedia_urls_from_text, create_folder_if_not_exists,
# )
# from innovation_pathfinder_ai.utils import create_wikipedia_urls_from_text

# persist_directory = os.getenv('VECTOR_DATABASE_LOCATION')

# @tool
# def memory_search(query:str) -> str:
#     """Search the memory vector store for existing knowledge and relevent pervious researches. \
#         This is your primary source to start your search with checking what you already have learned from the past, before going online."""
#     # Since we have more than one collections we should change the name of this tool
#     client = chromadb.PersistentClient(
#      path=persist_directory,
#     )
    
#     collection_name = os.getenv('CONVERSATION_COLLECTION_NAME')
#     #store using envar
    
#     embedding_function = SentenceTransformerEmbeddings(
#         model_name=os.getenv("EMBEDDING_MODEL"),
#         )
    
#     vector_db = Chroma(
#     client=client, # client for Chroma
#     collection_name=collection_name,
#     embedding_function=embedding_function,
#     )
    
#     retriever = vector_db.as_retriever()
#     docs = retriever.get_relevant_documents(query)
    
#     return docs.__str__()

# @tool
# def knowledgeBase_search(query:str) -> str:
#     """Search the internal knowledge base for research papers and relevent chunks"""
#     # Since we have more than one collections we should change the name of this tool
#     client = chromadb.PersistentClient(
#      path=persist_directory,
#     )
    
#     collection_name="ArxivPapers"
#     #store using envar
    
#     embedding_function = SentenceTransformerEmbeddings(
#         model_name=os.getenv("EMBEDDING_MODEL"),
#         )
    
#     vector_db = Chroma(
#     client=client, # client for Chroma
#     collection_name=collection_name,
#     embedding_function=embedding_function,
#     )
    
#     retriever = vector_db.as_retriever()
#     docs = retriever.get_relevant_documents(query)
    
#     return docs.__str__()

@tool
def arxiv_search(query: str) -> str:
    """Search arxiv database for scientific research papers and studies. This is your primary online information source.
    always check it first when you search for additional information, before using any other online tool."""
    global all_sources
    arxiv_retriever = ArxivRetriever(load_max_docs=3)
    data = arxiv_retriever.invoke(query)
    meta_data = [i.metadata for i in data]
    formatted_sources = format_arxiv_documents(data)
    all_sources += formatted_sources
    parsed_sources = parse_list_to_dicts(formatted_sources)
    # add_many(parsed_sources)
  
    return data.__str__()

@tool
def get_arxiv_paper(paper_id:str) -> None:
    """Download a paper from axriv to download a paper please input 
    the axriv id such as "1605.08386v1" This tool is named get_arxiv_paper
    If you input "http://arxiv.org/abs/2312.02813", This will break the code. Also only do 
    "2312.02813". In addition please download one paper at a time. Pleaase keep the inputs/output
    free of additional information only have the id. 
    """
    # code from https://lukasschwab.me/arxiv.py/arxiv.html
    paper = next(arxiv.Client().results(arxiv.Search(id_list=[paper_id])))
    
    number_without_period = paper_id.replace('.', '')
    
    # Download the PDF to a specified directory with a custom filename.
    paper.download_pdf(dirpath="./downloaded_papers", filename=f"{number_without_period}.pdf")

@tool
def embed_arvix_paper(paper_id:str) -> None:
    """Download a paper from axriv to download a paper please input 
    the axriv id such as "1605.08386v1" This tool is named get_arxiv_paper
    If you input "http://arxiv.org/abs/2312.02813", This will break the code. Also only do 
    "2312.02813". In addition please download one paper at a time. Pleaase keep the inputs/output
    free of additional information only have the id. 
    """
    # code from https://lukasschwab.me/arxiv.py/arxiv.html
    paper = next(arxiv.Client().results(arxiv.Search(id_list=[paper_id])))
    
    number_without_period = paper_id.replace('.', '')
    
    pdf_file_name = f"{number_without_period}.pdf"
    
    pdf_directory = "./downloaded_papers"
    # create_folder_if_not_exists(pdf_directory)
    
    # Download the PDF to a specified directory with a custom filename.
    paper.download_pdf(dirpath=pdf_directory, filename=f"{number_without_period}.pdf")
    
    # client = chromadb.PersistentClient(
    #  path=persist_directory,
    # )
    
    collection_name="ArxivPapers"
    #store using envar
    
    embedding_function = SentenceTransformerEmbeddings(
        model_name=os.getenv("EMBEDDING_MODEL"),
        )
    
    full_path = os.path.join(pdf_directory, pdf_file_name)
    
    # add_pdf_to_vector_store(
    #     collection_name=collection_name,
    #     pdf_file_location=full_path,
    # )
    
@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for additional information to expand on research papers or when no papers can be found."""
    global all_sources

    api_wrapper = WikipediaAPIWrapper()
    wikipedia_search = WikipediaQueryRun(api_wrapper=api_wrapper)
    wikipedia_results = wikipedia_search.run(query)
    formatted_summaries = format_wiki_summaries(wikipedia_results)
    all_sources += formatted_summaries
    parsed_summaries = parse_list_to_dicts(formatted_summaries)
    # add_many(parsed_summaries)
    #all_sources += create_wikipedia_urls_from_text(wikipedia_results)
    return wikipedia_results

@tool
def google_search(query: str) -> str:
    """Search Google for additional results when you can't answer questions using arxiv search or wikipedia search."""
    global all_sources
    
    websearch = GoogleSearchAPIWrapper()
    search_results:dict = websearch.results(query, 3)
    cleaner_sources =format_search_results(search_results)
    parsed_csources = parse_list_to_dicts(cleaner_sources)
    # add_many(parsed_csources)
    all_sources += cleaner_sources    
    
    return cleaner_sources.__str__()

# if __name__ == "__main__":
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')


model = ChatMistralAI(model="mistral-large-latest")


# chat = ChatMistralAI(api_key=MISTRAL_API_KEY)

llm = HuggingFaceEndpoint(repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1", 
                        temperature=0.1, 
                        max_new_tokens=1024,
                        repetition_penalty=1.2,
                        return_full_text=False
    )

# llm = ChatAnthropic(
#     anthropic_api_key=ANTHROPIC_API_KEY,
#     model_name="claude-3-opus-20240229",
#     )

tools = [
    # memory_search,
    # knowledgeBase_search,
    # arxiv_search,
    wikipedia_search,
    # google_search,
#    get_arxiv_paper,
    ]

prompt = PromptTemplate.from_template(
    template=template_system
)
prompt = prompt.partial(
    tools=render_text_description(tools),
    tool_names=", ".join([t.name for t in tools]),
)

chat_model_with_stop = llm.bind(stop=["\nObservation"])
agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
        # "chat_history": lambda x: x["chat_history"],
    }
    | prompt
    | chat_model_with_stop
    | ReActJsonSingleInputOutputParser()
)

# instantiate AgentExecutor
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,
    max_iterations=10,       # cap number of iterations
    #max_execution_time=60,  # timout at 60 sec
    return_intermediate_steps=True,
    handle_parsing_errors=True,
    )

# sample = agent_executor.invoke(
#         {
#             "input": " Humphrey Bogart has won several snooker world championships.",
#             "chat_history": []
#         }
# )

# sample = agent_executor.invoke(
#         {
#             "input": "Magnus Carlsen won the 2018 FIDE World Chess Championship[cit].",
#             "chat_history": []
#         }
# )




# x = 0
# pass