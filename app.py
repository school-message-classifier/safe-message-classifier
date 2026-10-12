
import streamlit as st
from pathlib import Path
import joblib

# إعداد الصفحة
st.set_page_config(
    page_title="مساعد الحاج والمعتمر",
    page_icon="🕋",
    layout="centered"
)

# تنسيق عربي من اليمين إلى اليسار
st.markdown("""
<style>
    .stApp {
        direction: rtl;
        text-align: right;
    }

    h1, h2, h3, p, label, div {
        text-align: right;
    }

    .stTextArea textarea {
        direction: rtl;
        text-align: right;
    }

    .result-box {
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #d9e2df;
        margin-top: 16px;
    }
</style>
""", unsafe_allow_html=True)

# دليل الجهات
CONTACTS = {
    "حج وخدمات": {
        "name": "وزارة الحج والعمرة",
        "phone": "1966"
    },
    "صحي": {
        "name": "وزارة الصحة",
        "phone": "937"
    },
    "شرعي": {
        "name": "وزارة الشؤون الإسلامية",
        "phone": "8002451000"
    },
    "أمني طارئ": {
        "name": "مركز العمليات الأمنية الموحدة",
        "phone": "911"
    }
}

# تحميل النموذج إن كان موجودًا
MODEL_PATH = Path("model.joblib")
model = None

if MODEL_PATH.exists():
    try:
        model = joblib.load(MODEL_PATH)
    except Exception:
        st.error("تعذر تحميل نموذج التصنيف.")

# عنوان الواجهة
st.title("🕋 مساعد الحاج والمعتمر")

st.write(
    "اكتب استفسارك، وسيساعدك التطبيق على "
    "تحديد الجهة المناسبة للتواصل."
)

st.info(
    "هذا مشروع تعليمي. إذا كانت الحالة طارئة، "
    "تواصل مباشرة مع جهة الطوارئ المناسبة ولا تنتظر نتيجة النموذج."
)

# إدخال النص
with st.form("request_form"):
    request_text = st.text_area(
        "ما الذي تحتاج إلى المساعدة فيه؟",
        placeholder="اكتب استفسارك هنا...",
        height=140
    )

    submitted = st.form_submit_button(
        "تصنيف الطلب",
        use_container_width=True
    )

# معالجة الطلب
if submitted:
    if not request_text.strip():
        st.warning("يرجى كتابة الاستفسار أولًا.")

    elif model is None:
        st.warning(
            "الواجهة جاهزة، لكن نموذج التصنيف لم يُربط بعد. "
            "سنربطه بعد تدريبه في Google Colab."
        )

    else:
        try:
            # يتوقع النموذج اسم الفئة
            category = str(model.predict([request_text])[0])

            if category in CONTACTS:
                contact = CONTACTS[category]

                st.subheader("نتيجة التصنيف")

                st.markdown(
                    f"""
                    <div class="result-box">
                        <p><strong>الفئة:</strong> {category}</p>
                        <p><strong>الجهة:</strong> {contact["name"]}</p>
                        <p><strong>رقم التواصل:</strong>
                        {contact["phone"]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.caption(
                    "تحقق من ملاءمة الجهة لطلبك؛ فقد يخطئ النموذج في التصنيف."
                )

            else:
                st.error(
                    "أعاد النموذج فئة غير معروفة. "
                    "يرجى مراجعة بيانات التدريب."
                )

        except Exception:
            st.error(
                "حدث خطأ أثناء التصنيف. "
                "تحقق من توافق النموذج مع الواجهة."
            )
