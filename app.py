import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Battery Selection and Load Analysis Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("thatchers_half_hourly_cleaned.csv")
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df

df = load_data()

st.title("Battery Selection and Load Analysis Dashboard")
st.caption("Half hourly electricity analysis for electrical engineering assessment, battery sizing, and reporting")

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Date Filters")

min_date = df["Date"].min()
max_date = df["Date"].max()

start_date = st.sidebar.date_input("Start date", min_date)
end_date = st.sidebar.date_input("End date", max_date)

filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()

if filtered_df.empty:
    st.warning("No data available for the selected date range.")
    st.stop()

# -----------------------------
# Derived columns
# -----------------------------
filtered_df["TimeOnly"] = filtered_df["DateTime"].dt.strftime("%H:%M")
filtered_df["MonthName"] = filtered_df["DateTime"].dt.month_name()
filtered_df["DayName"] = filtered_df["DateTime"].dt.day_name()
filtered_df["Hour"] = filtered_df["DateTime"].dt.hour
filtered_df["IsWeekend"] = filtered_df["DateTime"].dt.dayofweek >= 5
filtered_df["Power_kW"] = filtered_df["kWh"] * 2

# -----------------------------
# KPIs
# -----------------------------
total_energy_kwh = filtered_df["kWh"].sum()
num_days = filtered_df["Date"].nunique()
avg_daily_energy_kwh = total_energy_kwh / num_days if num_days > 0 else 0

avg_demand_kw = filtered_df["Power_kW"].mean()
peak_demand_kw = filtered_df["Power_kW"].max()
peak_row = filtered_df.loc[filtered_df["Power_kW"].idxmax()]
peak_time = peak_row["DateTime"]

load_factor = (avg_demand_kw / peak_demand_kw) * 100 if peak_demand_kw > 0 else 0

base_load_kw = filtered_df["Power_kW"].quantile(0.10)
p50_kw = filtered_df["Power_kW"].quantile(0.50)
p90_kw = filtered_df["Power_kW"].quantile(0.90)
p95_kw = filtered_df["Power_kW"].quantile(0.95)
p99_kw = filtered_df["Power_kW"].quantile(0.99)

st.subheader("Key Performance Indicators")

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Energy", f"{total_energy_kwh:,.0f} kWh")
k2.metric("Average Daily Energy", f"{avg_daily_energy_kwh:,.0f} kWh")
k3.metric("Average Demand", f"{avg_demand_kw:,.1f} kW")
k4.metric("Peak Demand", f"{peak_demand_kw:,.1f} kW")
k5.metric("Load Factor", f"{load_factor:,.1f}%")
k6.metric("Days Selected", f"{num_days}")

st.markdown(
    f"""
**Peak interval timestamp:** {peak_time}  
**Base load estimate:** {base_load_kw:,.1f} kW  
"""
)

st.subheader("Demand Percentiles")

p1, p2, p3, p4, p5 = st.columns(5)
p1.metric("P50", f"{p50_kw:,.1f} kW")
p2.metric("P90", f"{p90_kw:,.1f} kW")
p3.metric("P95", f"{p95_kw:,.1f} kW")
p4.metric("P99", f"{p99_kw:,.1f} kW")
p5.metric("Base Load", f"{base_load_kw:,.1f} kW")

# -----------------------------
# Trends
# -----------------------------
st.subheader("Energy and Demand Trends")

daily_energy = filtered_df.groupby(filtered_df["DateTime"].dt.date)["kWh"].sum().reset_index()
daily_energy.columns = ["Date", "Daily_Energy_kWh"]

month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

monthly_energy = filtered_df.groupby("MonthName")["kWh"].sum().reset_index()
monthly_energy["MonthName"] = pd.Categorical(monthly_energy["MonthName"], categories=month_order, ordered=True)
monthly_energy = monthly_energy.sort_values("MonthName")

trend1, trend2 = st.columns(2)

with trend1:
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(daily_energy["Date"], daily_energy["Daily_Energy_kWh"])
    ax1.set_title("Daily Energy Consumption")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Energy (kWh)")
    ax1.grid(True)
    plt.xticks(rotation=45)
    st.pyplot(fig1)

with trend2:
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.bar(monthly_energy["MonthName"], monthly_energy["kWh"])
    ax2.set_title("Monthly Energy Consumption")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Energy (kWh)")
    plt.xticks(rotation=45)
    st.pyplot(fig2)

