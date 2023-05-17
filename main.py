import gspread
import pandas as pd
import streamlit as st
import plotly.express as px
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode


def extract_info_from_file(rawlst):

    # Provide a list of keywords to search for
    keywords = ['Full-time', 'Contract']
    info_list = []
    for item in rawlst:
        mail_date = item.get('date')
        mail_body = item.get('body')
        mail_body_lst = mail_body.replace('\r','').split('\n')

        # Remove spaces between lines
        lines = [line.strip() for line in mail_body_lst if line.strip()]

        # Process each line and extract information

        for i, line in enumerate(lines):
            # Check if any of the keywords are present in the line
            if any(keyword in line for keyword in keywords):
                # Get the index of the line containing the keyword
                keyword_index = i

                # Replace the line based on the specific keyword
                for keyword in keywords:
                    if keyword in line:
                        if keyword == 'Full-time':
                            lines[keyword_index] = 'Full-time'
                        elif keyword == 'Contract':
                            lines[keyword_index] = 'Contract'
                        break

                # Get the start and end indices for the block of lines to extract
                start_index = max(0, keyword_index - 4)
                end_index = keyword_index

                # Extract the block of lines
                info = {
                    "Title" : lines[start_index],
                    "Org" :  lines[start_index + 1],
                    "Location": lines[start_index + 2].replace("Canada"," "),
                    "Source": lines[start_index + 3].replace("via", " "),
                    "JobType": lines[start_index + 4],
                    "JobPostingDate" : mail_date
                }


                # Add the extracted information to the list
                info_list.append(info)



    return info_list

def read_google_sheet():
    gc = gspread.service_account(filename='token/job-alerts-386113-173efc7f90e9.json')
    sh = gc.open("jobalert")
    rows = sh.sheet1.get_all_records()
    return rows

def createDatafrme(formatedList):
    df = pd.DataFrame(formatedList)

    # Convert the data type of the column to date
    df['JobPostingDate'] = pd.to_datetime(df['JobPostingDate']).dt.date
    return df

if __name__ == "__main__":
    # read the details from the google sheet
    sheetlst = read_google_sheet()

    #format the incomming data
    formatedList = extract_info_from_file(sheetlst)

    #create a dataframe
    df = createDatafrme(formatedList)


    #Start preparing the dashboard
    st.title("Job Search analytics")

    # Create grid options
    grid_options = GridOptionsBuilder.from_dataframe(df)

    # Configure sidebar and enable row selection
    grid_options.configure_side_bar()
    #grid_options.configure_selection('single')

    # Render the DataFrame with sidebar and row selection using st_aggrid
    AgGrid(df[:10], gridOptions=grid_options.build())



    #0 . number of jobs as per date in graph

    # Count the number of jobs posted on each date
    job_count = df['JobPostingDate'].value_counts().reset_index()
    job_count.columns = ['JobPostingDate', 'Count']

    # Create a line chart using Plotly Express
    fig = px.line(job_count, x='JobPostingDate', y='Count')

    # Set the chart title
    fig.update_layout(title='Number of Jobs Posted by Date')

    # Format the x-axis tick labels to display only the date
    fig.update_xaxes(tickformat="%Y-%m-%d")

    # Render the chart in Streamlit
    st.plotly_chart(fig)


    # 1. Number of jobs posting as per date

    # Group the DataFrame by 'JobPostingDate' and 'Location' and count the number of titles
    grouped_df = df.groupby(['JobPostingDate', 'Location']).size().reset_index(name='Count')

    # Create a grouped bar chart using Plotly Express
    fig = px.bar(grouped_df, x='JobPostingDate', y='Count', color='Location',
                 title='Number of Titles Posted by Date and Location')

    # Set the x-axis tick format to show only the date
    fig.update_layout(xaxis=dict(type='category'))

    # Render the chart in Streamlit
    st.plotly_chart(fig)

    # # Group the DataFrame by 'jobPostingDate' and count the number of unique titles
    # grouped_df = df.groupby('JobPostingDate')['Title'].nunique().reset_index(name='count')
    #
    # # Create a grouped bar chart using Plotly Express
    # st.plotly_chart(px.bar(grouped_df, x='JobPostingDate', y='count'))



    # 2. Location with highest number of jobs

    st.plotly_chart(px.histogram(df.Location, x="Location", title="Location with most number of jobs"))

    # 3. create drop down
    options=df["Location"].unique().tolist()
    selected_location=st.selectbox(
    'Select the location',
    options)

    st.write('You selected:', selected_location)

    # now create a graph as per the selected location
    filtered_df = df[df['Location'] == selected_location]
    fig = px.histogram(filtered_df, x='Title', title='Job Titles')
    st.plotly_chart(fig)

    #4. source of jobs

    st.plotly_chart(px.histogram(df.Source, x="Source", title="sites with most number of jobs"))

    #5. Types of job ratio

    st.plotly_chart(px.histogram(df.JobType, x="JobType", title="Job Type Discription"))

    #6. Companies with most number oj jobs

    st.plotly_chart(px.histogram(df.Org, x="Org", title="Organisation"))




