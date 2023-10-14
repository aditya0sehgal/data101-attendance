from flask import Flask, render_template, request, redirect
import pandas as pd
from datetime import datetime

app = Flask(__name__)

df = None
uid_options = []

@app.route('/')
def index():
    return render_template('index.html', uid_options=uid_options)

@app.route('/load_csv', methods=['POST'])
def load_csv_file():
    global df
    global uid_options

    file = request.files['csv_file']

    if file:
        df = pd.read_csv(file)

        df = df.iloc[2:]
        df = df[['RecordedDate', 'uid', 'LocationLongitude', 'LocationLatitude']]
        df = df.dropna()
        df = df[df['uid'] != 'imielins']
        df = df.reset_index(drop=True)
        df['Date'] = pd.to_datetime(df['RecordedDate']).dt.strftime('%m/%d/%Y')
        df['Time'] = pd.to_datetime(df['RecordedDate']).dt.time
        df = df[['uid', 'Date', 'Time', 'LocationLongitude', 'LocationLatitude']]

        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
        uid_options = list(df['uid'].unique())

    return redirect('/')

@app.route('/generate_attendance', methods=['POST'])
def generate_attendance():
    selected_uid = request.form['uid']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    start_date = datetime.strptime(start_date, "%m/%d/%Y")
    end_date = datetime.strptime(end_date, "%m/%d/%Y")

    if selected_uid and start_date and end_date:
        filtered_df = df[(df['uid'] == selected_uid) & (df['Date'] >= start_date) & (df['Date'] <= end_date)]

        unique_tuesdays_thursdays = len(filtered_df[filtered_df['Date'].dt.day_name().isin(['Tuesday', 'Thursday'])]['Date'].unique())

        all_tuesdays_thursdays = pd.date_range(start_date, end_date, freq='W-TUE').union(pd.date_range(start_date, end_date, freq='W-THU'))
        total_tuesdays_thursdays = len(all_tuesdays_thursdays)

        if total_tuesdays_thursdays > 0:
            attendance_percentage = unique_tuesdays_thursdays / total_tuesdays_thursdays
            result_text_percentage = f"Attendance Percentage for {selected_uid}: {attendance_percentage:.2%}"
        else:
            result_text_percentage = "No Tuesdays or Thursdays in the selected date range"

        attendance_count = filtered_df.groupby(['Date']).size().reset_index(name='Count')
        result_text_list = attendance_count.to_html()
    else:
        result_text_percentage = "Please select all necessary inputs."
        result_text_list = "Please select all necessary inputs."

    return render_template('index.html', uid_options=uid_options, result_text_percentage=result_text_percentage, result_text_list=result_text_list)

if __name__ == '__main__':
    app.run(debug=True)
