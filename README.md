# kelonvoice

Aplikasi desktop untuk membangun bank kata audio dari sumber suara seseorang, lalu menyusun kalimat baru dengan menyambung potongan-potongan audio kata tersebut.

## Fitur

- `Profiles` untuk memisahkan bank kata per suara.
- `Build` untuk mengekstrak kata dari YouTube atau file lokal.
- `Word Bank` untuk menelusuri, mencari, dan memutar klip kata.
- `Compose` untuk menyusun kalimat dari kata yang sudah tersimpan.

## Menjalankan

```bash
pip install -r requirements.txt
python main.py
```

## Kebutuhan

- Python 3.10+
- FFmpeg tersedia di `PATH`
- Windows, macOS, atau Linux

## Struktur Data

```text
data/
  kelonvoice.db
  profiles/
    <profile-id>/
      source_raw.mp3
      source_raw.wav
      words/
        word_0.wav
```

## Catatan

- Data hasil proses disimpan di folder `data/`.
- Model Whisper dan aset bantu lain bisa diletakkan di `vendor/`.
