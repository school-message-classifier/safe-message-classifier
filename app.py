
import re
from pathlib import Path

import joblib
import streamlit as st

# إعداد الصفحة
st.set_page_config(
    page_title="المرشد الرسائل الآمن",
    page_icon="🛡️",
    layout="centered"
)

# الأصناف المعتمدة فــي بيانات التدريب
LABELS = ["آمن", "خطير", "تحقق"]

# إرشادات ثابتة مرتبطة بكل صنف
GUIDANCE = {
    "آمن": (
        "لا تظهر مؤشرات خطر واضحة في النص، "
        "لكن هذا لا يضمن سلامة الرسالة."
    ),
    "خطير": (
        "لا تنفذ الطلب المشبوه، ولا تشارك بياناتك أو رموز التحقق. "
        "تحقق من الجهة عبر قناة رسمية مستقلة."
    ),
    "تحقق": (
        "تحقق من هوية المرسل وسبب الرسالة عبر التطبيق أو الموقع الرسمي. "
        " لا تعتمد على رقم المرسل وحده، ولا تفتح الرابط الوارد أو تشارك رموزا."
    )
}

# تحميل النموذج
MODEL_PATH = Path("model.joblib")
model = None

if MODEL_PATH.exists():
    try:
        model = joblib.load(MODEL_PATH)
    except Exception:
        st.error("تعذر تحميل النموذج. تحقق من ملف model.joblib.")

# تنسيق الواجهة العربية
st.markdown("""
<style>
    .stApp {
        direction: rtl;
        text-align: right;
    }

    h1, h2, h3, p, label {
        text-align: right;
    }

    .stTextArea textarea {
        direction: rtl;
        text-align: right;
    }

    .result-box {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #d9e2df;
        margin: 12px 0;
    }
</style>
""", unsafe_allow_html=True)


def extract_links(text):
    """استخراج الروابط الظاهرة دون فتحها."""
    pattern = r'(?i)\b(?:https?://|www\.)[^\s<>"\']+'
    return re.findall(pattern, text)


# واجهة التطبيق
st.title("🛡️ مرشد الرسائل الآمن")

st.write(
    "أدخل رسالة وصلتك لمعرفة تصنيفها والإرشادات المناسبة "
    "للتعامل معها."
)

st.info(
    "يحلل التطبيق نص الرسالة فقط. لا يفتح الروابط، "
    "ولا يستطيع إثبات أن الرسالة أو الرابط آمن أو ضار."
)

with st.form("message_form"):
    message_text = st.text_area(
        "الرسالة الواردة",
        placeholder="الصق الرسالة هنا، بما فيها الرابط إن وجد...",
        height=180
    )

    submitted = st.form_submit_button(
        "تحليل الرسالة",
        use_container_width=True
    )

# معالجة الرسالة
if submitted:
    if not message_text.strip():
        st.warning("يرجى لصق الرسالة أولًا.")

    elif model is None:
        st.warning(
            "لم يُربط نموذج التصنيف بعد. "
            "درّبي النموذج واحفظيه باسم model.joblib."
        )

    else:
        try:
            # استخراج الروابط دون زيارتها
            links = extract_links(message_text)

            if links:
                st.subheader("الروابط الموجودة في الرسالة")
                for link in links:
                    st.code(link, language=None)

                st.caption("عُرضت الروابط كما وردت دون فتحها.")

            # التحقق من أصناف النموذج
            if not hasattr(model, "classes_"):
                st.error(
                    "تعذر التحقق من أصناف النموذج. "
                    "راجعي طريقة التدريب."
                )

            elif set(model.classes_) != set(LABELS):
                st.error(
                    "أصناف النموذج لا تطابق الأصناف المعتمدة: "
                    + "، ".join(LABELS)
                )

            else:
                # اختيار الصنف المتوقع
                prediction = str(model.predict([message_text])[0])

                st.subheader("نتيجة التحليل")

                st.markdown(
                    f"""
                    <div class="result-box">
                        <strong>صنف الرسالة: {prediction}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.subheader("التوجيهات")
                st.write(GUIDANCE[prediction])

                # عرض درجات الأصناف إن كان النموذج يدعمها
                if hasattr(model, "predict_proba"):
                    probabilities = model.predict_proba(
                        [message_text]
                    )[0]

                    classes = list(model.classes_)
                    scores = {
                        str(label): float(score)
                        for label, score in zip(classes, probabilities)
                    }

                    st.subheader("درجات الأصناف")

                    for label in LABELS:
                        st.write(
                            f"**{label}:** {scores[label] * 100:.1f}%"
                        )
                        st.progress(
                            max(0.0, min(1.0, scores[label]))
                        )

                    st.caption(
                        "هذه درجات النموذج وليست احتمالات مؤكدة "
                        "لخطورة الرسالة."
                    )

                st.caption(
                    "قد يخطئ النموذج. عند الشك، تحققي من المرسل "
                    "عبر قناة رسمية مستقلة."
                )

        except Exception:
            st.error(
                "تعذر تحليل الرسالة. تحققي من توافق النموذج "
                "المحفوظ مع الواجهة."
            )
