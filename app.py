
import re
from pathlib import Path

import joblib
import streamlit as st

# إعداد الصفحة
st.set_page_config(
    page_title="مرشد الرسائل الآمن",
    page_icon="🛡️",
    layout="centered"
)

# الفئات التي سيكشف عنها النموذج
LABELS = [
    "نص تصيد",
    "طلب وصول غير مصرح به",
    "رابط مشبوه"
]

# حد عرض المؤشر، قابل للتعديل بعد تقييم النموذج
THRESHOLD = 0.50

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
    """استخراج الروابط المكتوبة في الرسالة دون فتحها."""
    pattern = r'(?i)\b(?:https?://|www\.)[^\s<>"\']+'
    return re.findall(pattern, text)


# عنوان التطبيق
st.title("🛡️ مرشد الرسائل الآمن")

st.write(
    "حلّل الرسائل الواردة وتعرّف على مؤشرات التصيّد "
    "ومحاولات الوصول غير المصرح به والروابط المشبوهة."
)

st.info(
    "الصق نص الرسالة كما وصلك. لا تفتح الروابط أثناء التحليل؛ "
    "التطبيق يفحص النص فقط ولا يتحقق من سلامة المواقع فعليًا."
)

# إدخال الرسالة
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

# تحليل الرسالة
if submitted:
    if not message_text.strip():
        st.warning("يرجى لصق الرسالة أولًا.")

    else:
        links = extract_links(message_text)

        st.subheader("نتيجة التحليل")

        if links:
            st.write("**روابط عُثر عليها داخل النص:**")
            for link in links:
                st.code(link, language=None)
            st.caption("تم استخراج الروابط نصيًا دون فتحها.")
        else:
            st.write("لم يُعثر على رابط واضح بالنمط المستخدم.")

        if model is None:
            st.warning(
                "لم يُربط نموذج التصنيف بعد. "
                "احفظ النموذج المدرّب باسم model.joblib "
                "في مستودع المشروع."
            )

        else:
            try:
                # يتطلب هذا الكود نموذج تصنيف متعدد التسميات
                # يعيد درجة مستقلة لكل فئة.
                if not hasattr(model, "predict_proba"):
                    st.error(
                        "النموذج لا يدعم predict_proba. "
                        "يجب إعداد نموذج مناسب لإظهار درجات الفئات."
                    )

                elif not hasattr(model, "classes_"):
                    st.error(
                        "تعذر التحقق من فئات النموذج. "
                        "راجع طريقة تدريبه."
                    )

                else:
                    model_classes = list(model.classes_)

                    if set(model_classes) != set(LABELS):
                        st.error(
                            "فئات النموذج لا تطابق الفئات المعتمدة. "
                            "أعد تدريب النموذج بهذه الفئات: "
                            + "، ".join(LABELS)
                        )

                    else:
                        probabilities = model.predict_proba(
                            [message_text]
                        )

                        # يدعم OneVsRestClassifier متعدد التسميات
                        # الذي يعيد مصفوفة درجات للفئات.
                        if getattr(probabilities, "ndim", 0) != 2:
                            st.error(
                                "شكل نتائج النموذج غير متوافق. "
                                "تحقق من أن النموذج متعدد التسميات."
                            )

                        elif probabilities.shape[1] != len(model_classes):
                            st.error(
                                "عدد درجات النموذج لا يطابق عدد الفئات."
                            )

                        else:
                            scores = {
                                label: float(probabilities[0][index])
                                for index, label in enumerate(model_classes)
                            }

                            highest_score = max(scores.values())
                            suspicious_labels = [
                                label
                                for label, score in scores.items()
                                if score >= THRESHOLD
                            ]

                            st.markdown(
                                '<div class="result-box">',
                                unsafe_allow_html=True
                            )

                            st.metric(
                                "أعلى مؤشر اشتباه تقديري",
                                f"{highest_score * 100:.1f}%"
                            )

                            st.caption(
                                "هذه درجة النموذج وليست احتمالًا مؤكدًا "
                                "لأن الرسالة ضارة."
                            )

                            st.markdown("</div>", unsafe_allow_html=True)

                            st.subheader("مؤشرات الاشتباه")

                            for label in LABELS:
                                score = scores[label]
                                st.write(
                                    f"**{label}** — "
                                    f"{score * 100:.1f}%"
                                )
                                st.progress(
                                    max(0.0, min(1.0, score))
                                )

                            if suspicious_labels:
                                st.warning(
                                    "مؤشرات تستحق الانتباه: "
                                    + "، ".join(suspicious_labels)
                                )
                            else:
                                st.success(
                                    "لم تتجاوز أي فئة حد العرض المحدد. "
                                    "هذا لا يثبت أن الرسالة آمنة."
                                )

                            st.subheader("إرشادات السلامة")

                            if "نص تصيد" in suspicious_labels:
                                st.write(
                                    "- تحقق من هوية المرسل عبر قناة رسمية "
                                    "قبل تنفيذ طلبه."
                                )

                            if "طلب وصول غير مصرح به" in suspicious_labels:
                                st.write(
                                    "- لا تشارك كلمات المرور أو رموز التحقق، "
                                    "ولا تمنح صلاحيات دخول استجابةً لرسالة "
                                    "غير موثوقة."
                                )

                            if "رابط مشبوه" in suspicious_labels:
                                st.write(
                                    "- لا تضغط على الرابط. افتح الموقع الرسمي "
                                    "بكتابة عنوانه بنفسك عند الحاجة."
                                )

                            st.caption(
                                "قد يخطئ النموذج أو يفوته اكتشاف الخطر. "
                                "لم يتم فتح الروابط أو التحقق من محتواها."
                            )

            except Exception:
                st.error(
                    "تعذر تحليل الرسالة. تحقق من توافق النموذج "
                    "المحفوظ مع الكود وبيانات التدريب."
                )
