# SIHKA BBWS Citanduy: Product Backlog

## Vision

To Create web app that to accomdate **storing long term time series hidrological data**, **telemetri** as well as **manual measurement**.

Start from **seed** 🌱 and **grow forever** 🌳.

## Product Backlog 📦

### 2507-02 EWS Reply, play start from selected date, menampilkan data berjalan per jam per 2 detik, tampilkan hujan dan TMA pada waktu tersebut

### 2506-02 Trouble Ticket: Note -> **Log Book**, threaded, add 'closed' column, default False

### 2507-03 Fasilitas Download per pos, rentang waktu sebulan, pilih pos, pilih bulan

### 2507-01 Disaster Event, record disaster (luapan air sungai), alias Kejadian Bencana

### 2506-01 EWS (Early Warning System), MAP with realtime (5-10 minutes delay) on Hard Rain or Siaga Sungai



## Sprint

### Sprint 2506-01: EWS (Early Warning System), MAP with realtime (5-10 minutes delay) on Hard Rain or Siaga Sungai
- [x] Membuat url ```/ews```, tampilkan peta
- [x] Peta menampilkan batas wilayah sungai Citanduy
- [x] Siapkan data lokasi Pos Hidrologi
- [x] Script yang jalan setiap 5 menit untuk ```fetch``` data hujan dan TMA terbaru

## How to Run this

  1. Create Python Virtual Environtment
  ```bash
  $ python -m venv .venv
  ```
  2. Activate virtual env and install library requirements
  ```bash
  $ .venv/bin/activate
  $ pip install -r requirements.txt
  ```
  3. copy ```.env.example``` to ```.env``` dan edit sesuai konfigurasi lokal
  4. Jalankan flask development server: ```$ flask run --debug -p 3000```