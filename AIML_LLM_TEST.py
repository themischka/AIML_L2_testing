import streamlit as st
import time
import ollama
API_KEY = st.secrets["GROQ_API_KEY"]
MODEL = "llama-3.1-8b-instant"

st.write("Practicing connecting code and ai for AIML_L2 2026")

st.caption("try it in different languages and try and see if it knows the password")

# Initialize chat history
if "messages" not in st.session_state:
    # shares var between reruns
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

# Display chat messages from history on app rerun
# st.session_state.messages is var of past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
# st.chat_input(what the text box display says)
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        # empty container to hold one thing
        message_placeholder = st.empty()
        full_response = ""
        # st.session_state.messages past messages, messages is a list from a list
        temp = ollama.chat(model=MODEL, messages=st.session_state.messages)
        # pick what you want from the list from a list
        assistant_response = temp["message"]["content"]
        # Simulate stream of response with milliseconds delay
        # drama ra diay ni pina huna2
        for chunk in assistant_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
