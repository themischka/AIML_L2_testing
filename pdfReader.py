# -------imports------ #
from groq import Groq
from pypdf import PdfReader
import chromadb
import streamlit as st
import datetime


# -------vars------ #
tone = str()
API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=API_KEY)
MODEL = "llama-3.1-8b-instant"
disThresh = float(1.0)
lostThresh = float(1.2)
msgtollm = "give me the answer only based on the chat history"

# -------session_state definitions------ #
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
if "chunk_size" not in st.session_state:
    st.session_state.chunk_size = 300
if "overlap" not in st.session_state:
    st.session_state.overlap = 150

# -------formatting tabs------ #
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["PDF file reader", "Sample PDFs provided", "Mad-Lib Maker", "Ask the database", "Feedback", "About"])

# -------formatting sidebar------ #
st.sidebar.header("RAG Settings")
st.sidebar.slider(
    "Chunk size",
    min_value=100,
    max_value=2000,
    value=300,
    step=50,
    key="chunk_size"
)

st.sidebar.slider(
    "Chunk overlap",
    min_value=0,
    max_value=500,
    value=150,
    step=25,
    key="overlap"
)

chunk_size = st.session_state.chunk_size
overlap = st.session_state.overlap

if overlap >= chunk_size:
    st.sidebar.error(
        "Overlap must be smaller than chunk size."
    )

# -------main pdf reader------ #
with tab1:
    st.title("Pdf file reader")
    st.write("This is a Pdf reader, import a pdf here and ask questions about it.")
    st.write("If you do not have a Pdf to import check the next tab there are two samples to try out.")
    container = st.container(border=True)
    file = st.file_uploader("Upload a .pdf file", "pdf")
    if file and st.button("Process File"):
        x = datetime.datetime.now()
        chunks = []
        st.write("File processing")
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        step = st.session_state.chunk_size - st.session_state.overlap

        for i in range(0, len(text), step):
            chunks.append(text[i:i + st.session_state.chunk_size])
        st.sidebar.write(f"Chunk size: {st.session_state.chunk_size}")
        st.sidebar.write(f"Overlap: {st.session_state.overlap}")
        st.write(len(chunks))
        client = chromadb.Client()
        docName = "documents_" + x.strftime("%Y%m%d_%H%M%S_%f")
        collection = client.create_collection(docName)
        tags = [file.name + str(i) for i in range(len(chunks))]
        collection.add(documents=chunks, ids=tags)
        st.session_state.collection = collection
        st.write("Chunks added to knowledge base")
    question = st.text_input("Ask about the uploaded file.")
    st.session_state.messages.append({"role": "assistant", "content": st.session_state.response})
    if st.button("Search"):
        st.write("Thinking!")
        collection = st.session_state.collection
        result = collection.query(query_texts=question, n_results=6)
        # distances compared to thresh hold to filter out bad results
        for x in range(1):
            if result["distances"][0][x] < disThresh:
                st.session_state.tone = "Respond confidently."
                st.session_state.hallucinating = False
                st.session_state.lost = False
            elif lostThresh > result["distances"][0][x] > disThresh:
                st.session_state.hallucinating = True
                st.session_state.lost = False
                st.session_state.tone = "Respond doubtfully."
            else:
                st.session_state.tone = "Be very doubtful, there is likely not enough information to make a response"
                st.session_state.lost = True
        # change this so that it prints documents of relevant +- 3 ids
        st.session_state.context = result["documents"][0][::-1]
        st.session_state.question = question
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
            container.write("I am probably lost, so my answer may not be accurate.")
        else:
            container.markdown(st.session_state.answer)
            container.write("Don't forget I get confused too!")

with tab2:
    st.title("Read from sample PDFs")
    st.write("Click on either of the samples, wait for them to load, then ask a question.")
    col1, col2, col3 = st.columns(3)
    container = st.container(border=True)
    with col1:
        if st.button("Sample 1"):
            chunks = []
            st.write("File processing")
            sampleFile = "sample1.pdf"
            reader = PdfReader(sampleFile)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            step = st.session_state.chunk_size - st.session_state.overlap
            for i in range(0, len(text), step):
                chunks.append(text[i: i + st.session_state.chunk_size])
            st.write(len(chunks))
            client = chromadb.Client()
            time = datetime.datetime.now()
            docName = "documents_" + time.strftime("%Y%m%d_%H%M%S_%f")
            collection = client.create_collection(docName)
            tags = [sampleFile + str(i) for i in range(len(chunks))]
            collection.add(documents=chunks, ids=tags)
            st.session_state.collection = collection
            st.write("Chunks added to knowledge base.")
        st.write("Sample 1 is about Ponyo (2008).")
    with col2:
        if st.button("Sample 2"):
            chunks = []
            st.write("File processing")
            sampleFile = "sample2.pdf"
            reader = PdfReader(sampleFile)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            step = st.session_state.chunk_size - st.session_state.overlap
            for i in range(0, len(text), step):
                chunks.append(text[i: i + st.session_state.chunk_size])
            st.write(len(chunks))
            client = chromadb.Client()
            time = datetime.datetime.now()
            docName = "documents_" + time.strftime("%Y%m%d_%H%M%S_%f")
            collection = client.create_collection(docName)
            tags = [sampleFile + str(i) for i in range(len(chunks))]
            collection.add(documents=chunks, ids=tags)
            st.session_state.collection = collection
            st.write("Chunks added to knowledge base")
        st.write("Sample 2 is about Spirited Away (2001).")
    with col3:
        if st.button("Sample 3"):
            chunks = []
            st.write("File processing")
            sampleFile = "PDF READER.pdf"
            reader = PdfReader(sampleFile)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            step = st.session_state.chunk_size - st.session_state.overlap
            for i in range(0, len(text), step):
                chunks.append(text[i: i + st.session_state.chunk_size])
            st.write(len(chunks))
            client = chromadb.Client()
            time = datetime.datetime.now()
            docName = "documents_" + time.strftime("%Y%m%d_%H%M%S_%f")
            collection = client.create_collection(docName)
            tags = [sampleFile + str(i) for i in range(len(chunks))]
            collection.add(documents=chunks, ids=tags)
            st.session_state.collection = collection
            st.write("Chunks added to knowledge base")
        st.write("Sample 3 is about what are RAGs and this website.")

    question = st.text_input("Ask a question about what the file is about.", placeholder="Enter here")
    if st.button("search about the sample"):
        st.write("thinking")
        collection = st.session_state.collection
        result = collection.query(query_texts=question, n_results=6)
        st.session_state.context = result["documents"][0][::-1]
        st.session_state.question = question
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

