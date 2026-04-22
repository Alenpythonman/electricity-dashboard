import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Battery Selection Dashboard", layout="wide")

# -----------------------------
# Load data
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("thatchers_half_hourly_cleaned.csv")
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df

df = load_data()

# -----------------------------
# Sidebar filters (ONLY ONCE)
# -----------------------------
st.sidebar.header("Filters")

min_date = df["Date"].min()
max_date = df["Date"].max()

start_date = st.sidebar.date_input("Start date", min_date, key="start")
end_date = st.sidebar.date_input("End date", max_date, key="end")

filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()

if filtered_df.empty:
    st.warning("No data available")
    st.stop()

# -----------------------------
# Derived columns
# -----------------------------
filtered_df["Power_kW"] = filtered_df["kWh"] * 2
filtered_df["TimeOnly"] = filtered_df["DateTime"].dt.strftime("%H:%M")
filtered_df["DayName"] = filtered_df["DateTime"].dt.day_name()
filtered_df["Hour"] = filtered_df["DateTime"].dt.hour
filtered_df["IsWeekend"] = filtered_df["DateTime"].dt.dayofweek >= 5

# -----------------------------
# KPIs
# -----------------------------
total_energy = filtered_df["kWh"].sum()
avg_kw = filtered_df["Power_kW"].mean()
peak_kw = filtered_df["Power_kW"].max()
peak_time = filtered_df.loc[filtered_df["Power_kW"].idxmax(), "DateTime"]

p95 = filtered_df["Power_kW"].quantile(0.95)
p99 = filtered_df["Power_kW"].quantile(0.99)
base_load = filtered_df["Power_kW"].quantile(0.1)

st.title("Battery Selection and Load Analysis Dashboard")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Energy (kWh)", f"{total_energy:,.0f}")
k2.metric("Average Demand (kW)", f"{avg_kw:,.1f}")
k3.metric("Peak Demand (kW)", f"{peak_kw:,.1f}")
k4.metric("P95 Demand (kW)", f"{p95:,.1f}")

st.markdown(f"Peak occurred at **{peak_time}**")

# -----------------------------
# Load Profile
# -----------------------------
st.subheader("Average Power by Time of Day")

profile = filtered_df.groupby("TimeOnly")["Power_kW"].mean()

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(profile)
ax.set_ylabel("kW")
ax.set_xlabel("Time")
plt.xticks(rotation=90)
st.pyplot(fig)

# -----------------------------
# Load Duration Curve
# -----------------------------
st.subheader("Load Duration Curve")

ldc = filtered_df["Power_kW"].sort_values(ascending=False).reset_index(drop=True)

fig2, ax2 = plt.subplots(figsize=(10, 4))
ax2.plot(ldc)
ax2.set_ylabel("kW")
ax2.set_xlabel("Rank")
st.pyplot(fig2)

# -----------------------------
# Heatmap
# -----------------------------
st.subheader("Demand Heatmap")

heatmap = filtered_df.pivot_table(
    index=filtered_df["DateTime"].dt.date,
    columns="TimeOnly",
    values="Power_kW"
)

fig3, ax3 = plt.subplots(figsize=(15, 5))
im = ax3.imshow(heatmap, aspect="auto")
plt.colorbar(im, ax=ax3)
ax3.set_title("Demand Heatmap (kW)")
st.pyplot(fig3)

# -----------------------------
# Battery Model
# -----------------------------
st.subheader("Battery Selection")

target_kw = st.number_input("Target demand limit (kW)", value=float(p95))

eff = st.number_input("Efficiency (%)", value=90.0) / 100
dod = st.number_input("Depth of Discharge (%)", value=90.0) / 100

target_kwh = target_kw / 2

excess = (filtered_df["kWh"] - target_kwh).clip(lower=0)

battery_energy = excess.sum() * 0.5
battery_power = excess.max() * 2

battery_capacity = (battery_energy / eff) / dod if eff > 0 and dod > 0 else 0

b1, b2, b3 = st.columns(3)
b1.metric("Battery Power (kW)", f"{battery_power:,.1f}")
b2.metric("Battery Energy (kWh)", f"{battery_energy:,.1f}")
b3.metric("Installed Capacity (kWh)", f"{battery_capacity:,.1f}")

# -----------------------------
# Savings
# -----------------------------
st.subheader("Savings and ROI")

price = st.number_input("Energy price (£/kWh)", value=0.15)
demand_charge = st.number_input("Demand charge (£/kW/month)", value=10.0)

annual_factor = 365 / filtered_df["Date"].nunique()

annual_energy = battery_energy * annual_factor
energy_savings = annual_energy * price

demand_savings = (peak_kw - target_kw) * demand_charge * 12

total_savings = energy_savings + demand_savings

capex = battery_capacity * 250 + battery_power * 150

payback = capex / total_savings if total_savings > 0 else 0

r1, r2, r3 = st.columns(3)
r1.metric("Annual Savings (£)", f"{total_savings:,.0f}")
r2.metric("Battery Cost (£)", f"{capex:,.0f}")
r3.metric("Payback (years)", f"{payback:,.1f}")

# -----------------------------
# Report Summary
# -----------------------------
st.subheader("Report Summary")

st.markdown(f"""
- Peak demand: **{peak_kw:,.1f} kW**
- P95 demand: **{p95:,.1f} kW**
- Base load: **{base_load:,.1f} kW**
- Recommended battery: **{battery_capacity:,.0f} kWh / {battery_power:,.0f} kW**
- Estimated savings: **£{total_savings:,.0f} per year**
- Estimated payback: **{payback:,.1f} years**
""")

# -----------------------------
# Download
# -----------------------------
st.subheader("Download Data")

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download CSV",
    csv,
    "filtered_data.csv",
    "text/csv"
)