# -----------------------------
# Load behaviour
# -----------------------------
st.subheader("Load Behaviour")

avg_profile = filtered_df.groupby("TimeOnly")["Power_kW"].mean().reset_index()

profile_compare = filtered_df.groupby(["IsWeekend", "TimeOnly"])["Power_kW"].mean().reset_index()
weekday_profile = profile_compare[profile_compare["IsWeekend"] == False]
weekend_profile = profile_compare[profile_compare["IsWeekend"] == True]

weekday_avg = filtered_df.groupby("DayName")["Power_kW"].mean().reset_index()
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_avg["DayName"] = pd.Categorical(weekday_avg["DayName"], categories=day_order, ordered=True)
weekday_avg = weekday_avg.sort_values("DayName")

ldc = filtered_df["Power_kW"].sort_values(ascending=False).reset_index(drop=True)

lb1, lb2 = st.columns(2)

with lb1:
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.plot(avg_profile["TimeOnly"], avg_profile["Power_kW"])
    ax3.set_title("Average Power by Time of Day")
    ax3.set_xlabel("Time of Day")
    ax3.set_ylabel("Average Power (kW)")
    ax3.grid(True)
    plt.xticks(rotation=90)
    st.pyplot(fig3)

with lb2:
    fig4, ax4 = plt.subplots(figsize=(8, 4))
    ax4.plot(weekday_profile["TimeOnly"], weekday_profile["Power_kW"], label="Weekday")
    ax4.plot(weekend_profile["TimeOnly"], weekend_profile["Power_kW"], label="Weekend")
    ax4.set_title("Weekday vs Weekend Average Power")
    ax4.set_xlabel("Time of Day")
    ax4.set_ylabel("Average Power (kW)")
    ax4.grid(True)
    ax4.legend()
    plt.xticks(rotation=90)
    st.pyplot(fig4)

lb3, lb4 = st.columns(2)

with lb3:
    fig5, ax5 = plt.subplots(figsize=(8, 4))
    ax5.bar(weekday_avg["DayName"], weekday_avg["Power_kW"])
    ax5.set_title("Average Demand by Day")
    ax5.set_xlabel("Day")
    ax5.set_ylabel("Average Power (kW)")
    st.pyplot(fig5)

with lb4:
    fig6, ax6 = plt.subplots(figsize=(8, 4))
    ax6.plot(ldc)
    ax6.set_title("Load Duration Curve")
    ax6.set_xlabel("Interval Rank")
    ax6.set_ylabel("Power (kW)")
    ax6.grid(True)
    st.pyplot(fig6)

# -----------------------------
# Threshold analysis
# -----------------------------
st.subheader("Demand Threshold Analysis")

threshold_kw = st.number_input("Demand threshold (kW)", min_value=0.0, value=float(round(p95_kw, 1)), step=10.0)

intervals_above = (filtered_df["Power_kW"] > threshold_kw).sum()
percent_above = (intervals_above / len(filtered_df)) * 100
max_above_kw = filtered_df.loc[filtered_df["Power_kW"] > threshold_kw, "Power_kW"].max() if intervals_above > 0 else 0

th1, th2, th3 = st.columns(3)
th1.metric("Intervals Above Threshold", f"{intervals_above}")
th2.metric("Percent of Intervals", f"{percent_above:,.2f}%")
th3.metric("Maximum Demand Above Threshold", f"{max_above_kw:,.1f} kW")

# -----------------------------
# Peak analysis
# -----------------------------
st.subheader("Peak Analysis")

daily_peaks = filtered_df.groupby(filtered_df["DateTime"].dt.date)["Power_kW"].max().reset_index()
daily_peaks.columns = ["Date", "Peak_Demand_kW"]
daily_peaks = daily_peaks.nlargest(10, "Peak_Demand_kW")

top_peaks = filtered_df.nlargest(10, "Power_kW")[["DateTime", "Power_kW", "Hour", "DayName"]]

pk1, pk2 = st.columns(2)

with pk1:
    st.markdown("**Top 10 Daily Peaks**")
    st.dataframe(daily_peaks, use_container_width=True)

with pk2:
    st.markdown("**Top 10 Half Hourly Peaks**")
    st.dataframe(top_peaks, use_container_width=True)
    # -----------------------------
# Demand Heatmap
# -----------------------------
st.subheader("Demand Heatmap")

