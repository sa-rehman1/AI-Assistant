import streamlit as st
import pandas as pd
import openai

# Set up OpenAI API
openai.api_key = "your_api_key"

# Function to query ChatGPT with a specific question and dataset context
def query_chatgpt(question, context):
    prompt = f"""
    Given the following dataset:
    {context}

    Answer the following question consisely and write your final calculation:
    {question}
    """

    prompt2="""You are a teacher who excels in statistics 
    after recieving the data you have to do calculations and answer the query 
    asked by the user you are  the best in analyzing data in whole world
    You do not have to show how you are calculating the answers"""

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {'role':"system","content":prompt2},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# Streamlit app

    upload_file = st.file_uploader("Upload CSV file with student data", type="csv")

    if upload_file is not None:
        # Load the data
        df = pd.read_csv(uploaded_file)

        # Display the dataframe
        st.write("### Uploaded Data", df)

        # Ask the teacher to input a question
        question = st.text_area("Ask a question about the dataset:")

        if st.button("Get Answer"):
            # Convert dataframe to a string format
            context = df.to_string(index=False)

            # Query ChatGPT
            answer = query_chatgpt(question, context)

            # Display the answer
            st.write("### Answer from ChatGPT")
            st.write(answer)
