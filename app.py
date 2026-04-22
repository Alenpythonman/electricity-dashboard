import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Thatchers Electricity Dashboard", layout="wide")

st.title("Thatchers Half Hourly Electricity Dashboard")

df = pd.read_csv("thatchers_half_hourly_cleaned.csv")
df["DateTime"] = pd.to_datetime(df["DateTime"])
df["Date"] = pd.to_datetime(df["Date"]).dt.date

st.sidebar.header("Filters")
min_date = df["Date"].min()
max_date = df["Date"].max()

start_date = st.sidebar.date_input("Start date", min_date)
end_date = st.sidebar.date_input("End date", max_date)

filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()

total_kwh = filtered_df["kWh"].sum()
avg_kwh = filtered_df["kWh"].mean()
peak_kwh = filtered_df["kWh"].max()
peak_time = filtered_df.loc[filtered_df["kWh"].idxmax(), "DateTime"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total kWh", f"{total_kwh:,.1f}")
col2.metric("Average Half Hourly kWh", f"{avg_kwh:,.1f}")
col3.metric("Peak Half Hourly kWh", f"{peak_kwh:,.1f}")
col4.metric("Peak Time", str(peak_time))

st.subheader("Daily Electricity Consumption")
daily = filtered_df.groupby(filtered_df["DateTime"].dt.date)["kWh"].sum().reset_index()
daily.columns = ["Date", "Daily_kWh"]

fig1, ax1 = plt.subplots(figsize=(12, 4))
ax1.plot(daily["Date"], daily["Daily_kWh"])
ax1.set_title("Daily Electricity Consumption")
ax1.set_xlabel("Date")
ax1.set_ylabel("kWh")
ax1.grid(True)
plt.xticks(rotation=45)
st.pyplot(fig1)

st.subheader("Average Half Hourly Load Profile")
filtered_df["TimeOnly"] = filtered_df["DateTime"].dt.strftime("%H:%M")
avg_profile = filtered_df.groupby("TimeOnly")["kWh"].mean().reset_index()

fig2, ax2 = plt.subplots(figsize=(12, 4))
ax2.plot(avg_profile["TimeOnly"], avg_profile["kWh"])
ax2.set_title("Average Half Hourly Load Profile")
ax2.set_xlabel("Time of Day")
ax2.set_ylabel("Average kWh")
ax2.grid(True)
plt.xticks(rotation=90)
st.pyplot(fig2)

st.subheader("Monthly Electricity Consumption")
filtered_df["MonthName"] = filtered_df["DateTime"].dt.month_name()
monthly = filtered_df.groupby("MonthName")["kWh"].sum().reset_index()

month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
monthly["MonthName"] = pd.Categorical(monthly["MonthName"], categories=month_order, ordered=True)
monthly = monthly.sort_values("MonthName")

fig3, ax3 = plt.subplots(figsize=(12, 4))
ax3.bar(monthly["MonthName"], monthly["kWh"])
ax3.set_title("Monthly Electricity Consumption")
ax3.set_xlabel("Month")
ax3.set_ylabel("kWh")
plt.xticks(rotation=45)
st.pyplot(fig3)

st.subheader("Average Half Hourly Consumption by Day of Week")
filtered_df["DayName"] = filtered_df["DateTime"].dt.day_name()
weekday = filtered_df.groupby("DayName")["kWh"].mean().reset_index()

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday["DayName"] = pd.Categorical(weekday["DayName"], categories=day_order, ordered=True)
weekday = weekday.sort_values("DayName")

fig4, ax4 = plt.subplots(figsize=(10, 4))
ax4.bar(weekday["DayName"], weekday["kWh"])
ax4.set_title("Average Half Hourly Consumption by Day of Week")
ax4.set_xlabel("Day")
ax4.set_ylabel("Average kWh")
st.pyplot(fig4)

st.subheader("Load Duration Curve")
ldc = filtered_df["kWh"].sort_values(ascending=False).reset_index(drop=True)

fig5, ax5 = plt.subplots(figsize=(12, 4))
ax5.plot(ldc)
ax5.set_title("Load Duration Curve")
ax5.set_xlabel("Interval Rank")
ax5.set_ylabel("kWh")
ax5.grid(True)
st.pyplot(fig5)

st.subheader("Weekday vs Weekend Load Profile")
filtered_df["IsWeekend"] = filtered_df["DateTime"].dt.dayofweek >= 5
profile_compare = filtered_df.groupby(["IsWeekend", "TimeOnly"])["kWh"].mean().reset_index()

weekday_profile = profile_compare[profile_compare["IsWeekend"] == False]
weekend_profile = profile_compare[profile_compare["IsWeekend"] == True]

fig6, ax6 = plt.subplots(figsize=(12, 4))
ax6.plot(weekday_profile["TimeOnly"], weekday_profile["kWh"], label="Weekday")
ax6.plot(weekend_profile["TimeOnly"], weekend_profile["kWh"], label="Weekend")
ax6.set_title("Weekday vs Weekend Average Profile")
ax6.set_xlabel("Time of Day")
ax6.set_ylabel("Average kWh")
ax6.grid(True)
ax6.legend()
plt.xticks(rotation=90)
st.pyplot(fig6)

st.subheader("Top 10 Daily Peaks")
daily_peaks = filtered_df.groupby(filtered_df["DateTime"].dt.date)["kWh"].max().reset_index()
daily_peaks.columns = ["Date", "Peak_kWh"]
daily_peaks = daily_peaks.nlargest(10, "Peak_kWh")
st.dataframe(daily_peaks, use_container_width=True)

st.subheader("Top 10 Peak Half Hourly Intervals")
top_peaks = filtered_df.nlargest(10, "kWh")[["DateTime", "kWh"]]
st.dataframe(top_peaks, use_container_width=True)

st.subheader("Simple Peak Shaving Battery Estimate")
target_limit = st.number_input("Target peak limit kWh per half hour", min_value=0.0, value=float(round(avg_kwh, 1)))
excess = (filtered_df["kWh"] - target_limit).clip(lower=0)
estimated_battery_energy = excess.sum() * 0.5
estimated_max_discharge = excess.max()

c1, c2 = st.columns(2)
c1.metric("Estimated Battery Energy Needed, kWh", f"{estimated_battery_energy:,.1f}")
c2.metric("Estimated Max Discharge Power Equivalent", f"{estimated_max_discharge * 2:,.1f} kW")

st.subheader("Download Filtered Data")
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="filtered_thatchers_data.csv",
    mime="text/csv"
)