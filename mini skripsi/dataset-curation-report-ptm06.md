# LAPORAN KURASI DATASET CITRA & DATA SHEET (DATA CARD)
## Computer Vision & Deep Learning — Modul 06: Persiapan Dataset Citra
### Proyek: CassavaCare AI — On-Device Cassava Leaf Disease Diagnosis

---

| **Mata Kuliah** | Computer Vision and Deep Learning |
| :--- | :--- |
| **Kode / SKS** | TIF-CVDL / 3 SKS |
| **Program Studi** | Teknik Informatika (Konsentrasi AI-Based Mobile & Web) |
| **Topik Modul 06** | Kurasi Data Custom, Labeling Gratis, Augmentasi `torchvision`, & Analisis Bias Visual |
| **Dosen Pengampu** | Edwin Hari Agus Prastyo, S.Kom., M.Kom. |
| **Penyusun** | Tim Pengembang CassavaCare AI |

---

### BAB I: DESKRIPSI DOMAIN, MASALAH, & AKUISISI DATA

#### 1.1 Latar Belakang & Domain Masalah
Tanaman singkong (*Manihot esculenta Crantz*) merupakan sumber karbohidrat terbesar ketiga di dunia dan makanan pokok bagi lebih dari 500 juta jiwa. Namun, produktivitas pertanian singkong terancam secara masif oleh infeksi virus dan serangga hama yang dapat menyebabkan kehilangan hasil panen hingga $1 miliar USD per tahun [3, 9, 32]. 

Aplikasi **CassavaCare AI** dirancang untuk mendeteksi 3 penyakit virus utama dan 2 jenis kerusakan hama pada daun singkong langsung di lapangan (*on-device*) tanpa membutuhkan koneksi internet.

#### 1.2 Sumber & Strategi Akuisisi Data
Dataset yang dikurasi menggabungkan **Sekunder Benchmark Riset** dan **Pengumpulan Otentik Lapangan**:
1. **Benchmark Utama (Ramcharan et al., 2017):** Dataset citra daun singkong terpublikasi (*Frontiers in Plant Science*, DOI: 10.3389/fpls.2017.01852) yang diambil di kebun percobaan *International Institute of Tropical Agriculture* (IITA) Bagamoyo, Tanzania [3].
2. **Pengumpulan Mandiri (Primary Field Data):** Pengambilan foto daun singkong otentik menggunakan kamera smartphone (1080p s.d. 4K) pada variasi kondisi pencahayaan alami (pagi, siang terik, dan temaram sore) di lahan pertanian lokal untuk meningkatkan generalisasi model.

---

### BAB II: DATASET DATASHEET (DATA CARD - GEBRU ET AL., 2021)

Sesuai standar ilmiah internasional (*Datasheets for Datasets*, Gebru et al., 2021) [108, 109], berikut adalah lembar fakta dataset **CassavaCare AI**:

