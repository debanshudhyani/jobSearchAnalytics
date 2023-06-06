import gspread
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime


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

    st.set_page_config(page_title="Job Search Analytics",
                       page_icon=":bar_chart:",
                       layout="wide")

    df = df.replace(r'^\s*$', float('NaN'), regex=True)  # Replace blanks by NaN
    df.dropna(inplace=True)

    #st.dataframe(df)
    # Convert 'JobPostingDate' column to datetime format
    df['JobPostingDate'] = pd.to_datetime(df['JobPostingDate'])

    # Add 'Month' column
    df['Month'] = df['JobPostingDate'].dt.strftime('%B')

    # sidebar
    st.sidebar.header("Please Filter Here: ")
    location_options = sorted(df["Location"].dropna().unique())
    selected_locations = st.sidebar.multiselect(
        "Select the Location:",
        options=["All"] + location_options,
        default=["All"]
    )

    if "".join(selected_locations) =="All":
        selected_locations= location_options


    JobType = st.sidebar.multiselect(
        "Select the Jobtype: ",
        options=df["JobType"].unique(),
        default=df["JobType"].unique()
    )

    # Date range selection
    min_date = df["JobPostingDate"].min()
    max_date = df["JobPostingDate"].max()
    selected_start_date, selected_end_date = st.sidebar.date_input(
        "Select Date Range:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Data display selection
    display_option = st.sidebar.selectbox(
        "Display Data:",
        options=["Day-wise", "Month-wise"],
        index=0
    )

    analysis_col=""
    if display_option == "Day-wise":
        analysis_col= "JobPostingDate"
    else:
        analysis_col="Month"



    df_selection = df.query(
            "Location in @selected_locations & JobType == @JobType & @selected_start_date <= JobPostingDate <= @selected_end_date"
        )

    st.dataframe(df_selection)



    #0 . number of jobs as per date in graph

    # Count the number of jobs posted on each date
    df_selection.sort_values(analysis_col, inplace=True)
    job_count = df_selection[analysis_col].value_counts().sort_index().reset_index()
    job_count.columns = [analysis_col, 'Count']

    # Sort the month column chronologically
    month_order = pd.to_datetime(job_count[analysis_col], format="%B").dt.month
    job_count = job_count.iloc[month_order.argsort()]

    # Create a line chart using Plotly Express
    fig = px.line(job_count, x=analysis_col, y='Count')

    # Set the chart title
    fig.update_layout(title='Number of Jobs Posted by Date')

    # Format the x-axis tick labels to display only the date
    fig.update_xaxes(tickformat="%Y-%m-%d")

    # Render the chart in Streamlit
    st.plotly_chart(fig)


    # 1. Number of jobs posting as per date and Location

    # Group the DataFrame by 'JobPostingDate' and 'Location' and count the number of titles
    df_selection.sort_values(analysis_col, inplace=True)
    grouped_df = df_selection.groupby([analysis_col, 'Location']).size().reset_index(name='Count')

    # Sort the month data chronologically
    if display_option == "Month-wise":
        month_order = pd.to_datetime(grouped_df[analysis_col], format="%B").dt.month
        grouped_df = grouped_df.iloc[month_order.argsort()]

    # Create a grouped bar chart using Plotly Express
    fig = px.bar(grouped_df, x=analysis_col, y='Count', color='Location',
                 title='Number of Titles Posted by Date and Location')

    # Set the x-axis tick format to show only the date or month
    if display_option == "Day-wise":
        fig.update_layout(xaxis=dict(type='category', categoryorder='category ascending'),
                          xaxis_title=analysis_col)
    else:
        fig.update_layout(xaxis=dict(type='category', categoryorder='array', categoryarray=grouped_df[analysis_col]),
                          xaxis_title=analysis_col)

    # Render the chart in Streamlit
    st.plotly_chart(fig)


    # 2. Location with highest number of jobs

    st.plotly_chart(px.histogram(df_selection.Location, x="Location", title="Location with most number of jobs"))

    # 3. create drop down
    options=df_selection["Location"].unique().tolist()
    selected_location=st.selectbox(
    'Select the location',
    options)

    st.write('You selected:', selected_location)

    # now create a graph as per the selected location
    filtered_df = df_selection[df_selection['Location'] == selected_location]
    fig = px.histogram(filtered_df, x='Title', title='Job Titles')
    st.plotly_chart(fig)

    #4. source of jobs

    st.plotly_chart(px.histogram(df_selection.Source, x="Source", title="sites with most number of jobs"))

    #5. Types of job ratio

    st.plotly_chart(px.histogram(df_selection.JobType, x="JobType", title="Job Type Discription"))

    #6. Companies with most number oj jobs

    st.plotly_chart(px.histogram(df_selection.Org, x="Org", title="Organisation"))




