from sys import prefix
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import datetime, pytz
import glob, os
import plotly.graph_objects as go
from scipy.signal import find_peaks

excel_type =["vnd.ms-excel","vnd.openxmlformats-officedocument.spreadsheetml.sheet", "vnd.oasis.opendocument.spreadsheet", "vnd.oasis.opendocument.text"]

def plotly_any_axis(data, title="", x_variable=None, *args):
    fig = go.Figure()

    # Plot each specified column on the same plot
    for column in args:
        fig.add_trace(go.Scatter(x=data[x_variable], y=data[column], mode='lines', name=column))

    # Format the figure
    fig.update_layout(title=title)

    # Set the x-axis title
    fig.update_layout(xaxis_title=x_variable)

    # Set the same range (adjust as needed) for the y-axis
    # Right now, I have it set to 100, but you can use "auto-scale" on the interactive graph
    fig.update_layout(yaxis=dict(range=[0, 100]))

    # Recolor to avoid overlapping colors
    fig.for_each_trace(lambda t: t.update(line=dict(color=t.marker.color)))

    return fig

def find_and_print_peaks(data, x_variable, variable_thresholds, selected_variables):
    for column in selected_variables:
        # Find peaks in the current column with a minimum height threshold
        threshold = variable_thresholds.get(column, 0)  # Default threshold is 0 if not specified
        peaks, _ = find_peaks(data[column], height=threshold)

        # Display a table of peak information
        print(f'\n{column} Peaks')

        peak_info = []
        for i in range(len(peaks)):
            peak_time = data.loc[peaks[i], x_variable]
            peak_value = data.loc[peaks[i], column]

            peak_info.append({
                'Peak Time': peak_time, 'Peak Value': peak_value,
            })

        # Calculate and print the average value for all data points
        average_value_all = data[column].mean()
        print(f"Average Value (All): {average_value_all:.2f}")

        # Calculate and print the average value for peaks only
        average_value_peaks = data.loc[peaks, column].mean()
        print(f"Average Value (Peaks): {average_value_peaks:.2f}")

        peak_info_table = pd.DataFrame(peak_info)
        print("\nPeak Information:")
        print(peak_info_table)


# Threshold values for peaks
thresholds = {
    'IAT (C)': 0.0,
    'INJPW': 0.0,
    'MAP (kPa)': 0.0,
    'RPM (rpm)': 0.0,
    'TPS (%)': 0.0,
    'BARO': 0.0,
    'CLT': 0.0,
    'FUELP': 0.0,
    'OILP': 0.0,
    'OILT': 0.0,
    'VSPD': 0.0,
    'CoolingSwitch': 0.0,
    'FuelPump': 0.0,
    'MaxCoolSwitch': 0.0,
    'OutputCurrent': 0.0,
    'OutputLoad': 0.0,
    'OutputVoltage': 0.0,
    'WaterPump': 0.0,
    'Channel ID (none)': 0.0,
}

def process_excel_file(file_path):
    try:
        # Read the Excel file
        logfile = pd.read_excel(file_path, engine='openpyxl')  # Specify the engine explicitly
        
        # Pull out logging date
        logging_started = logfile.iloc[4, 1]
        print(logging_started)

        # Edit the file
        logfile_edited = pd.read_excel(file_path, skiprows=6, engine='openpyxl')  # Specify the engine explicitly
        
        # Fix formatting in column names
        for i, col in enumerate(logfile_edited.columns):
            if not pd.isna(logfile_edited.iloc[0, i]):
                new_col_name = f"{col} ({logfile_edited.iloc[0, i]})" # Add units from first row
                logfile_edited = logfile_edited.rename(columns={col: new_col_name}) # rename the columns with updated names
        logfile_edited = logfile_edited[1:] # Remove the first row, as the units have been added to the header
        
        return logfile_edited
    except pd.errors.ParserError:
        st.error("Error: Please upload a valid Excel file.")
        return None


def data(data, file_type, seperator=None):

    if file_type == "csv":
        data = pd.read_csv(data)

   # elif file_type == "json":
    #    data = pd.read_json(data)
    #    data = (data["devices"].apply(pd.Series))
    
    elif file_type in excel_type:
        data = pd.read_excel(data)
        st.sidebar.info("If you are using Excel file so there could be chance of getting minor error(temporary sollution: avoid the error by removing overview option from input box) so bear with it. It will be fixed soon")
    
    elif file_type == "plain":
        try:
            data = pd.read_table(data, sep=seperator)
        except ValueError:
            st.info("If you haven't Type the separator then dont worry about the error this error will go as you type the separator value and hit Enter.")

    return data

