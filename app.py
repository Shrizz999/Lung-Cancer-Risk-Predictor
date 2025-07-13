import streamlit as st
import pandas as pd
import joblib
from fpdf import FPDF
import base64


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


def generate_pdf(full_name, df, prediction, proba):
    pdf = StyledPDF()
    pdf.add_page()

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Name: {full_name}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", '', 12)
    for col in df.columns:
        val = df[col].values[0]
        if col != 'AGE':
            val = bin_to_yesno(val)
        pdf.data_row(col, val)

    result = "High Risk" if prediction == 1 else "Low Risk"
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(220, 53, 69) if prediction == 1 else pdf.set_fill_color(40, 167, 69)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, f"Prediction: {result}", ln=True, fill=True)
    pdf.cell(0, 10, f"Prediction Confidence: {proba * 100:.2f}%", ln=True, fill=True)

    pdf.set_text_color(0, 0, 0)
    path = "Lung-Cancer_Prediction_Report.pdf"
    pdf.output(path)
    return path


st.set_page_config(page_title="Lung Cancer Risk Prediction", layout="centered")

st.sidebar.title("🔍 About")
st.sidebar.info("""
This app uses a Machine Learning model to predict the risk of lung cancer based on medical and lifestyle inputs.
""")
st.sidebar.title("📬 Contact")
st.sidebar.info("Questions? Email: `shrizzites@gmail.com`")

# Disclaimer
st.sidebar.title("⚠️ Disclaimer")
st.sidebar.info("""
This app is for informational purposes only and should not be used as a substitute for professional medical advice.
""")

st.title("Lung Cancer Risk Prediction")
full_name = st.text_input("Enter your full name:")

AGE = st.slider('Age', 1, 100, 25)
GENDER_M = st.selectbox('Gender', ('MALE', 'FEMALE'))
SMOKING = st.selectbox('Do you smoke?', ('YES', 'NO'))
YELLOW_FINGERS = st.selectbox('Yellow fingers?', ('YES', 'NO'))
ANXIETY = st.selectbox('Anxiety?', ('YES', 'NO'))
CHRONIC_DISEASE = st.selectbox('Chronic disease?', ('YES', 'NO'))
FATIGUE = st.selectbox('Fatigue?', ('YES', 'NO'))
ALLERGY = st.selectbox('Allergy?', ('YES', 'NO'))
WHEEZING = st.selectbox('Wheezing?', ('YES', 'NO'))
ALCOHOL_CONSUMING = st.selectbox('Alcohol consumption?', ('YES', 'NO'))
COUGHING = st.selectbox('Coughing?', ('YES', 'NO'))
SHORTNESS_OF_BREATH = st.selectbox('Shortness of breath?', ('YES', 'NO'))
SWALLOWING_DIFFICULTY = st.selectbox('Swallowing difficulty?', ('YES', 'NO'))
CHEST_PAIN = st.selectbox('Chest pain?', ('YES', 'NO'))

if st.button("🔍 Predict"):
    input_data = [[AGE, GENDER_M, SMOKING, YELLOW_FINGERS, ANXIETY,
                   CHRONIC_DISEASE, FATIGUE, ALLERGY, WHEEZING, ALCOHOL_CONSUMING,
                   COUGHING, SHORTNESS_OF_BREATH, SWALLOWING_DIFFICULTY, CHEST_PAIN]]

    df = pd.DataFrame(input_data, columns=expected_columns)

    for col in expected_columns:
        if df[col].dtype == 'object':
            df[col] = df[col].map({'YES': 1, 'NO': 0, 'MALE': 1, 'FEMALE': 0})

    prediction = model.predict(df)[0]
    proba = float(model.predict_proba(df)[0][1])
    result_label = "High Risk" if prediction else "Low Risk"

 
    if prediction == 1:
        st.markdown(
            f'<div style="background-color:#dc3545;padding:10px;border-radius:8px;color:white;font-weight:bold;">🧪 Prediction: High Risk</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="background-color:#28a745;padding:10px;border-radius:8px;color:white;font-weight:bold;">🧪 Prediction: Low Risk</div>',
            unsafe_allow_html=True)

    st.metric("📊 Confidence", f"{proba * 100:.2f}%")

    pdf_path = generate_pdf(full_name, df, prediction, proba)
    with open(pdf_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="Lung_Cancer_Prediction_Report.pdf">📄 Download Report</a>'
        st.markdown(href, unsafe_allow_html=True)

    if "past_predictions" not in st.session_state:
        st.session_state.past_predictions = []

    display_df = df.copy()
    for col in display_df.columns:
        if col != 'AGE':
            display_df[col] = bin_to_yesno(display_df[col].values[0])
    st.session_state.past_predictions.append((full_name, display_df, result_label, proba))


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

st.markdown("---")
st.caption("🔒 Data is not stored. All predictions are local and for demo use only.")
