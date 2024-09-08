from llama_index.core import SimpleDirectoryReader
from llama_parse import LlamaParse
from llama_index.readers.github import GithubClient, GithubRepositoryReader
from utils import (setup_index_and_chat_engine, get_embedding_model, set_chat_memory,
                   set_ollama_llm, set_huggingface_llm, set_nvidia_model, set_openai_model, set_anth_model)
import torch, os, glob, gc, dotenv
dotenv.load_dotenv()

DIRECTORY_PATH = "data"
GRAPH_DB_PATH = "neo4DB"
EMBED_MODEL = get_embedding_model()

# TODO Add free parsing options for advanced docs, Llama Parse only lets you parse 1000 free docs a day
# TODO Figure out why multiprocessing of docs causes program to reload in a loop
# Local Document Loading Function
def load_docs():
    parser = LlamaParse(api_key=os.getenv("LLAMA_CLOUD_API_KEY"))
    all_files = glob.glob(os.path.join(DIRECTORY_PATH, "**", "*"), recursive=True)
    all_files = [f for f in all_files if os.path.isfile(f)]
    documents = []
    supported_extensions = [".pdf", ".docx", ".xlsx", ".csv", ".xml", ".html"]
    for file in all_files:
        file_extension = os.path.splitext(file)[1].lower()
        if "LLAMA_CLOUD_API_KEY" in os.environ and file_extension in supported_extensions:
            file_extractor = {file_extension: parser}
            documents.extend(
                SimpleDirectoryReader(input_files=[file], file_extractor=file_extractor).load_data())
        else:
            documents.extend(SimpleDirectoryReader(input_files=[file]).load_data())
    return documents

# GitHub Repo Reader setup function
def load_github_repo(owner, repo, branch):
    if "GITHUB_PAT" in os.environ:
        github_client = GithubClient(github_token=os.getenv("GITHUB_PAT"), verbose=True)
        owner=owner
        repo=repo
        branch=branch
        documents= GithubRepositoryReader(
            github_client=github_client,
            owner=owner,
            repo=repo,
            use_parser=False,
            verbose=False,
        ).load_data(branch=branch)
        return documents
    else:
        print("Couldn't find your GitHub Personal Access Token in the environment file. Make sure you enter your "
              "GitHub Personal Access Token in the .env file.")


def create_chat_engine(model_provider, model, temperature, max_tokens, custom_prompt, top_p,
                       context_window, quantization, owner, repo, branch):
    # Clearing GPU Memory
    torch.cuda.empty_cache()
    gc.collect()
    # Loading Documents and GitHub Repos
    documents = load_docs()
    if owner and repo and branch:
        documents.extend(load_github_repo(owner, repo, branch))
    # Loading Embedding Model
    embed_model = EMBED_MODEL
    # Loading LLM
    llm_setters = {
        "Ollama": lambda: set_ollama_llm(model, temperature, max_tokens),
        "HuggingFace": lambda: set_huggingface_llm(model, temperature, max_tokens, top_p, context_window, quantization),
        "NVIDIA NIM": lambda: set_nvidia_model(model, temperature, max_tokens, top_p),
        "OpenAI": lambda: set_openai_model(model, temperature, max_tokens, top_p),
        "Anthropic": lambda: set_anth_model(model, temperature, max_tokens)
    }
    try:
        llm = llm_setters[model_provider]()
    except KeyError:
        raise ValueError(f"Unsupported model provider: {model_provider}")
    # Setting Memory
    memory = set_chat_memory(model)
    return setup_index_and_chat_engine(docs=documents, llm=llm, embed_model=embed_model,
                                       memory=memory, custom_prompt=custom_prompt)
