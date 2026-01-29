# Absen_siswa_pi

## Menjalankan Sistem Lengkap:
```shell

# 1. Start database
sudo systemctl start mysql

# 2. Start web server (sudah auto start)
sudo systemctl start apache2

# 3. Start scanner API
sudo systemctl start scanner-api

# 4. Start multi-scanner
sudo systemctl start multi-scanner

# 5. Cek semua service
sudo systemctl status mysql apache2 scanner-api multi-scanner
```

