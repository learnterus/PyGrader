# PyGrader
**Automated Python Code Grading System with Randomized Problems**

PyGrading adalah platform web berbasis Flask yang dirancang untuk mengotomatisasi proses ujian pemrograman Python. Sistem ini membantu pengajar mengelola bank soal, mendistribusikan soal secara acak kepada mahasiswa untuk mencegah kecurangan, dan memberikan penilaian instan berdasarkan output serta kualitas kode.



## Fitur Utama
- **Randomized Problem Sets**: Setiap mahasiswa mendapatkan soal yang berbeda secara acak dari Bank Soal saat pertama kali login.
- **Automated Execution**: Menjalankan kode mahasiswa secara aman menggunakan `subprocess` dengan batasan waktu (*timeout*) untuk menghindari *infinite loop*.
- **Flexible Grading**: Mendukung penilaian berbasis *exact match* atau *case-insensitive* (mengabaikan huruf besar/kecil).
- **Static Code Quality Check**: Mampu memeriksa keberadaan kata kunci tertentu (seperti `while`, `def`, atau `input`) untuk memastikan mahasiswa mengikuti instruksi logika yang benar.
- **Lecturer Dashboard**: Panel khusus dosen untuk manajemen soal, melihat rekapitulasi nilai secara real-time, dan fitur ekspor nilai ke Excel.
- **Modern UI**: Antarmuka bersih dan responsif menggunakan Bootstrap 5.

## Teknologi yang Digunakan
- **Backend**: Python 3, Flask
- **Database**: SQLite (File-based)
- **ORM**: Flask-SQLAlchemy
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Reporting**: Pandas & Openpyxl

## 📂 Struktur Proyek
```text
├── app.py              # Backend logic & API Routes
├── instance/           # Folder database SQLite (ujian.db)
├── submissions/        # Folder penyimpanan file kiriman mahasiswa
├── Tampilan/           # Template HTML (Frontend)
│   ├── login.html
│   ├── dashboard.html
│   ├── rekap_dosen.html
│   └── tambah_soal.html
└── README.md

