# streamlit run pdfReader.py
from io import BytesIO
import requests
from groq import Groq
from pypdf import PdfReader
import chromadb
import streamlit as st
import datetime
import os

tone = str()
API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=API_KEY)
MODEL = "llama-3.1-8b-instant"
disThresh = float(1.0)
lostThresh = float(1.2)
msgtollm = "give me the answer only based on the chat history"


with st.bottom:
    container = st.container(border=True)
if "hallucinating" not in st.session_state:
    st.session_state.hallucinating = False
if "lost" not in st.session_state:
    st.session_state.lost = False
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "user", "content": msgtollm}]
if "collection" not in st.session_state:
    st.session_state.collection = str()
if "response" not in st.session_state:
    st.session_state.response = str()
if "answer" not in st.session_state:
    st.session_state.answer = []
tab1, tab2 = st.tabs(["PDF file reader", "Sample PDFs provided"])
col1, col2 = st.columns(2)
with tab1:
    st.title("Pdf file reader")

    file = st.file_uploader("Upload a .pdf file", "pdf")
    if file and st.button("Process File"):
        x = datetime.datetime.now()
        chunks = []
        st.write("File processing")
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        chunk_size = 300
        overlap = 150
        step = chunk_size - overlap
        for i in range(0, len(text), step):
            chunks.append(text[i: i + chunk_size])
        # print(len(chunks), "chunks: ")

        # for x in chunks:
        #     print(x)
        st.write(len(chunks))
        client = chromadb.Client()
        # something here about check if doc is already in
        docName = "documents_" + x.strftime("%Y%m%d_%H%M%S_%f")
        collection = client.create_collection(docName)
        tags = [file.name + str(i) for i in range(len(chunks))]
        collection.add(documents=chunks, ids=tags)
        st.session_state.collection = collection
        st.write("Chunks added to knowledge base")
    question = st.text_input("ask about the doc")
    # if question := st.chat_input("Ask about the document"):
    #     st.session_state.messages.append({"role": "user", "content": question})
    #     with st.chat_message("user"):
    #         st.markdown(question)
    #
    #     with st.chat_message("assistant"):
    #         message_placeholder = st.empty()
    #         full_response = ""
    #         st.session_state.response = client.chat.completions.create(model=MODEL, messages=st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": st.session_state.response})
    if st.button("Search"):
        st.write("Thinking!")
        collection = st.session_state.collection
        result = collection.query(query_texts=question, n_results=6)
        # distances compared to thresh hold to filter out bad results
        for x in range(1):
            if result["distances"][0][x] < disThresh:
                # print(result["distances"])
                # print(result["ids"])
                st.session_state.tone = "Respond confidently."
                st.session_state.hallucinating = False
                st.session_state.lost = False
                # print(st.session_state.tone)
            elif lostThresh > result["distances"][0][x] > disThresh:
                # print(result["distances"])
                # print(result["ids"])
                st.session_state.hallucinating = True
                st.session_state.lost = False
                st.session_state.tone = "Respond doubtfully."
                # print(st.session_state.tone)
            else:
                # print(result["distances"])
                # print(result["ids"])
                st.session_state.tone = "Be very doubtful, there is likely not enough information to make a response"
                # print(st.session_state.tone)
                st.session_state.lost = True
        # end of test area?
        # change this so that it prints documents of relevant +- 3 ids
        st.session_state.context = result["documents"][0][::-1]
        st.session_state.question = question
        # for ans in st.session_state.context:
        #     st.write(ans)
        context = "\n".join(st.session_state.context)
        question = st.session_state.question

        messages = [
            {"role": "system", "content": f"Answer if the user's question using only the provided document context. If the context contains enough information to answer, give the answer. {tone}"},
            {"role": "user", "content": f"DOCUMENT CONTEXT: \n{context}\n\nQUESTION:\n{question}"}
        ]
        response = client.chat.completions.create(model=MODEL, messages=messages)
        # st.write("LLM answer: ", response.choices[0].message.content)
        st.session_state.answer = response.choices[0].message.content
        if st.session_state.hallucinating is True:
            container.markdown(st.session_state.answer)
            container.write("With that being said, I might be confused with something else, make sure to double check!")
        elif st.session_state.lost is True:
            container.markdown(st.session_state.answer)
            container.write("I am definitely lost, try your question again or check the contents of you pdf to see if it is relevant.")
        else:
            container.markdown(st.session_state.answer)
            container.write("Don't forget I get confused too!")

    # if st.button("LLM answer"):
    #     context = "\n".join(st.session_state.context)
    #     question = st.session_state.question
    #
    #     messages = [
    #         {"role": "system", "content": f"Answer if the user's question using only the provided document context. If the context contains enough information to answer, give the answer. {tone}"},
    #         {"role": "user", "content": f"DOCUMENT CONTEXT: \n{context}\n\nQUESTION:\n{question}"}
    #     ]
    #     response = client.chat.completions.create(model=MODEL, messages=messages)
    #     st.write("LLM answer: ", response.choices[0].message.content)
    #     if st.session_state.hallucinating is True:
    #         st.write("With that being said, I might be confused with something else, make sure to double check!")
    #     elif st.session_state.lost is True:
    #         st.write("I am definitely lost, try your question again or check the contents of you pdf to see if it is relevant.")
    #     else:
    #         st.write("Don't forget I get confused too!")
