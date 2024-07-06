import json
from dotenv import load_dotenv, find_dotenv
import os

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_core.runnables import RunnablePassthrough

from prompts import RAG_PROMPT

load_dotenv(find_dotenv())
LLM_API_KEY = os.environ.get("LLM_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME")


def format_docs(docs):
    return "\n".join(doc.page_content.replace("\n\n", "\n") for doc in docs)

def get_user_data(logs_path):
    with open(logs_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    users = data["meta"]["users"]
    userindex = data["meta"]["userindex"]
    messages = data["data"]["1052316946932170803"]
    messages = [messages[m_id] for m_id in messages]
    return users, userindex, messages

def msg2text(users, userindex, msg):
    msg_text = msg.get("m")
    if msg_text is None:
        return None
    msg_author = users[userindex[msg["u"]]]["name"]
    return f"'{msg_author}' --- '{msg_text}'"

def main():
    # logs_path = "data/discord_messages_prog.json"
    # users, userindex, messages = get_user_data(logs_path)
    # msgs_strings = []
    # for msg in messages:
    #     msg_text = msg2text(users, userindex, msg)
    #     if msg_text is not None:
    #         msgs_strings.append(msg_text)
    # messages_string = "\n\n".join(msgs_strings)
    # with open("data/messages.txt", "w", encoding="utf-8") as f:
    #     f.write(messages_string)

    # text_splitter = CharacterTextSplitter(
    #     separator="\n\n",
    #     chunk_size=1200,
    #     chunk_overlap=200,
    #     length_function=len,
    #     is_separator_regex=False
    # )
    # with open("data/messages.txt", "r", encoding="utf-8") as f:
    #     plain_text = f.read()
    # texts = text_splitter.create_documents([plain_text])

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=LLM_API_KEY
    )
    # docsearch = PineconeVectorStore.from_documents(
    #     texts,
    #     embedding=embeddings, 
    #     index_name=PINECONE_INDEX_NAME
    # )
    retriever = PineconeVectorStore(
        embedding=embeddings, 
        index_name=PINECONE_INDEX_NAME
    ).as_retriever(search_kwargs={"k": 7})
    query = ""
    # docs = docsearch.similarity_search(query, k=5)
    # for doc in docs:
    #     print("-"*40)
    #     print(doc.page_content)

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=LLM_API_KEY,
        temperature=0
    )

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | llm
    )
    answer = rag_chain.invoke(query)
    print(f"""
    ******Prompt******\n{query}\n
    *****Final Answer*****\n{answer.content}\n
    *****Tokens used*****\n{answer.response_metadata['token_usage']['total_tokens']}
    """.strip())


if __name__ == "__main__":
    main()