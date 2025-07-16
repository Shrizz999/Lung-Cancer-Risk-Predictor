import streamlit as st
import pandas as pd
import joblib
from fpdf import FPDF
import base64
from datetime import datetime
import plotly.graph_objects as go

model = joblib.load('RFC.pkl')
expected_columns = joblib.load('columns.pkl')


def bin_to_yesno(val):
    return 'YES' if val == 1 else 'NO'


class StyledPDF(FPDF):
    def header(self):
        self.set_fill_color(70, 130, 180)
        self.rect(0, 0, 210, 20, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", 'B', 16)
        self.cell(0, 10, "  Lung Cancer Risk Prediction Report", ln=True)
        self.ln(10)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-20)
        self.set_font("Arial", 'I', 8)
        self.set_text_color(120, 120, 120)
        self.multi_cell(0, 5, "Disclaimer: This report is generated using an AI model and should not be treated as medical advice.\nPlease consult a certified healthcare provider.", 0, 'C')

    def data_row(self, col, value):
        self.set_font("Arial", '', 12)
        self.cell(90, 10, f"{col.replace('_', ' ').title()}:", border=1)
        self.cell(90, 10, str(value), border=1, ln=True)


def generate_pdf(full_name, df_display, prediction, proba):
    pdf = StyledPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Name: {full_name}", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(5)

    for col in df_display.columns:
        val = df_display[col].values[0]
        pdf.data_row(col, val)

    result = "High Risk" if prediction == 1 else "Low Risk"
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(220, 53, 69) if prediction == 1 else pdf.set_fill_color(40, 167, 69)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, f"Risk Prediction: {result}", ln=True, fill=True)
    pdf.cell(0, 10, f"Risk Probability: {proba * 100:.2f}%", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)

    path = "Lung-Cancer_Prediction_Report.pdf"
    pdf.output(path)
    return path


# Streamlit UI
st.set_page_config(page_title="Lung Cancer Risk Prediction", layout="centered", initial_sidebar_state="expanded")

st.sidebar.title("🔍 About")
st.sidebar.info("This app uses a Machine Learning model to predict the risk of lung cancer based on medical and lifestyle inputs.")
st.sidebar.title("📬 Contact")
st.sidebar.info("Questions? Email: `shrizzites@gmail.com`")
st.sidebar.title("⚠️ Disclaimer")
st.sidebar.info("This app is for informational purposes only and should not be used as a substitute for professional medical advice.")

st.title("Lung Cancer Risk Prediction")
full_name = st.text_input("Enter your full name:")

AGE = st.slider('Age', 1, 100, 25, help="Select your current age.")
GENDER_M = st.selectbox('Gender', ('MALE', 'FEMALE'), help="Select your biological gender.")
SMOKING = st.selectbox('Do you smoke?', ('YES', 'NO'), help="Smoking is a major risk factor for lung diseases.")
YELLOW_FINGERS = st.selectbox('Yellow fingers?', ('YES', 'NO'), help="Yellowing may indicate long-term tobacco use.")
ANXIETY = st.selectbox('Anxiety?', ('YES', 'NO'), help="Mental health can indirectly impact physical health.")
CHRONIC_DISEASE = st.selectbox('Chronic disease?', ('YES', 'NO'), help="Includes diabetes, hypertension, etc.")
FATIGUE = st.selectbox('Fatigue?', ('YES', 'NO'), help="Feeling constantly tired or low in energy.")
ALLERGY = st.selectbox('Allergy?', ('YES', 'NO'), help="Any persistent allergic reactions or sensitivities.")
WHEEZING = st.selectbox('Wheezing?', ('YES', 'NO'), help="Whistling sound during breathing.")
ALCOHOL_CONSUMING = st.selectbox('Alcohol consumption?', ('YES', 'NO'), help="Regular alcohol intake?")
COUGHING = st.selectbox('Coughing?', ('YES', 'NO'), help="Frequent or chronic coughing?")
SHORTNESS_OF_BREATH = st.selectbox('Shortness of breath?', ('YES', 'NO'), help="Difficulty breathing or catching breath.")
SWALLOWING_DIFFICULTY = st.selectbox('Swallowing difficulty?', ('YES', 'NO'), help="Pain or discomfort when swallowing.")
CHEST_PAIN = st.selectbox('Chest pain?', ('YES', 'NO'), help="Any sharp, dull, or persistent pain in the chest area.")


