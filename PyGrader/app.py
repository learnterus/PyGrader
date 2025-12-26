from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import subprocess
import os
import pandas as pd
from flask import send_file
import io
import random

app = Flask(__name__, template_folder='Tampilan')
app.secret_key = 'kunci_rahasia_anda' # Dibutuhkan untuk fitur 'flash' pesan error

# --- KONFIGURASI DATABASE ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ujian.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODEL DATABASE ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nim = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nim = db.Column(db.String(10), nullable=False)
    skor = db.Column(db.Integer)
    status = db.Column(db.String(20))
    nama_file = db.Column(db.String(100))
    id_soal = db.Column(db.Integer)
    
class Soal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(100))
    deskripsi = db.Column(db.Text)
    input_test = db.Column(db.Text) # Input simulasi (stdin)
    output_test = db.Column(db.Text) # Kunci jawaban (stdout)
    kriteria = db.Column(db.String(50)) # Misal: 'exact_match' atau 'contain'
    req_kode = db.Column(db.String(200)) # Contoh isi: "while,def,list"
    forbidden_kode = db.Column(db.String(200)) # Contoh isi: "import"

# Buat database secara otomatis
with app.app_context():
    db.create_all()

UPLOAD_FOLDER = 'submissions'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- LOGIKA PENILAI ---
def grade_code(file_path, soal_obj):
    try:

        def is_safe_code(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Daftar kata kunci yang dilarang
            forbidden = ['os.', 'subprocess.', 'shutil.', 'eval(', 'exec(', 'open(', 'socket']
            
            for word in forbidden:
                if word in content:
                    return False, word
            return True, None
        
        process = subprocess.run(
            ['python', file_path],
            input=soal_obj.input_test,
            capture_output=True, text=True, timeout=2
        )
        
        actual_output = process.stdout[:1000].strip()
        expected_output = soal_obj.output_test.strip()

        # Cek kriteria yang dipilih dosen
        if soal_obj.kriteria == 'lower_case_match':
            is_correct = actual_output.lower() == expected_output.lower()
        else: # exact match
            is_correct = actual_output == expected_output

        if is_correct:
            return "Passed", 100
        return "Wrong Answer", 0
    except Exception as e:
        return f"Error: {str(e)}", 0
    
def check_code_quality(file_path, soal_obj):
    with open(file_path, 'r') as f:
        content = f.read()

    errors = []
    
  
    if soal_obj.req_kode:
        requirements = soal_obj.req_kode.split(',')
        for req in requirements:
            if req.strip() not in content:
                errors.append(f"Kode harus mengandung: '{req}'")

    if soal_obj.forbidden_kode:
        forbid = soal_obj.forbidden_kode.split(',')
        for fbd in forbid:
            if fbd.strip() in content:
                errors.append(f"Kode dilarang mengandung: '{fbd}'")

    return errors

# --- ROUTES ---

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login_process', methods=['POST'])
def login_process():
    nim_input = request.form.get('nim')
    password_input = request.form.get('password')

    user = User.query.filter_by(nim=nim_input).first()

    if user and user.password == password_input:
        session['nim'] = nim_input
        # LOGIKA ACAK SOAL PINDAH KE SINI (Sebelum Redirect)
        existing_sub = Submission.query.filter_by(nim=nim_input).first()
        if not existing_sub:
            semua_soal = Soal.query.all()
            if semua_soal: # Pastikan ada soal di bank soal agar tidak error
                soal_terpilih = random.choice(semua_soal)
                tugas_baru = Submission(nim=nim_input, skor=0, status="Pending", id_soal=soal_terpilih.id)
                db.session.add(tugas_baru)
                db.session.commit()
        
        return redirect(url_for('dashboard', nim=nim_input))
    else:
        flash("NIM tidak terdaftar atau Password salah!")
        return redirect(url_for('login_page'))
    
@app.route('/dashboard/<nim>')
def dashboard(nim):
    if session.get('nim') != nim:
        return "Akses Ditolak: Anda tidak berwenang melihat dashboard ini."
    # 1. Cari data submission mahasiswa
    sub_info = Submission.query.filter_by(nim=nim).first()
    
    # 2. Ambil detail soal dari tabel Soal
    detail_soal = None
    if sub_info:
        detail_soal = Soal.query.get(sub_info.id_soal)
    
    # 3. Ambil riwayat pengumpulan 
    riwayat_mhs = Submission.query.filter_by(nim=nim).all()
    
    return render_template('dashboard.html', 
                           nim=nim, 
                           soal=detail_soal, 
                           riwayat=riwayat_mhs)

@app.route('/dosen/login', methods=['GET', 'POST'])
def login_dosen():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Hardcoded: Ganti ini dengan username & pass dosen yang kamu mau
        if username == 'admin_dosen' and password == 'alpro':
            session['user_role'] = 'dosen' # Simpan status login di session
            return redirect(url_for('rekap_dosen'))
        else:
            flash("Login Dosen Gagal!")
            
    return render_template('login_dosen.html')

# Route untuk melihat semua hasil ujian (Dashboard Dosen)
@app.route('/dosen/rekap')
def rekap_dosen():
    
    if session.get('user_role') != 'dosen':
        flash("Anda harus login sebagai dosen untuk mengakses halaman ini!")
        return redirect(url_for('login_dosen'))
    
    # Mengambil semua data dari tabel Submission di database
    semua_hasil = Submission.query.all()
    return render_template('rekap_dosen.html', data_nilai=semua_hasil)

@app.route('/dosen/ekspor')
def ekspor_excel():
   
    query = Submission.query.all()
    
    
    data = []
    for h in query:
        data.append({
            "NIM": h.nim,
            "Status": h.status,
            "Skor": h.skor,
            "Nama File": h.nama_file
        })
    
   
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Nilai Ujian')
    
    output.seek(0)
    
    return send_file(output, 
                     download_name="rekap_nilai_alpro.xlsx", 
                     as_attachment=True)

@app.route('/dosen/tambah_soal', methods=['GET', 'POST'])
def tambah_soal():
    if request.method == 'POST':
        # Ambil data dari form HTML
        judul = request.form.get('judul')
        deskripsi = request.form.get('deskripsi')
        input_test = request.form.get('input_test')
        output_test = request.form.get('output_test')
        kriteria = request.form.get('kriteria')

        # Simpan ke database
        soal_baru = Soal(
            judul=judul, 
            deskripsi=deskripsi, 
            input_test=input_test, 
            output_test=output_test, 
            kriteria=kriteria
        )
        db.session.add(soal_baru)
        db.session.commit()

        flash("Soal berhasil ditambahkan ke Bank Soal!")
        return redirect(url_for('rekap_dosen')) 

  
    return render_template('tambah_soal.html')

@app.route('/submit/<nim>', methods=['POST'])
def submit_code(nim):
    if not (len(nim) == 10 and nim.startswith('5049')):
        return "Akses Ilegal: Format NIM salah!"

    if 'file_tugas' not in request.files:
        return "File tidak ditemukan"
    
    file = request.files['file_tugas']
    
    if not file.filename.lower().endswith('.py'):
        flash("Hanya file .py yang diperbolehkan!") # Kirim pesan ke dashboard
        return redirect(url_for('dashboard', nim=nim))
    
    filename = f"{nim}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # AMBIL SOAL MAHASISWA DARI DB
    sub_info = Submission.query.filter_by(nim=nim).first()
    soal_obj = Soal.query.get(sub_info.id_soal)

    # 1. Cek Output (Dynamic Testing)
    status_output, skor_output = grade_code(file_path, soal_obj)

    # 2. Cek Kualitas Kode (Static Testing)
    kode_errors = check_code_quality(file_path, soal_obj)

    # 3. Logika Gabungan
    final_score = skor_output
    if kode_errors:
        final_score -= 20  # Potong nilai jika syarat kode tidak terpenuhi
        status_output = f"Passed with Notes: {', '.join(kode_errors)}"
    
    if final_score < 0: final_score = 0

    # Simpan ke DB
    sub_info.skor = final_score
    sub_info.status = status_output
    db.session.commit()
    
    return redirect(url_for('dashboard', nim=nim))

@app.route('/logout')
def logout():
    session.clear() # Hapus semua data login
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)