with tab3:
    st.title("Mad-Lib maker")
    st.write("Enter text into the following prompts, then press finish to see your mad-lib.")

    nomIn = st.text_input("Give me a name, for example: Milana")
    if nomIn:
        st.write("you wrote: (", nomIn, ") for your name")
    nameIN = nomIn

    plIn = st.text_input("Give me a city, for example: Vancouver")
    if plIn:
        st.write("you wrote: (", plIn, ") for your place")
    placeIN = plIn

    emIn = st.text_input("Give me an emotion, for example: Nervous")
    if emIn:
        st.write("you wrote: (", emIn, ") for your emotion")
    emotionIN = emIn

    numIn = st.text_input("Give me a number greater than 5, for example: 8")
    if numIn:
        st.write("you wrote: (", numIn, ") for your number")
    numberIN = numIn

    foIn = st.text_input("Give me a food at a restaurant, for example: Steak")
    if foIn:
        st.write("you wrote: (", foIn, ") for your food")
    foodIN = foIn

    if st.button("finish"):
        st.write(
            nameIN, " went to go",
            placeIN, " because",
            nameIN, " was going to see a friend.",
            nameIN, " was feeling very",
            emotionIN, "to see this friend because, this friend had once eaten",
            numberIN, foodIN, "s and left",
            nameIN, "with the bill"
        )
        st.balloons()
with tab4:
    st.write("tab 4 is a work in progress")
    # client = chromadb.PersistentClient(path="./my_db")
    #
    # disThres = float(0.42)
    # talk = True
    #
    # # making a collection (a table of data) holds all the knowledge
    # collection = client.get_or_create_collection("animals")
    # sentences = [
    #     "Good dogs, like Snoopy are the best.",
    #     "Snoopy is a good dog.",
    #     "Dogs are not good",
    #     "The smoke is strong today."
    #     # "Милана хочет есть.",
    #     # "Milana wants to eat.",
    #     # "Милана думала что там есть яблока здесь.",
    #     # "там нет яблоко здешь."
    #     # "니 생일은 언재?",
    #     # "내 생일은 어제였"
    # ]
    #
    # # unique tags
    # tags = ["1", "2", "3", "4"]
    # collection.add(documents=sentences, ids=tags)
    #
    # while talk:
    #     # queries
    #     question = st.text_input("Ask a question, /add to add to database, or say /bye to quit: ", key="talkQues")
    #     if question == "/bye":
    #         talk = False
    #     elif question == "/add":
    #         adding = st.text_input("type something to add to the database: ", key="talkadding")
    #         i = 4
    #         st.write("adding", adding, "to the database")
    #         sentences.append(adding)
    #         st.write(sentences, sep="\n")
    #         # and then do something to make it add another number to collection
    #         nxtHigh = str(max(int(x) for x in tags) + 1)
    #         tags.append(nxtHigh)
    #         collection.add(documents=sentences, ids=tags)
    #         st.write(tags, sep="\n")
    #     else:
    #         result = collection.query(query_texts=question, n_results=2)
    #
    #         # results of distance aren't floats, so they cannot be compared
    #
    #         # prints the sentences that are most similar to the query
    #         print(result["documents"])
    #         # prints the ids, the tag that was assigned to the sentences
    #         print(result["ids"])
    #         # prints the "distance" between the query and the sentences in the database
    #         print(result["distances"])
    #         for x in range(len(result["distances"][0])):
    #             print(result["distances"][0][x])
    #             if result["distances"][0][x] > disThres:
    #                 print("the results may not be accurate, I may be hallucinating")
    #
    #
    #
with tab5:
    # -------feedback area------ #
    st.title("Feedback page")
    st.write("Write your feed back here.")
    feedback = st.text_input("Type feedback here")
    with open("count.txt", "a") as f:
        f.write(f"\n {feedback}")
    with open("count.txt") as f:
        savedFeed = f.read()
    sideCont = st.container(border=True)
    sideCont.markdown(savedFeed.replace("\n", "  \n"))
with tab6:
    st.title("About")
    st.write(
        "This website was built with streamlit and python, during the Circuit Stream AIML L2 course."
        "The main goal of the AIML L2 bootcamp was to learn about machine learning and ai and this website reflects that learning and also some side projects learned in the process."
        "This website is still a work in progress, I plan to add more to it soon, like in the database tab I have the code for it I just need to add it soon."
    )