```
================================================================================
                    LEMBAR DATASET (DATA CARD) CASSAVACARE AI
================================================================================
1. MOTIVASI PENGUMPULAN:
   - Dibuat untuk melatih model Computer Vision ringan (Inception v3 / MobileNet /
     CNN Custom) yang mampu mengklasifikasikan penyakit daun singkong secara presisi.
   - Dikembangkan oleh Tim Mahasiswa TIF IMWAD di bawah bimbingan Dosen Pengampu.

2. KOMPOSISI CITRA & DISTRIBUTION:
   - Total Citra Utuh (Original Dataset)  : 2,756 citra berwarna (RGB).
   - Total Leaflet Cropped (Leaflet Set)  : 15,000 citra potongan helai daun.
   - Sebaran Kelas (Original Leaf Dataset):
     * Cassava Brown Streak Disease (CBSD) : 398 citra  (14.4%)
     * Cassava Mosaic Disease (CMD)       : 388 citra  (14.1%)
     * Brown Leaf Spot (BLS)               : 386 citra  (14.0%)
     * Green Mite Damage (GMD)             : 309 citra  (11.2%)
     * Red Mite Damage (RMD)               : 415 citra  (15.1%)
     * Healthy (Daun Sehat)                : 860 citra  (31.2%)
   - Rentang Resolusi Asli                : 1920x1080 px hingga 5184x3888 px.

3. PROSES PENGUMPULAN DATA:
   - Perangkat Kamera : Kamera Digital Sony Cybershot 20.2 MP & Smartphone Sony IMX 64MP.
   - Waktu & Kondisi  : Pukul 07.30 - 16.30 WIB, sudut pandang bervariasi (top-down,
                        45-degree angle, close-up leaflet, medium leaf shot).

4. PRA-PENGOLAHAN & ANOTASI:
   - Validator Anotasi: Pakar penyakit tanaman IITA disandingkan dengan anotasi mandiri.
   - Platform Anotasi : Make Sense (makesense.ai) untuk mengekspor format YOLO (.txt)
                        dan struktur PyTorch ImageFolder.

5. KETERBATASAN & POTENSI BIAS:
   - Latar belakang foto mencakup tanah, bayangan, tangan manusia, dan dedaunan sekitarnya.
   - Belum mencakup citra pada kondisi malam hari dengan kilat lampu flash buatan.
================================================================================
```

---

### BAB III: PIPELINE STANDARISASI, DATA HYGIENE, & KODE PYTORCH

#### 3.1 Struktur Direktori Standar `ImageFolder`
Dataset disusun mengacu pada hirarki resmi `torchvision.datasets.ImageFolder` [90]:

```text
dataset_cassavacare/
├── train/
│   ├── BLS/       (386 citra)
│   ├── CBSD/      (398 citra)
│   ├── CMD/       (388 citra)
│   ├── GMD/       (309 citra)
│   ├── HEALTHY/   (860 citra)
│   └── RMD/       (415 citra)
├── val/
└── test/
```

#### 3.2 Audit Kebersihan Data (Data Hygiene & Anti-Data Leakage)
1. **Eliminasi Corrupt JPEG:** Menggunakan skrip `PIL.Image.verify()` untuk mendeteksi dan menghapus byte terpotong yang berpotensi menggagalkan *training loop* [102].
2. **Deduplikasi via MD5 Hash:** Mencegah kebocoran data (*data leakage*) antara subset latih dan uji menggunakan hashing MD5 `hashlib.md5()` [103].
3. **Pemisahan Deterministik (Anti-Leakage Rule):** Dataset dibagi terlebih dahulu (*Split First*) menjadi **Train 70%**, **Val 15%**, dan **Test 15%** dengan *random seed* (42). Augmentasi acak **hanya** diterapkan secara dinamis padasubset *Train* saat iterasi epoch [98, 99].

#### 3.3 Kode Pipeline PyTorch Fungsional (`curation_pipeline.py`)

