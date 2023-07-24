import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import os

st.set_page_config(layout="wide", page_title="Hopcharge Dashboard",
                   page_icon=":bar_chart:")


def get_csv_files(directory_path):
    file_list = []

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".csv"):
                file_path = os.path.join(root, file)
                file_list.append(file_path)

    df_list = [pd.read_csv(file) for file in file_list]
    concatenated_df = pd.concat(df_list, ignore_index=True)
    return concatenated_df


path = './data'
df = get_csv_files(path)
df1 = pd.read_csv('EPOD NUMBER.csv')

df = df[df['canceled'] != True]
df['licensePlate'] = df['licensePlate'].str.upper()
df['licensePlate'] = df['licensePlate'].str.replace(
    'HR55AJ4OO3', 'HR55AJ4003')
df['fromTime'] = pd.to_datetime(df['fromTime'])
df.rename(columns={'location.state': 'Customer Location City',
          'fromTime': 'Actual Date'}, inplace=True)
df['Actual Date'] = pd.to_datetime(
    df['Actual Date'], format='mixed', errors='coerce')
df = df[df['Actual Date'].dt.year > 2021]
df['Actual Date'] = df['Actual Date'].dt.date
df['Customer Location City'].replace(
    {'Haryana': 'Gurugram', 'Uttar Pradesh': 'Noida'}, inplace=True)
cities = ['Gurugram', 'Noida', 'Delhi']
df = df[df['Customer Location City'].isin(cities)]


requiredcols = ['Actual Date', 'EPOD Name', 'Customer Location City']

merged_df = pd.merge(df, df1, on=["licensePlate"])
merged_df = merged_df[requiredcols]
merged_df.to_csv('merged.csv')

df = merged_df


def formatINR(number):
    s, *d = str(number).partition(".")
    r = ",".join([s[x-2:x] for x in range(-3, -len(s), -2)][::-1] + [s[-3:]])
    return "".join([r] + d)


