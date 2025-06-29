from ultralytics import YOLO
from PIL import Image
from torchvision import transforms
import numpy as np
import os
from fpdf import FPDF
# تحويل الصور لتناسب مدخلات النموذج
transform = transforms.Compose([
    transforms.Resize((640, 640)),  # تغيير حجم الصورة لتناسب مدخلات YOLO
    transforms.ToTensor(),  # تحويل الصورة إلى Tensor
])

# تحميل النموذج
def load_model():
    model = YOLO('models/best.pt')  # تحميل الأوزان من ملف best.pt
    return model
def generate_report(image_path):
    # التحقق إذا كانت الصورة موجودة
    if not os.path.exists(image_path):
        return f"File not found: {image_path}"

    # تحميل الصورة من المسار
    image = Image.open(image_path)
    image_tensor = transform(image).unsqueeze(0)  # إضافة بعد إضافي لتناسب المدخلات بالنموذج

    # تحميل النموذج
    model = load_model()

    # إجراء التنبؤ باستخدام النموذج
    results = model(image_tensor)

    # الحصول على الصورة المتعقبة
    tracked_image = results[0].plot()
    tracked_image_pil = Image.fromarray(tracked_image)

    # 🟢 استخراج اسم الصورة الأصلية (بدون المسار الكامل)
    filename = os.path.basename(image_path)  # مثال: original.jpg
    name_without_ext = os.path.splitext(filename)[0]  # مثال: original

    # 🟢 تحديد مسار حفظ الصورة الناتجة بنفس الاسم
    output_image_name = f"{name_without_ext}_tracked.jpg"
    output_image_path = os.path.join("static/outputs", output_image_name)
    tracked_image_pil.save(output_image_path)

    # 📝 إعداد التقرير
    report = f"The tracked image has been saved at {output_image_path}"
    
    # 🔁 إرجاع المسار الصحيح للصورة الأصلية (علشان تعرضها في report.html)
    original_image_path = image_path.replace("static/", "")  # علشان تستخدمه في url_for

    # إنشاء ملف PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    #pdf.cell(200, 10, txt="Image Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 10, report)

    pdf_bytes = pdf.output(dest='S').encode('latin1')

    return report, pdf_bytes, original_image_path, output_image_path.replace("static/", "")


   