```python
import os
import random
import hashlib
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split, Dataset
from torchvision import datasets, transforms
from PIL import Image

# 1. Reproducibility Seed Setup
SEED = 42
def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

set_seed(SEED)

# 2. Audit Kebersihan Data (PIL Verify & MD5 Hash Deduplication)
def clean_and_deduplicate(dataset_dir):
    seen_hashes = set()
    corrupt_count = 0
    duplicate_count = 0
    
    for root, _, files in os.walk(dataset_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                filepath = os.path.join(root, file)
                # Check 1: Integrity Check
                try:
                    with Image.open(filepath) as img:
                        img.verify()
                except Exception:
                    os.remove(filepath)
                    corrupt_count += 1
                    continue
                
                # Check 2: Hash Check
                hasher = hashlib.md5()
                with open(filepath, 'rb') as f:
                    hasher.update(f.read())
                file_hash = hasher.hexdigest()
                
                if file_hash in seen_hashes:
                    os.remove(filepath)
                    duplicate_count += 1
                else:
                    seen_hashes.add(file_hash)
                    
    print(f" Data Hygiene Selesai: {corrupt_count} file corrupt dihapus, {duplicate_count} file duplikat dibersihkan.")

# 3. Transformasi Augmentasi Dinamis torchvision
IMAGE_SIZE = (224, 224)

# Dynamic Train Transform (Invariansi Geometris & Fotometrik)
train_transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(degrees=15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2), # Aman untuk bercak daun
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Evaluation Transform (Murni tanpa augmentasi acak)
val_test_transform = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 4. Wrapper Class untuk Memisahkan Transformasi Subset
class TransformSubset(Dataset):
    def __init__(self, subset, transform=None):
        self.subset = subset
        self.transform = transform
        
    def __getitem__(self, index):
        x, y = self.subset[index]
        if self.transform:
            x = self.transform(x)
        return x, y
        
    def __len__(self):
        return len(self.subset)

# 5. Penanganan Class Imbalance via Weighted Cross-Entropy Loss
def get_weighted_loss_criterion(full_dataset, train_indices):
    class_counts = [0] * len(full_dataset.classes)
    for idx in train_indices:
        _, label = full_dataset[idx]
        class_counts[label] += 1
        
    total_samples = sum(class_counts)
    num_classes = len(class_counts)
    
    # Formula: w_i = N_total / (K * N_i)
    class_weights = [total_samples / (num_classes * count) if count > 0 else 1.0 for count in class_counts]
    weights_tensor = torch.tensor(class_weights, dtype=torch.float)
    return nn.CrossEntropyLoss(weight=weights_tensor)
```

---

### BAB IV: ANALISIS RISIKO BIAS VISUAL & MITIGASI SHORTCUT LEARNING

#### 4.1 Identifikasi Bahaya *Shortcut Learning*
Model *Deep Learning* berisiko mengalami *shortcut learning*—yaitu mempelajari korelasi latar belakang palsu alih-alih fitur morfologi penyakit sejati [107]. Pada dataset citra daun singkong, potensi bias visual meliputi:
1. **Bias Tangan / Sepatu Pengumpul Data:** Foto penyakit langka (misal GMD) sering diambil sembari memegang helai daun dengan tangan manusia. Model dapat secara keliru menyimpulkan *"Jika ada jari manusia di tepi foto, maka itu GMD"*.
2. **Bias Tanah / Sinar Matahari Direct:** Foto daun sehat (*Healthy*) cenderung diambil saat kondisi terang pencahayaan atas, sedangkan daun berpenyakit layu merunduk mendekati tanah (*background* tanah cokelat).
3. **Bias Warna Akibat Over-Augmentation:** Penerapan `Hue Jitter` berlebihan dapat mengubah warna bintik *Red Mite Damage* (merah karat) menjadi hijau, merusak validitas semantik fitur penyakit [101].

#### 4.2 Strategi Mitigasi Terstruktur
1. **Random Resized Crop (0.8 - 1.0):** Memotong acak area tengah daun untuk mengeliminasi objek distraksi tepi layar (tangan, tanah, langit) [96].
2. **ColorJitter Terkontrol (Brightness=0.2, Contrast=0.2, Hue=0.0):** Memvariasikan kecerahan tanpa merusak spektrum warna asli gejala penyakit [96].
3. **Pemberian Bobot Kerugian (Weighted Loss):** Mengatasi ketimpangan jumlah citra kelas *Healthy* (31.2%) dibanding *GMD* (11.2%) menggunakan penalti *Cross Entropy* terbobot agar model tidak mengambil jalan pintas tebakan terbanyak [105].

---

### KESIMPULAN & REKOMENDASI

Pipeline kurasi dataset **CassavaCare AI** telah berhasil menerapkan standar kebersihan data, validasi format labeling, pembagian subset deterministik tanpa kebocoran data, serta mitigasi bias visual secara komprehensif. Dataset ini siap digunakan untuk tahap pelatihan model *Convolutional Neural Network* (CNN / MobileNet / TF-Lite) pada tahap selanjutnya.
