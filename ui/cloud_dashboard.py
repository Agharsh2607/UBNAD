import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="UBNAD Live Demo", layout="wide")

st.title("🛡️ UBNAD — Unauthorized Background Network Activity Detector")
st.caption("Cloud Demonstration Mode")

apps = ["chrome", "spotify", "vscode", "calculator", "python", "telegram"]
ips = ["142.250.183.14", "20.42.65.91", "185.231.222.33", "104.26.10.78"]

def generate_data():
    data = []
    for _ in range(20):
        app = random.choice(apps)
        score = random.randint(0, 30)

        if score > 20:
            risk = "CRITICAL"
        elif score > 10:
            risk = "HIGH"
        elif score > 5:
            risk = "MEDIUM"
        else:
            risk = "SAFE"

        data.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "application": app,
            "destination": random.choice(ips),
            "suspicion_score": score,
            "risk": risk
        })
    return pd.DataFrame(data)

df = generate_data()

st.subheader("Live Monitoring (Demo Data)")
st.dataframe(df, use_container_width=True)

st.subheader("Alerts")
alerts = df[df["risk"].isin(["HIGH","CRITICAL"])]

if len(alerts)==0:
    st.success("No suspicious behavior detected")
else:
    for _, row in alerts.iterrows():
        st.error(f"{row['application']} contacting {row['destination']} — {row['risk']}")
