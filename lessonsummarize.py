import streamlit as st
import time
import langchain
import openai
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.embeddings.openai import OpenAIEmbeddings


from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter



openai_key = "your_api_key"


def summarize():
    # st.markdown('<h1 style="font-family:Lora;color:darkred;text-align:center;">Summarize Your Lesson</h1>',unsafe_allow_html=True)
    # st.markdown('<i><h3 style="font-family:Arial;color:darkred;text-align:center;font-size:20px;padding-left:50px">Your AI Assistant To Summarize Lessons To Help You Cover Bullet Points!</h3><i>',unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF File Of Your Lesson")

    if uploaded_file:
        with st.spinner("Summarizing lesson into bullet points..."):
            with open(uploaded_file.name, mode='wb') as w:
                w.write(uploaded_file.getvalue())
            loader = PyPDFLoader(uploaded_file.name)
            pages = loader.load()
            
            # Split
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size = 1500,
                chunk_overlap = 150
            )

            splits = text_splitter.split_documents(pages)

            embedding = OpenAIEmbeddings(api_key="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")

            persist_directory = 'docs/chroma/'

            vectordb = Chroma.from_documents(
                documents=splits,
                embedding=embedding,
                persist_directory=persist_directory
            )

            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, api_key = openai_key)
                    
            template = """Use the following pieces of context and summarize the whole lesson for the teacher in bullet point to help teachers understand lesson. If you don't know the answer, just say that you don't know, don't try to make up an answer. Keep the answer as concise as possible.  
            {context}
            Question: {question}
            Helpful Answer:"""

            QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"],template=template)

            # Run chain
            qa_chain = RetrievalQA.from_chain_type(
                llm,
                retriever=vectordb.as_retriever(),
                chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
            )

            result = qa_chain({"query": "Summarize this lesson for me. I am a teacher, I need to better understand this lesson. put it in bullet points"})

            st.success(result['result'])

            vectordb.delete_collection()