def seconddata(data, file_type, seperator=None):

    if file_type == "csv":
        data = pd.read_csv(data)

   # elif file_type == "json":
    #    data = pd.read_json(data)
    #    data = (data["devices"].apply(pd.Series))
    
    elif file_type in excel_type:
        data = pd.read_excel(data)
        st.sidebar.info("If you are using Excel file so there could be chance of getting minor error(temporary sollution: avoid the error by removing overview option from input box) so bear with it. It will be fixed soon")
    
    elif file_type == "plain":
        try:
            data = pd.read_table(data, sep=seperator)
        except ValueError:
            st.info("If you haven't Type the separator then dont worry about the error this error will go as you type the separator value and hit Enter.")

    return data


def match_elements(list_a, list_b):
    non_match = []
    for i in list_a:
        if i  in list_b:
            non_match.append(i)
    return non_match


def download_data(data, label):
    current_time = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
    current_time = "{}.{}-{}-{}".format(current_time.date(), current_time.hour, current_time.minute, current_time.second)
    export_data = st.download_button(
                        label="Download {} data as CSV".format(label),
                        data=data.to_csv(),
                        file_name='{}{}.csv'.format(label, current_time),
                        mime='text/csv',
                        help = "When You Click On Download Button You can download your {} CSV File".format(label)
                    )
    return export_data


def describe(data):
    global num_category, str_category
    num_category = [feature for feature in data.columns if data[feature].dtypes != "O"]
    str_category = [feature for feature in data.columns if data[feature].dtypes == "O"]
    column_with_null_values = data.columns[data.isnull().any()]
    return data.describe(), data.shape, data.columns, num_category, str_category, data.isnull().sum(),data.dtypes.astype("str"), data.nunique(), str_category, column_with_null_values


def outliers(data, num_category_outliers):
    plt.figure(figsize=(6,2))
    flierprops = dict(marker='o', markerfacecolor='purple', markersize=6,
                    linestyle='none', markeredgecolor='black')
    
    path_list = []
    for i in range(len(num_category_outliers)):
        
        column = num_category_outliers[i]
        plt.xlim(min(data[column]), max(data[column])) 
        plt.title("Checking Outliers for {} Column".format(column))
        plot = sns.boxplot(x=column, flierprops=flierprops, data=data)
        fig = plot.get_figure()

        path = 'temp/pic{}.png'.format(i)
        fig.savefig(path)
        path_list.append(path)

    return path_list



def drop_items(data, selected_name):
    droped = data.drop(selected_name, axis = 1)
    return droped


def filter_data(data, selected_column, selected_name):
    if selected_name == []:
        filtered_data = data
    else:
        filtered_data = data[~ data[selected_column].isin(selected_name)]
    return filtered_data


def num_filter_data(data, start_value, end_value, column, param):
    if param == "Delete data inside the range":
        if column in num_category:
            num_filtered_data = data[~data[column].isin(range(int(start_value), int(end_value)+1))]
    else:
        if column in num_category:
            num_filtered_data = data[data[column].isin(range(int(start_value), int(end_value)+1))]
    
    return num_filtered_data


def rename_columns(data, column_names):
    rename_column = data.rename(columns=column_names)
    return rename_column


def handling_missing_values(data, option_type, dict_value=None):
    if option_type == "Drop all null value rows":
        data = data.dropna()

    elif option_type == "Only Drop Rows that contanines all null values":
        data = data.dropna(how="all")
    
    elif option_type == "Filling in Missing Values":
        data = data.fillna(dict_value)
    
    return data


def data_wrangling(data1, data2, key, usertype):
    if usertype == "Merging On Index":
        data = pd.merge(data1, data2, on=key, suffixes=("_extra", "_extra0"))
        data = data[data.columns.drop(list(data.filter(regex='_extra')))]
        return data
    
    elif usertype == "Concatenating On Axis":
        data = pd.concat([data1, data2], ignore_index=True)
        return data



def clear_image_cache():
    removing_files = glob.glob('temp/*.png')
    for i in removing_files:
        os.remove(i)