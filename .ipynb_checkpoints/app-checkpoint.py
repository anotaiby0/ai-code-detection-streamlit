import streamlit as st
import joblib
import pandas as pd

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="AI Code Detection Model Test",
    layout="wide"
)

# --------------------------------------------------
# Load model
# --------------------------------------------------
@st.cache_resource
def load_model():
    return joblib.load("best_ai_code_pipeline.pkl")

pipeline = load_model()

# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("AI Code Detection Model Test")
st.write("Paste your source code below, then click Predict.")

code_input = st.text_area(
    "Source Code",
    height=400,
    placeholder="Paste code here..."
)

if st.button("Predict"):
    if not code_input.strip():
        st.warning("Please paste some code first.")
    else:
        # Prediction
        prediction = pipeline.predict([code_input])[0]
        label = "AI" if int(prediction) == 1 else "Human"

        # Probabilities (if supported)
        ai_pct = None
        human_pct = None

        if hasattr(pipeline, "predict_proba"):
            probs = pipeline.predict_proba([code_input])[0]
            human_pct = probs[0] * 100
            ai_pct = probs[1] * 100

        # Results table
        results_df = pd.DataFrame({
            "Metric": ["Prediction", "AI Probability (%)", "Human Probability (%)"],
            "Value": [
                label,
                f"{ai_pct:.2f}" if ai_pct is not None else "N/A",
                f"{human_pct:.2f}" if human_pct is not None else "N/A"
            ]
        })

        st.subheader("Prediction Results")
        st.table(results_df)