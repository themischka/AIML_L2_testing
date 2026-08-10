import streamlit as st

score = 0
fruitDone = False
starsDone = False
col1, col2, col3 = st.columns(3)

with col1:
    st.title("This or That")
    st.write("apples or oranges")
    fruit = st.selectbox("Fruit", [" ", "apples", "oranges"])
    if fruit == "apples":
        score += 1

    if st.button("fruit done"):
        fruitDone = True

with col2:
    st.title("Stars")
    st.write("rate out of 5")
    sentMap = ["one", "two", "three", "four", "five"]
    select = st.feedback("stars")
    if select is not None:
        st.write("You selected", sentMap[select], "star(s)")

    if st.button("star done"):
        starsDone = True

with col3:
    st.title("Quiz time")
    if fruitDone is True and starsDone is True:
        st.write(f"Your score is {score}")
        if score > 5:
            st.write("You pass")
        else:
            st.write("You fail")
    elif fruitDone is False and starsDone is True:
        st.write("You have not filled out the fruit section")

    elif fruitDone is True and starsDone is False:
        st.write("You have not filled out the star section")

    else:
        st.write("None have been filled out")