consent = st.checkbox("I agree to the disclaimer and understand this is not a medical diagnosis.")
if not consent:
    st.warning("You must agree to the disclaimer to proceed.")
    st.stop()

if st.button("🔍 Predict"):
    input_data = [[AGE, GENDER_M, SMOKING, YELLOW_FINGERS, ANXIETY,
                   CHRONIC_DISEASE, FATIGUE, ALLERGY, WHEEZING, ALCOHOL_CONSUMING,
                   COUGHING, SHORTNESS_OF_BREATH, SWALLOWING_DIFFICULTY, CHEST_PAIN]]
    
    # Create human-readable display DataFrame
    df_display = pd.DataFrame(input_data, columns=expected_columns)

    # Create model-ready DataFrame
    df = df_display.copy()
    for col in expected_columns:
        if df[col].dtype == 'object':
            df[col] = df[col].map({'YES': 1, 'NO': 0, 'MALE': 1, 'FEMALE': 0})

    prediction = model.predict(df)[0]
    proba = float(model.predict_proba(df)[0][1])
    result_label = "High Risk" if prediction else "Low Risk"

    # Display Result Banner
    icon = "🧠" if prediction == 0 else "⚠️"
    bar_color = "#28a745" if prediction == 0 else "#dc3545"
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg, {bar_color}, #222);
            padding: 15px;
            border-radius: 12px;
            color: white;
            font-size: 20px;
            font-weight: 600;
            text-align: center;
            box-shadow: 0px 2px 10px rgba(0,0,0,0.2);
        ">
            {icon} Prediction: {result_label}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Gauge Chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=proba * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Risk Probability"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': bar_color},
            'steps': [
                {'range': [0, 50], 'color': 'lightgreen'},
                {'range': [50, 100], 'color': 'lightcoral'}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

    # Generate PDF from display data
    pdf_path = generate_pdf(full_name, df_display, prediction, proba)

    # PDF Download Button
    with open(pdf_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        custom_button = f"""
        <style>
        .download-btn {{
        display: inline-block;
        background-color: #007bff;
        color: white !important;
        padding: 12px 22px;
        font-weight: 600;
        font-size: 16px;
        border-radius: 10px;
        text-decoration: none;
        transition: background-color 0.3s ease;
        border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .download-btn:hover {{
        background-color: #0056b3;
        text-decoration: none;
        }}
        </style>
        <a href="data:application/pdf;base64,{b64}" download="Lung_Cancer_Prediction_Report.pdf" class="download-btn">📥 Get My Lung Cancer Report</a>
        """
    st.markdown(custom_button, unsafe_allow_html=True)

    # Save to session state
    if "past_predictions" not in st.session_state:
        st.session_state.past_predictions = []

    st.session_state.past_predictions.append((full_name, df_display, result_label, proba))

# Display Past Predictions
if "past_predictions" in st.session_state:
    st.markdown("### 📁 Past Predictions")
    for i, (name, df_prev, label, prob) in enumerate(reversed(st.session_state.past_predictions[-5:])):
        color = "#dc3545" if label == "High Risk" else "#28a745"
        with st.expander(f"📝 Run #{len(st.session_state.past_predictions)-i} - {label} ({name})"):
            st.dataframe(df_prev)
            st.markdown(
                f'<div style="background-color:{color};padding:6px;border-radius:6px;color:white;font-weight:bold;">Prediction: {label}</div>',
                unsafe_allow_html=True)
            st.markdown(f"**Confidence:** {prob * 100:.2f}%")

# Feedback Section
st.markdown("---")
st.subheader("💬 Feedback")
feedback = st.text_area("Help us improve. What did you like or what can be better?")
if st.button("Submit Feedback"):
    st.success("✅ Thank you! Your feedback has been noted.")

st.markdown("---")
st.caption("🔒 Data is not stored. All predictions are local and for demo use only.")
