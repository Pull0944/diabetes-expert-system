# app.py
import numpy as np
import gradio as gr

# ---- membership ----
def mf_high_glucose(x):
    if x <= 120: return 0.0
    if x >= 200: return 1.0
    return (x - 120) / 80

def mf_mod_glucose(x):
    if x <= 100 or x >= 170: return 0.0
    if x <= 135: return (x - 100) / 35
    return (170 - x) / 35

def mf_high_bp(x):
    if x <= 80: return 0.0
    if x >= 100: return 1.0
    return (x - 80) / 20

def mf_high_bmi(x):
    if x <= 25: return 0.0
    if x >= 35: return 1.0
    return (x - 25) / 10

def mf_mod_bmi(x):
    if x <= 22 or x >= 31: return 0.0
    if x <= 26.5: return (x - 22) / 4.5
    return (31 - x) / 4.5

def mf_high_age(x):
    if x <= 35: return 0.0
    if x >= 60: return 1.0
    return (x - 35) / 25

def mf_high_skin(x):
    if x <= 20: return 0.0
    if x >= 45: return 1.0
    return (x - 20) / 25

def mf_high_insulin(x):
    if x <= 90: return 0.0
    if x >= 200: return 1.0
    return (x - 90) / 110

def mf_high_dpf(x):
    if x <= 0.4: return 0.0
    if x >= 1.2: return 1.0
    return (x - 0.4) / 0.8

def mf_many_preg(x):
    if x <= 2: return 0.0
    if x >= 8: return 1.0
    return (x - 2) / 6

BASE_RULES = [
    ("R1", [("g_high", mf_high_glucose), ("bmi_high", mf_high_bmi)], "Diabetes", 0.85),
    ("R2", [("g_high", mf_high_glucose), ("age_high", mf_high_age)], "Diabetes", 0.75),
    ("R3", [("g_high", mf_high_glucose), ("ins_high", mf_high_insulin)], "Diabetes", 0.80),
    ("R4", [("bmi_high", mf_high_bmi), ("dpf_high", mf_high_dpf)], "Diabetes", 0.70),
    ("R5", [("g_high", mf_high_glucose), ("bp_high", mf_high_bp)], "Diabetes", 0.60),
    ("R6", [("g_mod", mf_mod_glucose), ("bmi_mod", mf_mod_bmi)], "Pre-diabetes", 0.65),
    ("R7", [("age_high", mf_high_age), ("dpf_high", mf_high_dpf)], "Pre-diabetes", 0.55),
    ("R8", [("g_high", lambda x: 1 - mf_high_glucose(x)),
            ("bmi_high", lambda x: 1 - mf_high_bmi(x))], "Normal", 0.60),
]
PREG_RULES = [
    ("R9",  [("g_mod", mf_mod_glucose), ("preg_many", mf_many_preg)], "Pre-diabetes", 0.60),
    ("R10", [("g_high", mf_high_glucose), ("preg_many", mf_many_preg)], "Diabetes",     0.70),
]

def cf_combine_positive(cf_old, cf_new):
    return cf_old + cf_new * (1 - cf_old)

def infer(inputs):
    gender = inputs["Gender"]
    rules = BASE_RULES + (PREG_RULES if gender == "Perempuan" else [])
    conclusions = {"Diabetes":0.0, "Pre-diabetes":0.0, "Normal":0.0}
    active = []

    def get_val(fact):
        mapping = {
            'g_high':'Glucose','g_mod':'Glucose','bp_high':'BloodPressure',
            'bmi_high':'BMI','bmi_mod':'BMI','age_high':'Age',
            'skin_high':'SkinThickness','ins_high':'Insulin','dpf_high':'DiabetesPedigreeFunction',
            'preg_many':'Pregnancies'
        }
        return inputs[mapping[fact]]

    for rid, premises, concl, cf_rule in rules:
        mu_vals = []
        for fact_name, mf in premises:
            if fact_name == "preg_many" and gender != "Perempuan":
                mu_vals.append(0.0)
            else:
                mu_vals.append(float(np.clip(mf(get_val(fact_name)), 0.0, 1.0)))
        mu = min(mu_vals) if mu_vals else 0.0
        if mu > 0:
            cf_inst = cf_rule * mu
            conclusions[concl] = cf_combine_positive(conclusions[concl], cf_inst)
            active.append((rid, premises, concl, mu, cf_inst))
    return conclusions, active

RISK_EXPLANATIONS = {
    'Glucose': ('Glukosa darah', 'Kadar glukosa tinggi mengindikasikan gangguan regulasi gula darah.'),
    'BMI': ('Indeks massa tubuh', 'BMI tinggi berkaitan dengan resistensi insulin.'),
    'BloodPressure': ('Tekanan darah', 'Hipertensi sering menyertai sindrom metabolik.'),
    'Age': ('Usia', 'Risiko meningkat seiring bertambahnya usia.'),
    'Insulin': ('Insulin', 'Hiperinsulinemia merupakan tanda resistensi insulin.'),
    'DiabetesPedigreeFunction': ('Riwayat keluarga (DPF)', 'Menunjukkan kecenderungan genetik terhadap diabetes.'),
    'SkinThickness': ('Ketebalan kulit', 'Indikasi komposisi lemak subkutan.'),
    'Pregnancies': ('Jumlah kehamilan', 'Kehamilan berulang meningkatkan risiko gestasional.'),
}

