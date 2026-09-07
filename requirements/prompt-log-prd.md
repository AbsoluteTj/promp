# Prompt Log: CassavaCare AI

**Topik:** Problem Framing, User Research, dan Requirement Engineering  
**Dokumen yang Disusun:** PRD dan SRS  

---

## Log Prompt (Chain Prompting)

**Prompt 1: Pembuatan PRD**
```text
[Peran] Kamu adalah product manager senior untuk produk Mobile berfitur AI.
[Tugas] Susun DRAF PRD ringkas untuk "CassavaCare AI" berdasarkan kasus berikut.
[Konteks]
Problem statement: Petani singkong mengalami kerugian panen secara massal akibat keterlambatan identifikasi penyakit daun karena minimnya akses ke pakar botani secara cepat di lapangan.
Target user: Petani Singkong (Persona: Pak Yanto, butuh solusi cepat offline di ladang).
Stakeholder lain: Pakar pertanian, Pengepul hasil panen.
Bukti riset: Model AI Computer Vision terbukti mampu mendeteksi 3 penyakit utama dan 2 jenis hama pada daun singkong langsung dari citra kamera ponsel dengan akurasi 93% (Ramcharan et al., 2017, DOI: 10.3389/fpls.2017.01852).
Platform & stack: Mobile (Android) / Kotlin & TensorFlow Lite.
Fitur AI inti: Computer Vision (Image Classification) secara on-device.
Konstrain: Prototype 1 semester; data & biaya AI terbatas.
[Format output] 1) Ringkasan eksekutif; 2) Problem statement & bukti (fakta vs asumsi); 3) Target user & stakeholder; 4) Value proposition; 5) Tujuan produk & KPI; 6) Scope fitur MoSCoW; 7) Non-goals; 8) Asumsi & risiko + mitigasi.
[Aturan] Hanya gunakan data pada [Konteks]; bila kurang, tulis [ASUMSI-XX]. Bahasa Indonesia baku, format Markdown.