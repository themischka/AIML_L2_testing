#from day 4
import chromadb
# mga api key kuno ayaw e butang ditso sa python adto e butang as secret folder sa github
# creates/opens a database
client = chromadb.PersistentClient(path="./my_db")

disThres = float(0.64)
talk = True

# making a collection (a table of data) holds all the knowledge
# funcs: add(), query()
collection = client.get_or_create_collection("animals")
sentences = [
    "Good dogs, like Snoopy are the best.",
    "Snoopy is a good dog.",
    "Dogs are not good",
    "The smoke is strong today."
    # "Милана хочет есть.",
    # "Milana wants to eat.",
    # "Милана думала что там есть яблока здесь.",
    # "там нет яблоко здешь."
    # "니 생일은 언재?",
    # "내 생일은 어제였"
]

# unique tags
tags = ["1", "2", "3", "4"]
collection.add(documents=sentences, ids=tags)

while talk:
    # queries
    question = input("Ask a question, /add to add to database, or say /bye to quit: ")
    if question == "/bye":
        talk = False
    elif question == "/add":
        adding = input("type something to add to the database: ")
        i = 4
        print("adding", adding, "to the database")
        sentences.append(adding)
        print(sentences, sep="\n")
        # and then do something to make it add another number to collection
        nxtHigh = str(max(int(x) for x in tags) + 1)
        tags.append(nxtHigh)
        collection.add(documents=sentences, ids=tags)
        print(tags, sep="\n")
    else:
        result = collection.query(query_texts=question, n_results=2)

        # results of distance aren't floats, so they cannot be compared

        # prints the sentences that are most similar to the query
        print(result["documents"])
        # prints the ids, the tag that was assigned to the sentences
        print(result["ids"])
        # prints the "distance" between the query and the sentences in the database
        print(result["distances"])
        # if result["distances"] > disThres:
        #     print("the results may not be accurate, I may be hallucinating")