heatmap_metric = st.radio(
    "Heatmap display",
    ["Average Power (kW)", "Maximum Power (kW)"],
    horizontal=True
)

if heatmap_metric == "Average Power (kW)":
    heatmap_data = filtered_df.pivot_table(
        index=filtered_df["DateTime"].dt.date,
        columns="TimeOnly",
        values="Power_kW",
        aggfunc="mean"
    )
else:
    heatmap_data = filtered_df.pivot_table(
        index=filtered_df["DateTime"].dt.date,
        columns="TimeOnly",
        values="Power_kW",
        aggfunc="max"
    )

fig_hm, ax_hm = plt.subplots(figsize=(16, 6))
im = ax_hm.imshow(heatmap_data, aspect="auto")
ax_hm.set_title(heatmap_metric + " by Date and Time")
ax_hm.set_xlabel("Time of Day")
ax_hm.set_ylabel("Date")

# reduce x labels so they are readable
x_positions = range(0, len(heatmap_data.columns), 4)
x_labels = [heatmap_data.columns[i] for i in x_positions]
ax_hm.set_xticks(x_positions)
ax_hm.set_xticklabels(x_labels, rotation=90)

# reduce y labels so they are readable
if len(heatmap_data.index) > 20:
    y_positions = range(0, len(heatmap_data.index), max(1, len(heatmap_data.index) // 15))
else:
    y_positions = range(len(heatmap_data.index))

y_labels = [str(heatmap_data.index[i]) for i in y_positions]
ax_hm.set_yticks(y_positions)
ax_hm.set_yticklabels(y_labels)

cbar = plt.colorbar(im, ax=ax_hm)
cbar.set_label("Power (kW)")

st.pyplot(fig_hm)

# -----------------------------
# Realistic battery sizing
# -----------------------------
st.subheader("Battery Selection Assessment")

st.markdown("Use the controls below to estimate battery size for peak shaving against a target demand limit.")

bs1, bs2, bs3, bs4 = st.columns(4)

with bs1:
    target_limit_kw = st.number_input("Target demand limit (kW)", min_value=0.0, value=float(round(p95_kw, 1)), step=10.0)

with bs2:
    round_trip_efficiency = st.number_input("Round trip efficiency (%)", min_value=50.0, max_value=100.0, value=90.0, step=1.0)

with bs3:
    usable_dod = st.number_input("Usable depth of discharge (%)", min_value=10.0, max_value=100.0, value=90.0, step=1.0)

with bs4:
    max_discharge_duration_hours = st.number_input("Minimum discharge duration to support (hours)", min_value=0.5, max_value=8.0, value=1.0, step=0.5)

target_interval_kwh = target_limit_kw / 2

excess_interval_kwh = (filtered_df["kWh"] - target_interval_kwh).clip(lower=0)

raw_peak_shaving_energy_kwh = excess_interval_kwh.sum() * 0.5
required_battery_power_kw = excess_interval_kwh.max() * 2
peak_reduction_kw = max(0, peak_demand_kw - target_limit_kw)

efficiency_factor = round_trip_efficiency / 100
dod_factor = usable_dod / 100

usable_energy_required_kwh = raw_peak_shaving_energy_kwh / efficiency_factor if efficiency_factor > 0 else 0
installed_battery_capacity_kwh = usable_energy_required_kwh / dod_factor if dod_factor > 0 else 0

duration_based_capacity_kwh = required_battery_power_kw * max_discharge_duration_hours
recommended_battery_capacity_kwh = max(installed_battery_capacity_kwh, duration_based_capacity_kwh)

rb1, rb2, rb3, rb4 = st.columns(4)
rb1.metric("Target Demand Limit", f"{target_limit_kw:,.1f} kW")
rb2.metric("Peak Reduction Potential", f"{peak_reduction_kw:,.1f} kW")
rb3.metric("Required Battery Power", f"{required_battery_power_kw:,.1f} kW")
rb4.metric("Raw Shaved Energy", f"{raw_peak_shaving_energy_kwh:,.1f} kWh")

rb5, rb6, rb7 = st.columns(3)
rb5.metric("Efficiency Adjusted Energy", f"{usable_energy_required_kwh:,.1f} kWh")
rb6.metric("Installed Capacity from DoD", f"{installed_battery_capacity_kwh:,.1f} kWh")
rb7.metric("Recommended Battery Capacity", f"{recommended_battery_capacity_kwh:,.1f} kWh")

st.caption(
    "Recommended battery capacity takes the larger of two sizing checks: energy adjusted for efficiency and usable depth of discharge, and power sustained for the chosen discharge duration. This is still a screening tool and should be followed by a dispatch study."
)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Battery Selection and Load Analysis Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("thatchers_half_hourly_cleaned.csv")
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df

df = load_data()

st.title("Battery Selection and Load Analysis Dashboard")
st.caption("Half hourly electricity analysis for electrical engineering assessment, battery sizing, and reporting")

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Date Filters")

min_date = df["Date"].min()
max_date = df["Date"].max()

start_date = st.sidebar.date_input("Start date", min_date)
end_date = st.sidebar.date_input("End date", max_date)

filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()

if filtered_df.empty:
    st.warning("No data available for the selected date range.")
    st.stop()

# -----------------------------
# Derived columns
# -----------------------------
filtered_df["TimeOnly"] = filtered_df["DateTime"].dt.strftime("%H:%M")
filtered_df["MonthName"] = filtered_df["DateTime"].dt.month_name()
filtered_df["DayName"] = filtered_df["DateTime"].dt.day_name()
filtered_df["Hour"] = filtered_df["DateTime"].dt.hour
filtered_df["IsWeekend"] = filtered_df["DateTime"].dt.dayofweek >= 5
filtered_df["Power_kW"] = filtered_df["kWh"] * 2

# -----------------------------
# KPIs
# -----------------------------
total_energy_kwh = filtered_df["kWh"].sum()
num_days = filtered_df["Date"].nunique()
avg_daily_energy_kwh = total_energy_kwh / num_days if num_days > 0 else 0

avg_demand_kw = filtered_df["Power_kW"].mean()
peak_demand_kw = filtered_df["Power_kW"].max()
peak_row = filtered_df.loc[filtered_df["Power_kW"].idxmax()]
peak_time = peak_row["DateTime"]

load_factor = (avg_demand_kw / peak_demand_kw) * 100 if peak_demand_kw > 0 else 0

base_load_kw = filtered_df["Power_kW"].quantile(0.10)
p50_kw = filtered_df["Power_kW"].quantile(0.50)
p90_kw = filtered_df["Power_kW"].quantile(0.90)
p95_kw = filtered_df["Power_kW"].quantile(0.95)
p99_kw = filtered_df["Power_kW"].quantile(0.99)

st.subheader("Key Performance Indicators")

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Energy", f"{total_energy_kwh:,.0f} kWh")
k2.metric("Average Daily Energy", f"{avg_daily_energy_kwh:,.0f} kWh")
k3.metric("Average Demand", f"{avg_demand_kw:,.1f} kW")
k4.metric("Peak Demand", f"{peak_demand_kw:,.1f} kW")
k5.metric("Load Factor", f"{load_factor:,.1f}%")
k6.metric("Days Selected", f"{num_days}")

st.markdown(
    f"""
**Peak interval timestamp:** {peak_time}  
**Base load estimate:** {base_load_kw:,.1f} kW  
"""
)

st.subheader("Demand Percentiles")

p1, p2, p3, p4, p5 = st.columns(5)
p1.metric("P50", f"{p50_kw:,.1f} kW")
p2.metric("P90", f"{p90_kw:,.1f} kW")
p3.metric("P95", f"{p95_kw:,.1f} kW")
p4.metric("P99", f"{p99_kw:,.1f} kW")
p5.metric("Base Load", f"{base_load_kw:,.1f} kW")

# -----------------------------
# Trends
# -----------------------------
st.subheader("Energy and Demand Trends")

daily_energy = filtered_df.groupby(filtered_df["DateTime"].dt.date)["kWh"].sum().reset_index()
daily_energy.columns = ["Date", "Daily_Energy_kWh"]

month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

monthly_energy = filtered_df.groupby("MonthName")["kWh"].sum().reset_index()
monthly_energy["MonthName"] = pd.Categorical(monthly_energy["MonthName"], categories=month_order, ordered=True)
monthly_energy = monthly_energy.sort_values("MonthName")

trend1, trend2 = st.columns(2)

with trend1:
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(daily_energy["Date"], daily_energy["Daily_Energy_kWh"])
    ax1.set_title("Daily Energy Consumption")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Energy (kWh)")
    ax1.grid(True)
    plt.xticks(rotation=45)
    st.pyplot(fig1)

with trend2:
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.bar(monthly_energy["MonthName"], monthly_energy["kWh"])
    ax2.set_title("Monthly Energy Consumption")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Energy (kWh)")
    plt.xticks(rotation=45)
    st.pyplot(fig2)

# -----------------------------
# Load behaviour
# -----------------------------
st.subheader("Load Behaviour")

avg_profile = filtered_df.groupby("TimeOnly")["Power_kW"].mean().reset_index()

profile_compare = filtered_df.groupby(["IsWeekend", "TimeOnly"])["Power_kW"].mean().reset_index()
weekday_profile = profile_compare[profile_compare["IsWeekend"] == False]
weekend_profile = profile_compare[profile_compare["IsWeekend"] == True]

weekday_avg = filtered_df.groupby("DayName")["Power_kW"].mean().reset_index()
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_avg["DayName"] = pd.Categorical(weekday_avg["DayName"], categories=day_order, ordered=True)
weekday_avg = weekday_avg.sort_values("DayName")

ldc = filtered_df["Power_kW"].sort_values(ascending=False).reset_index(drop=True)

lb1, lb2 = st.columns(2)

with lb1:
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.plot(avg_profile["TimeOnly"], avg_profile["Power_kW"])
    ax3.set_title("Average Power by Time of Day")
    ax3.set_xlabel("Time of Day")
    ax3.set_ylabel("Average Power (kW)")
    ax3.grid(True)
    plt.xticks(rotation=90)
    st.pyplot(fig3)

with lb2:
    fig4, ax4 = plt.subplots(figsize=(8, 4))
    ax4.plot(weekday_profile["TimeOnly"], weekday_profile["Power_kW"], label="Weekday")
    ax4.plot(weekend_profile["TimeOnly"], weekend_profile["Power_kW"], label="Weekend")
    ax4.set_title("Weekday vs Weekend Average Power")
    ax4.set_xlabel("Time of Day")
    ax4.set_ylabel("Average Power (kW)")
    ax4.grid(True)
    ax4.legend()
    plt.xticks(rotation=90)
    st.pyplot(fig4)

lb3, lb4 = st.columns(2)

with lb3:
    fig5, ax5 = plt.subplots(figsize=(8, 4))
    ax5.bar(weekday_avg["DayName"], weekday_avg["Power_kW"])
    ax5.set_title("Average Demand by Day")
    ax5.set_xlabel("Day")
    ax5.set_ylabel("Average Power (kW)")
    st.pyplot(fig5)

with lb4:
    fig6, ax6 = plt.subplots(figsize=(8, 4))
    ax6.plot(ldc)
    ax6.set_title("Load Duration Curve")
    ax6.set_xlabel("Interval Rank")
    ax6.set_ylabel("Power (kW)")
    ax6.grid(True)
    st.pyplot(fig6)

# -----------------------------
# Threshold analysis
# -----------------------------
st.subheader("Demand Threshold Analysis")

threshold_kw = st.number_input("Demand threshold (kW)", min_value=0.0, value=float(round(p95_kw, 1)), step=10.0)

intervals_above = (filtered_df["Power_kW"] > threshold_kw).sum()
percent_above = (intervals_above / len(filtered_df)) * 100
max_above_kw = filtered_df.loc[filtered_df["Power_kW"] > threshold_kw, "Power_kW"].max() if intervals_above > 0 else 0

th1, th2, th3 = st.columns(3)
th1.metric("Intervals Above Threshold", f"{intervals_above}")
th2.metric("Percent of Intervals", f"{percent_above:,.2f}%")
th3.metric("Maximum Demand Above Threshold", f"{max_above_kw:,.1f} kW")

# -----------------------------
# Peak analysis
# -----------------------------
st.subheader("Peak Analysis")

daily_peaks = filtered_df.groupby(filtered_df["DateTime"].dt.date)["Power_kW"].max().reset_index()
daily_peaks.columns = ["Date", "Peak_Demand_kW"]
daily_peaks = daily_peaks.nlargest(10, "Peak_Demand_kW")

top_peaks = filtered_df.nlargest(10, "Power_kW")[["DateTime", "Power_kW", "Hour", "DayName"]]

pk1, pk2 = st.columns(2)

with pk1:
    st.markdown("**Top 10 Daily Peaks**")
    st.dataframe(daily_peaks, use_container_width=True)

with pk2:
    st.markdown("**Top 10 Half Hourly Peaks**")
    st.dataframe(top_peaks, use_container_width=True)
    # -----------------------------
# Demand Heatmap
# -----------------------------
st.subheader("Demand Heatmap")

heatmap_metric = st.radio(
    "Heatmap display",
    ["Average Power (kW)", "Maximum Power (kW)"],
    horizontal=True
)

if heatmap_metric == "Average Power (kW)":
    heatmap_data = filtered_df.pivot_table(
        index=filtered_df["DateTime"].dt.date,
        columns="TimeOnly",
        values="Power_kW",
        aggfunc="mean"
    )
else:
    heatmap_data = filtered_df.pivot_table(
        index=filtered_df["DateTime"].dt.date,
        columns="TimeOnly",
        values="Power_kW",
        aggfunc="max"
    )

fig_hm, ax_hm = plt.subplots(figsize=(16, 6))
im = ax_hm.imshow(heatmap_data, aspect="auto")
ax_hm.set_title(heatmap_metric + " by Date and Time")
ax_hm.set_xlabel("Time of Day")
ax_hm.set_ylabel("Date")

# reduce x labels so they are readable
x_positions = range(0, len(heatmap_data.columns), 4)
x_labels = [heatmap_data.columns[i] for i in x_positions]
ax_hm.set_xticks(x_positions)
ax_hm.set_xticklabels(x_labels, rotation=90)

# reduce y labels so they are readable
if len(heatmap_data.index) > 20:
    y_positions = range(0, len(heatmap_data.index), max(1, len(heatmap_data.index) // 15))
else:
    y_positions = range(len(heatmap_data.index))

y_labels = [str(heatmap_data.index[i]) for i in y_positions]
ax_hm.set_yticks(y_positions)
ax_hm.set_yticklabels(y_labels)

cbar = plt.colorbar(im, ax=ax_hm)
cbar.set_label("Power (kW)")

st.pyplot(fig_hm)

# -----------------------------
# Realistic battery sizing
# -----------------------------
st.subheader("Battery Selection Assessment")

st.markdown("Use the controls below to estimate battery size for peak shaving against a target demand limit.")

bs1, bs2, bs3, bs4 = st.columns(4)

with bs1:
    target_limit_kw = st.number_input("Target demand limit (kW)", min_value=0.0, value=float(round(p95_kw, 1)), step=10.0)

with bs2:
    round_trip_efficiency = st.number_input("Round trip efficiency (%)", min_value=50.0, max_value=100.0, value=90.0, step=1.0)

with bs3:
    usable_dod = st.number_input("Usable depth of discharge (%)", min_value=10.0, max_value=100.0, value=90.0, step=1.0)

with bs4:
    max_discharge_duration_hours = st.number_input("Minimum discharge duration to support (hours)", min_value=0.5, max_value=8.0, value=1.0, step=0.5)

target_interval_kwh = target_limit_kw / 2

excess_interval_kwh = (filtered_df["kWh"] - target_interval_kwh).clip(lower=0)

raw_peak_shaving_energy_kwh = excess_interval_kwh.sum() * 0.5
required_battery_power_kw = excess_interval_kwh.max() * 2
peak_reduction_kw = max(0, peak_demand_kw - target_limit_kw)

efficiency_factor = round_trip_efficiency / 100
dod_factor = usable_dod / 100

usable_energy_required_kwh = raw_peak_shaving_energy_kwh / efficiency_factor if efficiency_factor > 0 else 0
installed_battery_capacity_kwh = usable_energy_required_kwh / dod_factor if dod_factor > 0 else 0

duration_based_capacity_kwh = required_battery_power_kw * max_discharge_duration_hours
recommended_battery_capacity_kwh = max(installed_battery_capacity_kwh, duration_based_capacity_kwh)

rb1, rb2, rb3, rb4 = st.columns(4)
rb1.metric("Target Demand Limit", f"{target_limit_kw:,.1f} kW")
rb2.metric("Peak Reduction Potential", f"{peak_reduction_kw:,.1f} kW")
rb3.metric("Required Battery Power", f"{required_battery_power_kw:,.1f} kW")
rb4.metric("Raw Shaved Energy", f"{raw_peak_shaving_energy_kwh:,.1f} kWh")

rb5, rb6, rb7 = st.columns(3)
rb5.metric("Efficiency Adjusted Energy", f"{usable_energy_required_kwh:,.1f} kWh")
rb6.metric("Installed Capacity from DoD", f"{installed_battery_capacity_kwh:,.1f} kWh")
rb7.metric("Recommended Battery Capacity", f"{recommended_battery_capacity_kwh:,.1f} kWh")

st.caption(
    "Recommended battery capacity takes the larger of two sizing checks: energy adjusted for efficiency and usable depth of discharge, and power sustained for the chosen discharge duration. This is still a screening tool and should be followed by a dispatch study."
)

# -----------------------------
# Engineering interpretation
# -----------------------------
st.subheader("Engineering Interpretation Prompts")

st.markdown(f"""
- **P95 demand** is **{p95_kw:,.1f} kW**, which is a strong starting point for defining a practical peak shaving threshold.
- **P99 demand** is **{p99_kw:,.1f} kW**, showing the level of more extreme but less frequent peaks.
- **Peak demand** is **{peak_demand_kw:,.1f} kW**, so compare this against the P95 and P99 values to judge whether the site has occasional spikes or sustained high demand.
- **Base load estimate** is **{base_load_kw:,.1f} kW**, which helps define the lower operating band of the facility.
- If the selected target limit is close to P95, the battery is likely being used for frequent peak trimming.
- If the selected target limit is much lower than P95, the calculated battery size may become commercially unrealistic.
""")

# -----------------------------
# Download
# -----------------------------
# -----------------------------
# Report Summary
# -----------------------------
st.subheader("Report Summary")

weekday_mean_kw = filtered_df.loc[filtered_df["IsWeekend"] == False, "Power_kW"].mean()
weekend_mean_kw = filtered_df.loc[filtered_df["IsWeekend"] == True, "Power_kW"].mean()

if pd.isna(weekday_mean_kw):
    weekday_mean_kw = 0

if pd.isna(weekend_mean_kw):
    weekend_mean_kw = 0

if weekend_mean_kw > 0:
    weekday_vs_weekend_pct = ((weekday_mean_kw - weekend_mean_kw) / weekend_mean_kw) * 100
else:
    weekday_vs_weekend_pct = 0

report_summary = f"""
**Reporting period:** {start_date} to {end_date}

**Load profile overview**
- Total site energy consumption over the selected period was **{total_energy_kwh:,.0f} kWh**.
- Average daily energy consumption was **{avg_daily_energy_kwh:,.0f} kWh/day**.
- Average site demand was **{avg_demand_kw:,.1f} kW**, with a recorded peak demand of **{peak_demand_kw:,.1f} kW** at **{peak_time}**.
- The estimated base load was **{base_load_kw:,.1f} kW**.
- Demand percentile review shows **P50 = {p50_kw:,.1f} kW**, **P90 = {p90_kw:,.1f} kW**, **P95 = {p95_kw:,.1f} kW**, and **P99 = {p99_kw:,.1f} kW**.

**Behaviour and operating pattern**
- The load factor over the selected period was **{load_factor:,.1f}%**, which indicates the relationship between typical and peak demand.
- Average weekday demand was **{weekday_mean_kw:,.1f} kW** and average weekend demand was **{weekend_mean_kw:,.1f} kW**.
- This indicates that weekday demand is approximately **{weekday_vs_weekend_pct:,.1f}%** {'higher' if weekday_vs_weekend_pct >= 0 else 'lower'} than weekend demand.

**Battery screening assessment**
- Using a target demand limit of **{target_limit_kw:,.1f} kW**, the estimated peak reduction potential is **{peak_reduction_kw:,.1f} kW**.
- The required battery discharge power is estimated at **{required_battery_power_kw:,.1f} kW**.
- The raw peak shaving energy requirement is **{raw_peak_shaving_energy_kwh:,.1f} kWh**.
- After applying **{round_trip_efficiency:,.0f}%** round trip efficiency and **{usable_dod:,.0f}%** usable depth of discharge, the estimated installed battery capacity is **{installed_battery_capacity_kwh:,.1f} kWh**.
- Based on the selected minimum discharge support duration of **{max_discharge_duration_hours:,.1f} hours**, the recommended battery capacity is **{recommended_battery_capacity_kwh:,.1f} kWh**.

**Engineering note**
- This dashboard provides a screening level assessment for battery selection and peak shaving suitability.
- Final battery specification should be confirmed using a detailed dispatch study including tariff structure, charge strategy, state of charge limits, efficiency losses, and operational constraints.
"""

st.markdown(report_summary)
st.subheader("Download Filtered Data")

csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download filtered dataset as CSV",
    data=csv,
    file_name="filtered_thatchers_data.csv",
    mime="text/csv"
)
# -----------------------------
# Engineering interpretation
# -----------------------------
st.subheader("Engineering Interpretation Prompts")

st.markdown(f"""
- **P95 demand** is **{p95_kw:,.1f} kW**, which is a strong starting point for defining a practical peak shaving threshold.
- **P99 demand** is **{p99_kw:,.1f} kW**, showing the level of more extreme but less frequent peaks.
- **Peak demand** is **{peak_demand_kw:,.1f} kW**, so compare this against the P95 and P99 values to judge whether the site has occasional spikes or sustained high demand.
- **Base load estimate** is **{base_load_kw:,.1f} kW**, which helps define the lower operating band of the facility.
- If the selected target limit is close to P95, the battery is likely being used for frequent peak trimming.
- If the selected target limit is much lower than P95, the calculated battery size may become commercially unrealistic.
""")

# -----------------------------
# Download
# -----------------------------
# -----------------------------
# Report Summary
# -----------------------------
st.subheader("Report Summary")

weekday_mean_kw = filtered_df.loc[filtered_df["IsWeekend"] == False, "Power_kW"].mean()
weekend_mean_kw = filtered_df.loc[filtered_df["IsWeekend"] == True, "Power_kW"].mean()

if pd.isna(weekday_mean_kw):
    weekday_mean_kw = 0

if pd.isna(weekend_mean_kw):
    weekend_mean_kw = 0

if weekend_mean_kw > 0:
    weekday_vs_weekend_pct = ((weekday_mean_kw - weekend_mean_kw) / weekend_mean_kw) * 100
else:
    weekday_vs_weekend_pct = 0

report_summary = f"""
**Reporting period:** {start_date} to {end_date}

**Load profile overview**
- Total site energy consumption over the selected period was **{total_energy_kwh:,.0f} kWh**.
- Average daily energy consumption was **{avg_daily_energy_kwh:,.0f} kWh/day**.
- Average site demand was **{avg_demand_kw:,.1f} kW**, with a recorded peak demand of **{peak_demand_kw:,.1f} kW** at **{peak_time}**.
- The estimated base load was **{base_load_kw:,.1f} kW**.
- Demand percentile review shows **P50 = {p50_kw:,.1f} kW**, **P90 = {p90_kw:,.1f} kW**, **P95 = {p95_kw:,.1f} kW**, and **P99 = {p99_kw:,.1f} kW**.

**Behaviour and operating pattern**
- The load factor over the selected period was **{load_factor:,.1f}%**, which indicates the relationship between typical and peak demand.
- Average weekday demand was **{weekday_mean_kw:,.1f} kW** and average weekend demand was **{weekend_mean_kw:,.1f} kW**.
- This indicates that weekday demand is approximately **{weekday_vs_weekend_pct:,.1f}%** {'higher' if weekday_vs_weekend_pct >= 0 else 'lower'} than weekend demand.

**Battery screening assessment**
- Using a target demand limit of **{target_limit_kw:,.1f} kW**, the estimated peak reduction potential is **{peak_reduction_kw:,.1f} kW**.
- The required battery discharge power is estimated at **{required_battery_power_kw:,.1f} kW**.
- The raw peak shaving energy requirement is **{raw_peak_shaving_energy_kwh:,.1f} kWh**.
- After applying **{round_trip_efficiency:,.0f}%** round trip efficiency and **{usable_dod:,.0f}%** usable depth of discharge, the estimated installed battery capacity is **{installed_battery_capacity_kwh:,.1f} kWh**.
- Based on the selected minimum discharge support duration of **{max_discharge_duration_hours:,.1f} hours**, the recommended battery capacity is **{recommended_battery_capacity_kwh:,.1f} kWh**.

**Engineering note**
- This dashboard provides a screening level assessment for battery selection and peak shaving suitability.
- Final battery specification should be confirmed using a detailed dispatch study including tariff structure, charge strategy, state of charge limits, efficiency losses, and operational constraints.
"""

st.markdown(report_summary)
st.subheader("Download Filtered Data")

csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download filtered dataset as CSV",
    data=csv,
    file_name="filtered_thatchers_data.csv",
    mime="text/csv"
)