CSS = """
:root{ --bg:#f5f8fb; --card:#ffffff; --accent:#1060df; --ink:#2b3a4a; --muted:#667b8f; }
body{background:linear-gradient(180deg,#f7fbff,#eef5ff); color:var(--ink);}
.gradio-container{font-family: Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto;}
.card{background:var(--card); border:1px solid #e9eef5; border-radius:14px; box-shadow:0 8px 20px rgba(16,96,223,.06); padding:18px}
.btn-primary{background:linear-gradient(90deg,#3b82f6,#2563eb); color:white; border-radius:12px; padding:11px 16px; font-weight:600}
.small{font-size:0.92em; color:var(--muted)}
.kv{display:flex; justify-content:space-between; gap:12px; font-weight:600}
.meter-wrap{margin-top:8px; background:#eff6ff; border:1px solid #deebff; border-radius:10px; height:14px; overflow:hidden}
.meter{height:100%; width:10%; background:linear-gradient(90deg,#6be56b,#ffd66b,#ff6b6b); transition:width .9s cubic-bezier(.2,.9,.3,1)}
.grid{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px}
.item{background:white; border:1px solid #e9eef5; border-radius:12px; padding:12px}
.item-head{display:flex; gap:10px; align-items:center}
.iconbox{width:48px;height:48px;border-radius:10px;background:linear-gradient(135deg,#fff,#f7fbff);display:flex;align-items:center;justify-content:center;border:1px solid #e9eef5}
.badge{margin-left:auto; font-weight:700}
.badge.low{color:#1f9d55}
.badge.mid{color:#b7791f}
.badge.hi{color:#e02424}
"""

def risk_meter_block(concl):
    score = concl['Diabetes']*1.0 + concl['Pre-diabetes']*0.6
    pct = int(min(1.0, score)*100)
    return f"""
    <div class="card">
      <div style="display:flex;align-items:center;gap:12px">
        <div class="iconbox">🩺</div>
        <div>
          <div style="font-weight:700;color:var(--accent)">Ringkasan Risiko</div>
          <div class="small">Diabetes {concl['Diabetes']:.2f} • Pre-diabetes {concl['Pre-diabetes']:.2f} • Normal {concl['Normal']:.2f}</div>
        </div>
      </div>
      <div style="margin-top:12px">
        <div class="kv"><div>Indeks Risiko Keseluruhan</div><div>{pct}%</div></div>
        <div class="meter-wrap"><div class="meter" style="width:{pct}%"></div></div>
      </div>
    </div>
    """

def factors_grid(inputs, gender):
    factors = [
        ('Glucose','Glukosa (mg/dL)', inputs['Glucose']),
        ('BMI','BMI', inputs['BMI']),
        ('BloodPressure','Tekanan Darah Diastolik (mmHg)', inputs['BloodPressure']),
        ('Age','Usia (tahun)', inputs['Age']),
        ('Insulin','Insulin (pmol/L)', inputs['Insulin']),
        ('DiabetesPedigreeFunction','DPF', inputs['DiabetesPedigreeFunction']),
        ('SkinThickness','Skin Thickness (mm)', inputs['SkinThickness']),
    ]
    if gender == "Perempuan":
        factors.append(('Pregnancies','Jumlah Kehamilan', inputs['Pregnancies']))

    def sev(key, val):
        if key == 'Glucose': m = mf_high_glucose(val)
        elif key == 'BMI': m = mf_high_bmi(val)
        elif key == 'BloodPressure': m = mf_high_bp(val)
        elif key == 'Age': m = mf_high_age(val)
        elif key == 'Insulin': m = mf_high_insulin(val)
        elif key == 'DiabetesPedigreeFunction': m = mf_high_dpf(val)
        elif key == 'SkinThickness': m = mf_high_skin(val)
        elif key == 'Pregnancies': m = mf_many_preg(val)
        else: m = 0
        label = 'Rendah' if m < 0.33 else ('Sedang' if m < 0.66 else 'Tinggi')
        cls = 'low' if label=='Rendah' else ('mid' if label=='Sedang' else 'hi')
        return label, cls

    cards = '<div class="grid" style="margin-top:12px">'
    for key, label, val in factors:
        title, expl = RISK_EXPLANATIONS.get(key, (label, ''))
        lab, cls = sev(key, val)
        cards += f"""
        <div class="item">
          <div class="item-head">
            <div class="iconbox">🔎</div>
            <div>
              <div style="font-weight:700">{title}</div>
              <div class="small">{label}: {val}</div>
            </div>
            <div class="badge {cls}">{lab}</div>
          </div>
          <div style="margin-top:8px;color:#566b7e">{expl}</div>
        </div>
        """
    cards += '</div>'
    return cards