with tab2:
    st.write("still in the testing")
    st.title("Read from sample PDFs")
    with col1:
        st.write("Sample 1 is about Ponyo (2008)")
        if st.button("Sample 1"):
            chunks = []
            st.write("File processing")
            sampleFile = "sample1.pdf"
            reader = PdfReader(sampleFile)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            chunk_size = 300
            overlap = 150
            step = chunk_size - overlap
            for i in range(0, len(text), step):
                chunks.append(text[i: i + chunk_size])
            st.write(len(chunks))
            client = chromadb.Client()
            time = datetime.datetime.now()
            docName = "documents_" + time.strftime("%Y%m%d_%H%M%S_%f")
            collection = client.create_collection(docName)
            tags = [sampleFile + str(i) for i in range(len(chunks))]
            collection.add(documents=chunks, ids=tags)
            st.session_state.collection = collection
            st.write("Chunks added to knowledge base")
    with col2:
        st.write("Sample 2 is about Spirited Away (2001)")
        if st.button("Sample 2"):
            chunks = []
            st.write("File processing")
            sampleFile = "sample2.pdf"
            reader = PdfReader(sampleFile)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            chunk_size = 300
            overlap = 150
            step = chunk_size - overlap
            for i in range(0, len(text), step):
                chunks.append(text[i: i + chunk_size])
            st.write(len(chunks))
            client = chromadb.Client()
            time = datetime.datetime.now()
            docName = "documents_" + time.strftime("%Y%m%d_%H%M%S_%f")
            collection = client.create_collection(docName)
            tags = [sampleFile + str(i) for i in range(len(chunks))]
            collection.add(documents=chunks, ids=tags)
            st.session_state.collection = collection
            st.write("Chunks added to knowledge base")

    question = st.text_input("Ask a question about what the file is about.", placeholder="Enter here")
    if st.button("search about the sample"):
        st.write("thinking")
        collection = st.session_state.collection
        result = collection.query(query_texts=question, n_results=6)
        st.session_state.context = result["documents"][0][::-1]
        st.session_state.question = question
        # for ans in st.session_state.context:
        #     st.write(ans)
        context = "\n".join(st.session_state.context)
        question = st.session_state.question

        messages = [
            {"role": "system",
             "content": f"Answer if the user's question using only the provided document context. If the context contains enough information to answer, give the answer. {tone}"},
            {"role": "user", "content": f"DOCUMENT CONTEXT: \n{context}\n\nQUESTION:\n{question}"}
        ]
        response = client.chat.completions.create(model=MODEL, messages=messages)
        st.session_state.answer = response.choices[0].message.content
        container.markdown(st.session_state.answer)
    # if st.button("LLM sample pdf answer"):
    #     context = "\n".join(st.session_state.context)
    #     question = st.session_state.question
    #
    #     messages = [
    #         {"role": "system",
    #          "content": f"Answer if the user's question using only the provided document context. If the context contains enough information to answer, give the answer. {tone}"},
    #         {"role": "user", "content": f"DOCUMENT CONTEXT: \n{context}\n\nQUESTION:\n{question}"}
    #     ]
    #     response = client.chat.completions.create(model=MODEL, messages=messages)
    #     st.write("LLM sample answer: ", response.choices[0].message.content)