def check_credentials():
    st.markdown(
        """
            <style>
                .appview-container .main .block-container {{
                    padding-top: {padding_top}rem;
                    padding-bottom: {padding_bottom}rem;
                    }}

            </style>""".format(
            padding_top=1, padding_bottom=1
        ),
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns(3)

    image = Image.open('LOGO HOPCHARGE-03.png')
    col2.image(image, use_column_width=True)
    col2.markdown(
        "<h2 style='text-align: center;'>ECMS Login</h2>", unsafe_allow_html=True)
    image = Image.open('roaming vans.png')
    col1.image(image, use_column_width=True)

    with col2:
        username = st.text_input("Username")
        password = st.text_input(
            "Password", type="password")

    if username in st.secrets["username"] and password in st.secrets["password"]:
        index = st.secrets["username"].index(username)
        if st.secrets["password"][index] == password:
            st.session_state["logged_in"] = True
        else:
            col2.warning("Invalid username or password.")
    elif username not in st.secrets["username"] or password not in st.secrets["password"]:
        col2.warning("Invalid username or password.")


def main_page():
    st.markdown(
        """
            <style>
                .appview-container .main .block-container {{
                    padding-top: {padding_top}rem;
                    padding-bottom: {padding_bottom}rem;
                    }}

            </style>""".format(
            padding_top=1, padding_bottom=1
        ),
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4, col5 = st.columns(5)
    image = Image.open('LOGO HOPCHARGE-03.png')
    col1.image(image, use_column_width=True)
    col5.write("\n")
    if col5.button("Logout"):
        st.session_state.logged_in = False

    st.markdown(
        "<h2 style='text-align: leftr;'>EV Charging Management System</h2>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        df['Actual Date'] = pd.to_datetime(df['Actual Date'], errors='coerce')
        min_date = df['Actual Date'].min().date()
        max_date = df['Actual Date'].max().date()
        start_date = st.date_input(
            'Start Date', min_value=min_date, max_value=max_date, value=min_date, key="epod-date-start")
    with col2:
        end_date = st.date_input(
            'End Date', min_value=min_date, max_value=max_date, value=max_date, key="epod-date-end")

    epods = df['EPOD Name'].unique()

    with col3:

        EPod = st.multiselect(label='Select The EPod',
                              options=['All'] + epods.tolist(),
                              default='All')
    if 'All' in EPod:
        EPod = epods

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    filtered_data = df[(df['Actual Date'] >= start_date)
                       & (df['Actual Date'] <= end_date)]

    filtered_data = filtered_data[
        (filtered_data['EPOD Name'].isin(EPod))]
    filtered_data['Actual Date'] = pd.to_datetime(filtered_data['Actual Date'])
    df_count = filtered_data.groupby(
        ['Actual Date', 'Customer Location City']).size().reset_index(name='Session Count')
    df_count['Actual Date'] = df_count['Actual Date'].dt.strftime('%d/%m/%y')

    sumcount = df_count['Session Count'].sum()
    col4.metric("Total Sessions of EPods", formatINR(sumcount))
    revenue = sumcount*150
    revenue = formatINR(revenue)
    col5.metric("Total Revenue", f"\u20B9{revenue}")
    fig = px.bar(df_count, x='Actual Date', y='Session Count', color_discrete_map={'Delhi': '#243465', 'Gurugram': ' #5366a0', 'Noida': '#919fc8'},
                 color='Customer Location City', text=df_count['Session Count'])
    total_counts = df_count.groupby('Actual Date')[
        'Session Count'].sum().reset_index()

    for i, date in enumerate(total_counts['Actual Date']):
        fig.add_annotation(
            x=date,

            y=total_counts['Session Count'][i] + 0.9,
            text=str(total_counts['Session Count'][i]),
            showarrow=False,
            align='center',
            font_size=16,
            font=dict(color='black')
        )
    fig.update_layout(
        title='Session Count of All EPods till Date',
        xaxis_title='Date',
        yaxis_title='Session Count',
        xaxis_tickangle=-45,
        width=1200,
        legend_title='HSZs: ',

    )

    with col1:
        st.plotly_chart(fig, use_container_width=False)

    filtered_data = df[df['EPOD Name'].isin(EPod)]

    if (len(EPod) > 1):

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        filtered_data = filtered_data.sort_values('EPOD Name')
        for epod in filtered_data['EPOD Name'].unique():

            with col1:
                st.subheader(epod)
            filtered_data = df[(df['Actual Date'] >= start_date)
                               & (df['Actual Date'] <= end_date)]
            df_count = filtered_data[filtered_data['EPOD Name'] == epod].groupby(
                ['Actual Date', 'Customer Location City']).size().reset_index(name='Session Count')
            df_count['Actual Date'] = df_count['Actual Date'].dt.strftime(
                '%d/%m/%y')
            df_count = df_count.sort_values('Actual Date')
            sumcount = df_count['Session Count'].sum()
            revenue = sumcount*150
            revenue = formatINR(revenue)
            sumcount = formatINR(sumcount)
            col1.metric(f"Total Sessions by {epod}", sumcount)

            col1.metric("Total Revenue", f"\u20B9{revenue}")

            fig = px.bar(df_count, x='Actual Date', y='Session Count',
                         color='Customer Location City', color_discrete_map={'Delhi': '#243465', 'Gurugram': ' #5366a0', 'Noida': '#919fc8'}, text='Session Count')
            total_counts = df_count.groupby('Actual Date')[
                'Session Count'].sum().reset_index()

            for i, date in enumerate(total_counts['Actual Date']):
                fig.add_annotation(
                    x=date,

                    y=total_counts['Session Count'][i]+0.2,
                    text=str(total_counts['Session Count'][i]),
                    showarrow=False,
                    align='center',
                    font_size=18,
                    font=dict(color='black')
                )

            fig.update_xaxes(categoryorder='category ascending')

            fig.update_layout(
                title='Session Count by Date',
                xaxis_title='Date',
                yaxis_title=f'Session Count of {epod}',
                xaxis_tickangle=-45,
                width=1200,
                legend_title='HSZs: '
            )
            with col1:
                st.plotly_chart(fig)


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    main_page()
else:
    check_credentials()
    if st.session_state.logged_in:
        st.experimental_rerun()
