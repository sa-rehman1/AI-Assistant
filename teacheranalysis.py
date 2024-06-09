import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import openai
from docx import Document
from docx.shared import Pt
from io import BytesIO
import docx
from animations import display_cards

from customquery import query_chatgpt

# Set up OpenAI API
openai.api_key = "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"

# Cache data loading function to prevent refreshing
@st.cache_data
def load_data(file):
    return pd.read_csv(file)

# Function to get improvement suggestions from ChatGPT 3.5
@st.cache_data
def get_suggestions(student_name, marks_data, attendance_data):
    subject_strengths = [f"{subject}: {marks} marks" for subject, marks in marks_data.items() if marks >= 60]
    subject_weaknesses = [f"{subject}: {marks} marks" for subject, marks in marks_data.items() if marks < 60]
    
    prompt = f"""
    Student Name: {student_name}
    Subject Marks: {marks_data}
    Attendance: {attendance_data}%

    As a teacher, provide personalized suggestions for this student to improve their performance (max 100 words and in bullet points):
    - Identify strengths and weaknesses based on subject marks
    - Appreciate for subjects the student performed well
    - As a teacher recommend subject-specific study strategies where the student is weak 
    - Address attendance issues if present
    - The suggestions should not be general it should be based on individual performances
    - Suggest ways to maintain or boost motivation

    Take this as an example:

    Murtuza shines in English and Maths! His attentiveness in these classes is clearly paying off, 
    so keep up the excellent work in those subjects. 
    However, Science seems to be a bit of a challenge. 
    By participating in practical sessions and relating the concepts to real-life examples,
    Murtuza can definitely improve his understanding and score well next year.  
    Overall, keep up the good effort, Murtuza, and strive for success in all your subjects!

    By using this example rules I provided generate the content and keep it in form of bullet points and not more than 4
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Function to get class-wide improvement suggestions from ChatGPT 3.5
@st.cache_data
def get_class_suggestions(subject_avgs):
    prompt = f"""
    Class Subject Averages: {subject_avgs}

    As a teacher, provide brief suggestions to improve overall class performance (max 50 words and in bullet points not more than 3):
    - Identify subjects where students are struggling
    - Recommend teaching strategies to improve these subjects
    - Suggest activities or resources to help students understand difficult concepts
    - Provide general tips to maintain or boost class motivation
    """
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Function to calculate overall performance
def calculate_performance(marks):
    return sum(marks) / len(marks)

# Function to plot bar chart for performance
def plot_performance(subjects, marks, title):
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=subjects, y=marks, palette="coolwarm", ax=ax)
    ax.set_title(title, fontsize=16)
    ax.set_ylim(0, 100)
    for p in ax.patches:
        ax.annotate(f'{p.get_height():.2f}', (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=12)
    ax.set_xlabel('Subjects', fontsize=14)
    ax.set_ylabel('Marks', fontsize=14)
    sns.despine(fig)
    return fig

# Function to analyze subject performance
def analyze_subject_performance(df, subjects):
    weak_subjects = []
    strong_subjects = []
    avg_marks = df[subjects].mean()
    
    for subject in subjects:
        if avg_marks[subject] < 60:
            weak_subjects.append(subject)
        else:
            strong_subjects.append(subject)
    
    return weak_subjects, strong_subjects, avg_marks

# Function to get subject-specific improvement suggestions from ChatGPT 3.5
@st.cache_data
def get_subject_suggestions(subject):
    prompt = f"""
    The class is struggling in {subject}. Provide brief strategies to help students improve in this subject (50 words max):
    - Additional classes or tutoring
    - Recommended study resources or activities
    - Tips to improve understanding and retention of material
    - Methods to boost motivation and engagement in the subject

    Let's take an example for geography, change this as per the subject:
    Actively participate in class discussions. Share your thoughts and questions!
    Explore online resources like YouTube educational channels. They can offer additional explanations and diverse perspectives.
    Utilize AI tools for extra practice. These tools can provide personalized exercises to solidify your understanding.
    Form study groups with classmates who share similar interests. Discuss notes, solve problems together, and test each other's knowledge.
    Engage in hands-on activities like map quizzes or geography games. Learning can be fun and interactive!
    Seek additional help from teachers or tutors if you face specific challenges. They're here to support you!
    Maintain consistent attendance and focus during class. This will maximize your learning potential.  

    Make sure to keep this in bullet points not exceeding 3 and give the best response based on the example that I provided and the rules
    """
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Function to get attendance insights
def attendance_insights(df):
    avg_attendance = df['Attendance'].mean()
    min_attendance = df['Attendance'].min()
    max_attendance = df['Attendance'].max()
    
    avg_marks = df[[col for col in df.columns if col not in ['Roll No', 'Name', 'Attendance']]].mean(axis=1)
    correlation = df['Attendance'].corr(avg_marks)
    
    if correlation > 0.5:
        attendance_impact = "Low attendance is significantly impacting performance. Ensure regular attendance."
    elif correlation > 0:
        attendance_impact = "Attendance is moderately impacting performance. Try to attend more regularly."
    else:
        attendance_impact = "Attendance is not a major issue for performance. Focus on study habits and concentration."
    
    lowest_attendance_student = df[df['Attendance'] == min_attendance]['Name'].values[0]
    highest_attendance_student = df[df['Attendance'] == max_attendance]['Name'].values[0]
    
    insights = f"""
    - Average Attendance: {avg_attendance:.2f}%
    - Lowest Attendance: {min_attendance}% (Student: {lowest_attendance_student})
    - Highest Attendance: {max_attendance}% (Student: {highest_attendance_student})
    - Insights: {attendance_impact}
    """
    return insights

# Function to save insights to a docx file
def save_insights_to_docx(title, insights, charts):
    doc = Document()
    doc.add_heading(title, level=1)
    for insight in insights.split('\n'):
        if insight.strip():
            p = doc.add_paragraph(insight.strip(), style='BodyText')
            for run in p.runs:
                run.font.size = Pt(12)
    for chart in charts:
        image_stream = BytesIO()
        chart.savefig(image_stream, format='png')
        image_stream.seek(0)
        doc.add_picture(image_stream, width=docx.shared.Inches(6))
    return doc

# Streamlit app
def analysis():
    uploaded_file = st.file_uploader("Upload CSV file with student data", type="csv")
    analysis_type = st.sidebar.radio("Choose Analysis Type:", ["Class Wide Performance Analysis","Student Wise Performance Analysis",  "Attendance Analysis","Ask Questions To The Data"],horizontal=False)
    
    if uploaded_file is not None:
        # Read the CSV file
        df = load_data(uploaded_file)

        # Display the data
        # st.header("Student Data")
        # st.write(df)
        
        # Ensure the required columns are present
        required_columns = ['Roll No', 'Name', 'Attendance']
        if not all(col in df.columns for col in required_columns):
            st.error("CSV file must contain 'Roll No', 'Name', and 'Attendance' columns.")
        else:
            # Extract subject columns dynamically
            subjects = [col for col in df.columns if col not in required_columns]

            if analysis_type == "Student Wise Performance Analysis":
                st.markdown("<h1 style=font-size:30px;font-family:Garamond,serif;>Student-wise Analysis</h1>",unsafe_allow_html=True)
                
                # Select a student to analyze
                student_names = df['Name'].unique()
                selected_student = st.selectbox("Select a student to analyze:", student_names)
                
                # Filter data for selected student
                student_data = df[df['Name'] == selected_student].iloc[0]
                
                # Extract marks and attendance
                marks = {subject: student_data[subject] for subject in subjects}
                attendance = student_data['Attendance']
                
                # Calculate overall performance
                overall_score = calculate_performance(list(marks.values()))
                
                # Display overall performance
                st.markdown(f"<h1 style=font-size:30px;font-family:Garamond,serif;>{selected_student}'s Performance</h1>",unsafe_allow_html=True)
                st.write(f"Average Score: {overall_score:.2f}/100")
                st.write(f"Attendance: {attendance}%")
                
                # Bar chart for subject-wise performance
                fig = plot_performance(subjects, list(marks.values()), f"{selected_student}'s Subject-wise Marks")
                st.pyplot(fig)
                
                # Performance categories
                categories = {
                    'Excellent': 90,
                    'Good': 80,
                    'Needs Improvement': 60,
                    'Concerning': 40,
                    'Failed' : 0
                }
                
                # Display subject-wise status
                st.markdown("<h1 style=font-size:30px;font-family:Garamond,serif;>Subject-wise Status</h1>",unsafe_allow_html=True)
                for subject, mark in marks.items():
                    for cat, threshold in categories.items():
                        if mark >= threshold:
                            st.write(f"{subject}: {cat} ({mark}/100)")
                            break
                
                # Attendance status
                if attendance < 50:
                    st.error("🚨 CRITICAL WARNING: Attendance is dangerously low. Immediate action is required to avoid severe academic consequences.")
                elif attendance < 75:
                    st.warning("⚠️ Attendance is below 75%. This can significantly impact performance.")
                
                # Get personalized suggestions from ChatGPT 3.5
                st.markdown("<h1 style=font-size:30px;font-family:Garamond,serif;>Personalized Suggestions</h1>",unsafe_allow_html=True)
                suggestions = get_suggestions(selected_student, marks, attendance)
                st.write(suggestions)

                # Option to download the insights as a document
                charts = [fig]
                doc = save_insights_to_docx(f"{selected_student}'s Performance Insights", suggestions, charts)
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                st.download_button(label="Download Student Insights", data=buffer, file_name=f"{selected_student}_insights.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
            elif analysis_type == "Class Wide Performance Analysis":
                st.markdown("<h1 style=font-size:30px;font-family:Garamond,serif;>Class-wide Analysis</h1>",unsafe_allow_html=True)
                
                # Calculate overall class average
                class_avg = df[subjects].mean().mean()
                
                # Analyze subject performance
                weak_subjects, strong_subjects, avg_marks = analyze_subject_performance(df, subjects)
                
                st.markdown("<h1 style=font-size:30px;font-family:Garamond,serif;>Subjects Analysis</h1>",unsafe_allow_html=True)
                st.write("Subjects where students are performing well:")
                for subject in strong_subjects:
                    st.write(f"- {subject}: {avg_marks[subject]:.2f}/100")
                
                st.write("Subjects where students are struggling:")
                for subject in weak_subjects:
                    st.write(f"- {subject}: {avg_marks[subject]:.2f}/100")
                
                # Use display_cards for class-wide performance
                avg_marks = df[subjects].mean()
                highest_marks = df[subjects].max()
                lowest_marks = df[subjects].min()
    
                display_cards("Class Subject Performance", avg_marks.mean(), highest_marks.max(), lowest_marks.min())
                
                selected_subject = st.selectbox("Select a weak subject to get improvement suggestions:", weak_subjects)
                if selected_subject:
                    st.write(f"**Suggestions to Improve Performance in {selected_subject}:**")
                    subject_suggestions = get_subject_suggestions(selected_subject)
                    st.write(subject_suggestions)
                
                # Get class-wide improvement suggestions from ChatGPT 3.5
                st.markdown("<h1 style=font-size:30px;font-family:Garamond,serif;>Overall Class Improvement Plan</h1>",unsafe_allow_html=True)
                class_suggestions = get_class_suggestions(avg_marks.to_dict())
                st.write(class_suggestions)
                
                # Option to download the insights as a document
                charts = []
                class_doc = Document()
                class_doc.add_heading("Class-wide Performance Insights", level=1)
                class_doc.add_heading("Subjects Analysis", level=2)
                class_doc.add_heading("Subjects where students are performing well:", level=3)
                for subject in strong_subjects:
                    p = class_doc.add_paragraph(f"- {subject}: {avg_marks[subject]:.2f}/100", style='BodyText')
                    for run in p.runs:
                        run.font.size = Pt(12)
                class_doc.add_heading("Subjects where students are struggling:", level=3)
                for subject in weak_subjects:
                    p = class_doc.add_paragraph(f"- {subject}: {avg_marks[subject]:.2f}/100", style='BodyText')
                    for run in p.runs:
                        run.font.size = Pt(12)
                class_doc.add_heading("Overall Class Improvement Plan", level=2)
                p = class_doc.add_paragraph(class_suggestions, style='BodyText')
                for run in p.runs:
                    run.font.size = Pt(12)

                buffer = BytesIO()
                class_doc.save(buffer)
                buffer.seek(0)
                st.download_button(label="Download Class Insights", data=buffer, file_name="class_insights.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                
                # Select a specific subject to analyze
                st.markdown("<h1 style=font-size:30px;font-family:Garamond,serif;>Subject-wise Performance Analysis</h1>",unsafe_allow_html=True)
                selected_subject = st.selectbox("Select a subject to analyze:", subjects)
                
                if selected_subject:
                    # Average score for the selected subject
                    subject_avg = df[selected_subject].mean()
                    st.write(f"Class Average for {selected_subject}: {subject_avg:.2f}/100")
                    
                    # Distribution of marks for the selected subject
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.histplot(df[selected_subject], bins=10, kde=True, ax=ax, color="purple")
                    ax.set_title(f"Distribution of Marks in {selected_subject}", fontsize=16)
                    ax.set_xlabel('Marks', fontsize=14)
                    ax.set_ylabel('Frequency', fontsize=14)
                    sns.despine(fig)
                    st.pyplot(fig)
                    charts.append(fig)
                    
                    # Identify struggling students in the selected subject
                    struggling_students = df[df[selected_subject] < 61]
                    st.write(f"Number of students needing improvement in {selected_subject}: {len(struggling_students)}")
                    if not struggling_students.empty:
                        st.write(struggling_students[['Roll No', 'Name', selected_subject, 'Attendance']])
                    
                    # Display average, max, and min marks with student names
                    max_mark = df[selected_subject].max()
                    min_mark = df[selected_subject].min()
                    max_mark_student = df[df[selected_subject] == max_mark]['Name'].values[0]
                    min_mark_student = df[df[selected_subject] == min_mark]['Name'].values[0]
                    
                    # Use display_cards for subject performance summary
                    display_cards(f"{selected_subject} Performance Summary", subject_avg, max_mark, min_mark)
                    
                    # Include the summary in the document
                    subject_summary = f"""
                    Number of students needing improvement in {selected_subject}: {len(struggling_students)}

                    {selected_subject} Performance Summary
                    Average Marks: {subject_avg:.2f}/100

                    Highest Marks: {max_mark} (Student: {max_mark_student})

                    Lowest Marks: {min_mark} (Student: {min_mark_student})
                    """
                    # Option to download the subject-wise insights as a document
                    subject_doc = save_insights_to_docx(f"{selected_subject} Performance Insights", subject_summary, charts)
                    buffer = BytesIO()
                    subject_doc.save(buffer)
                    buffer.seek(0)
                    st.download_button(label=f"Download {selected_subject} Insights", data=buffer, file_name=f"{selected_subject}_insights.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
            elif analysis_type == "Attendance Analysis":
                st.markdown("<h1 style=font-size:30px;font-family:Garamond,serif;>Attendance Analysis</h1>",unsafe_allow_html=True)
                
                # Attendance distribution
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.histplot(data=df, x="Attendance", bins=10, kde=True, ax=ax, color="green")
                ax.set_title("Class Attendance Distribution", fontsize=16)
                ax.set_xlabel('Attendance (%)', fontsize=14)
                ax.set_ylabel('Frequency', fontsize=14)
                sns.despine(fig)
                st.pyplot(fig)
                
                # Get attendance insights
                st.markdown("<h1 style=font-size:30px;font-family:Garamond,serif;>Attendance Insights</h1>",unsafe_allow_html=True)
                insights = attendance_insights(df)
                st.write(insights)
    
                # Use display_cards for attendance summary
                avg_attendance = df['Attendance'].mean()
                highest_attendance = df['Attendance'].max()
                lowest_attendance = df['Attendance'].min()
    
                display_cards("Class Attendance Summary", avg_attendance, highest_attendance, lowest_attendance)

                charts = [fig]

                # Option to download the insights as a document
                attendance_doc = save_insights_to_docx("Attendance Insights", insights, charts)
                buffer = BytesIO()
                attendance_doc.save(buffer)
                buffer.seek(0)
                st.download_button(label="Download Attendance Insights", data=buffer, file_name="attendance_insights.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
            elif analysis_type=="Ask Questions To The Data":
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

                    # Load the data
                df = pd.read_csv(uploaded_file)

                # Display the dataframe
                # st.write("### Uploaded Data", df)

                # Ask the teacher to input a question
                question = st.text_area("Ask a question about the dataset :")

                if st.button("Get Answer"):
                    # Convert dataframe to a string format
                    context = df.to_string(index=False)

                    # Query ChatGPT
                    answer = query_chatgpt(question, context)

                    # Display the answer
                    # st.write("### Answer from ChatGPT")
                    st.success(answer)

                
    else:
        st.info("Please upload a CSV file with the following columns: Roll No, Name, Attendance, and at least one subject column.")


