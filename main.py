import gspread
import pandas as pd
import streamlit as st
import plotly.express as px


def extract_info_from_file(rawlst):

    # Provide a list of keywords to search for
    keywords = ['Full-time', 'Contract']

    for item in rawlst:
        mail_date = rawlst[0].get('date')
        mail_body = rawlst[0].get('body')
        mail_body_lst = mail_body.replace('\r','').split('\n')

        # Remove spaces between lines
        lines = [line.strip() for line in mail_body_lst if line.strip()]

        # Process each line and extract information
        info_list = []
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
                    "title" : lines[start_index],
                    "org" :  lines[start_index + 1],
                    "location": lines[start_index + 2],
                    "source": lines[start_index + 3],
                    "jobType": lines[start_index + 4],
                    "jobPostingDate" : mail_date
                }
                #info = '\n'.join(lines[start_index:end_index + 1])

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

    st.table(df)

    # 1. Number of jobs per job title
    st.plotly_chart(px.histogram(df.title, x="title",
                  title="Distribution of Athletes age"))



