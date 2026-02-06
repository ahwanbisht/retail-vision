from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Retail Vision Management", layout="wide")
st.title("Retail Vision — Management Analytics")

st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Start date", date.today() - timedelta(days=7))
end_date = st.sidebar.date_input("End date", date.today())

if start_date > end_date:
    st.error("Start date must be before end date")
    st.stop()

date_series = pd.date_range(start=start_date, end=end_date, freq="D")
index = range(len(date_series))
mock_data = pd.DataFrame(
    {
        "date": date_series,
        "footfall": [180 + (i * 9) % 110 for i in index],
        "product_popularity": [70 + (i * 7) % 40 for i in index],
    }
)

st.subheader("Historical Reports")
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(px.line(mock_data, x="date", y="footfall", title="Daily Footfall Trends"), use_container_width=True)
with c2:
    st.plotly_chart(
        px.bar(mock_data, x="date", y="product_popularity", title="Product Popularity (Interactions)"),
        use_container_width=True,
    )

st.subheader("Export")
st.download_button(
    "Export CSV report",
    data=mock_data.to_csv(index=False),
    file_name="retail_vision_report.csv",
    mime="text/csv",
)