def rule_trace(active):
    if not active:
        return "<div class='small'>Tidak ada aturan yang aktif—parameter berada pada rentang rendah.</div>"
    html = "<div class='card'>"
    html += "<div style='font-weight:700;color:var(--accent)'>Jejak Aturan</div>"
    for rid, premises, concl_name, mu, cf_inst in active:
        prem_names = ', '.join([p[0] for p in premises])
        html += f"<div style='padding:8px 0;border-bottom:1px dashed #e9eef5'><b>{rid}</b> • IF {prem_names} THEN <i>{concl_name}</i> — μ={mu:.2f}, CF={cf_inst:.2f}</div>"
    html += "</div>"
    return html

def diagnose(Gender, Pregnancies, Glucose, BloodPressure, SkinThickness,
             Insulin, BMI, DiabetesPedigreeFunction, Age):
    if Gender == "Laki-laki":
        Pregnancies = 0

    inputs = {
        'Gender': Gender,
        'Pregnancies': Pregnancies,
        'Glucose': Glucose,
        'BloodPressure': BloodPressure,
        'SkinThickness': SkinThickness,
        'Insulin': Insulin,
        'BMI': BMI,
        'DiabetesPedigreeFunction': DiabetesPedigreeFunction,
        'Age': Age,
    }
    concl, active = infer(inputs)

    header = risk_meter_block(concl)
    fgrid = factors_grid(inputs, Gender)
    rules = rule_trace(active)

    best = max(concl, key=concl.get)
    best_cf = concl[best]
    if best == 'Diabetes' and best_cf >= 0.50:
        tips = ("⚠ Indikasi risiko tinggi. Disarankan segera berkonsultasi dengan tenaga kesehatan "
                "untuk pemeriksaan lanjutan (mis. HbA1c, pemeriksaan laboratorium komprehensif).")
    elif best == 'Pre-diabetes':
        tips = ("ℹ Terdapat indikasi pra-diabetes. Pertimbangkan pengaturan pola makan, aktivitas fisik terukur, "
                "dan pemantauan glukosa berkala sesuai arahan tenaga kesehatan.")
    else:
        tips = ("✅ Parameter saat ini relatif dalam batas wajar. Pertahankan gaya hidup sehat "
                "dan lakukan pemeriksaan rutin sesuai kebutuhan.")

    detail = f"""
      {header}
      <div style="height:12px"></div>
      {fgrid}
      <div style="height:12px"></div>
      {rules}
      <div class="card" style="margin-top:12px;font-weight:600">{tips}</div>
    """

    text_summary = (
        f"Hasil: {best} (Keyakinan {best_cf:.2f}). "
        f"Diabetes={concl['Diabetes']:.2f} | Pre-diabetes={concl['Pre-diabetes']:.2f} | Normal={concl['Normal']:.2f}. "
        f"Saran: {tips}"
    )
    return detail, text_summary

with gr.Blocks(css=CSS) as demo:
    gr.Markdown("## Sistem Pakar Risiko Diabetes")
    gr.Markdown("<div class='small'>Alat bantu skrining berbasis aturan (Certainty Factor). Bukan pengganti diagnosis.</div>")

    with gr.Row():
        with gr.Column():
            gender = gr.Radio(choices=["Laki-laki","Perempuan"], value="Laki-laki", label="Jenis Kelamin")
            pregnancies = gr.Slider(0, 9, 0, step=1, label="Jumlah Kehamilan (aktif saat Perempuan)", interactive=False)
        with gr.Column():
            glucose = gr.Number(value=0, label='Glukosa (mg/dL)')
            bp = gr.Number(value=0, label='Tekanan Darah Diastolik (mmHg)')
            skin = gr.Number(value=0, label='Skin Thickness (mm)')
        with gr.Column():
            insulin = gr.Number(value=0, label='Insulin (pmol/L)')
            bmi = gr.Number(value=0, label='BMI')
            dpf = gr.Number(value=0, label='Diabetes Pedigree Function')
            age = gr.Number(value=0, label='Usia (tahun)')

    def toggle_preg(g, current):
        if g == "Laki-laki":
            return gr.update(value=0, interactive=False, label="Jumlah Kehamilan (non-aktif untuk Laki-laki)")
        return gr.update(interactive=True, label="Jumlah Kehamilan (aktif untuk Perempuan)")

    gender.change(fn=toggle_preg, inputs=[gender, pregnancies], outputs=pregnancies)

    btn = gr.Button('Analisis Sekarang', elem_classes='btn-primary')
    result_html = gr.HTML(label='Hasil & Penjelasan')
    export_text = gr.Textbox(label='Ringkasan Teks', lines=4)

    btn.click(
        fn=diagnose,
        inputs=[gender, pregnancies, glucose, bp, skin, insulin, bmi, dpf, age],
        outputs=[result_html, export_text]
    )

if __name__ == "__main__":
    demo.launch()
