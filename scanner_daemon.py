#!/usr/bin/env python3
"""
Scanner Daemon yang mengirim ke API
"""

import usb.core
import usb.util
import requests
import json
import time
import sys
from datetime import datetime

class ScannerDaemon:
    def __init__(self):
        self.api_url = "http://192.168.1.11/api/scan"
        self.running = True
        self.device = None
        self.location = "Scanner USB"  # Default location
        
    def setup_scanner(self):
        """Setup USB scanner"""
        print("🔍 Mencari scanner USB...")
        
        # Try common scanner VID/PID
        scanner_ids = [
            (0x9901, 0x301),   # use scanner
            (0x1a86, 0x7523),  # Generic CH340
            (0x0c2e, 0x0b00),  # Datalogic
            (0x05fe, 0x1010),  # Honeywell
            (0x1a40, 0x0101),  # Terminus
        ]
        
        for vid, pid in scanner_ids:
            self.device = usb.core.find(idVendor=vid, idProduct=pid)
            if self.device:
                print(f"✅ Scanner ditemukan: VID={vid:04x}, PID={pid:04x}")
                return True
        
        print("❌ Scanner fisik tidak ditemukan")
        return False
    
    def send_scan(self, nis):
        """Send scan data to API"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        try:
            data = {
                'nis': nis,
                'location': self.location
            }
            
            print(f"[{timestamp}] 📤 Mengirim NIS {nis} ke API...")
            
            response = requests.post(
                self.api_url,
                json=data,
                timeout=5
            )
            
            result = response.json()
            
            if result.get('success'):
                siswa = result.get('student', {})
                print(f"[{timestamp}] ✅ {siswa.get('nama')} ({nis}) - {siswa.get('kelas')}")
            else:
                print(f"[{timestamp}] ❌ {result.get('message')}")
                
        except requests.exceptions.ConnectionError:
            print(f"[{timestamp}] ⚠️  API tidak terhubung. Pastikan scanner-api berjalan!")
        except requests.exceptions.Timeout:
            print(f"[{timestamp}] ⚠️  Timeout menghubungi API")
        except Exception as e:
            print(f"[{timestamp}] ⚠️  Error: {e}")
    
    def read_from_scanner(self):
        """Read data from physical scanner"""
        try:
            if self.device.is_kernel_driver_active(0):
                self.device.detach_kernel_driver(0)
            
            self.device.set_configuration()
            endpoint = self.device[0][(0,0)][0]
            
            buffer = ""
            while self.running:
                try:
                    data = self.device.read(
                        endpoint.bEndpointAddress,
                        endpoint.wMaxPacketSize,
                        timeout=1000
                    )
                    
                    if data:
                        # Decode ASCII characters
                        for byte in data:
                            if 32 <= byte < 127:  # Printable ASCII
                                buffer += chr(byte)
                        
                        # End of scan (Enter key)
                        if '\r' in buffer or '\n' in buffer:
                            barcode = buffer.strip('\r\n')
                            if barcode:
                                return barcode
                            buffer = ""
                            
                except usb.core.USBTimeoutError:
                    continue
                    
        except Exception as e:
            print(f"Error membaca scanner: {e}")
        
        return None
    
    def simulate_scanner(self):
        """Simulate scanner input for testing"""
        print("🎮 Mode simulasi aktif")
        print("Tekan Ctrl+C untuk berhenti")
        print("-" * 50)
        
        test_students = [
            {'nis': '2026001', 'nama': 'Budi Santoso', 'kelas': 'X IPA 1'},
            {'nis': '2026002', 'nama': 'Sari Dewi', 'kelas': 'X IPA 2'},
            {'nis': '2026003', 'nama': 'Agus Wibowo', 'kelas': 'XI IPS 1'},
            {'nis': '2026004', 'nama': 'Rina Melati', 'kelas': 'XI IPA 1'},
            {'nis': '2026005', 'nama': 'Doni Prasetyo', 'kelas': 'XII IPA 1'},
        ]
        
        import random
        
        while self.running:
            time.sleep(random.uniform(2, 5))
            if self.running:
                student = random.choice(test_students)
                print(f"[SIMULASI] Scan NIS: {student['nis']}")
                self.send_scan(student['nis'])
    
    def run(self):
        """Main loop"""
        print("=" * 50)
        print("SCANNER DAEMON - Sistem Absensi")
        print("=" * 50)
        
        # Setup scanner
        has_scanner = self.setup_scanner()
        
        if has_scanner:
            print("📡 Scanner siap digunakan")
            print("🔍 Arahkan scanner ke barcode siswa...")
            print("-" * 50)
            
            try:
                while self.running:
                    barcode = self.read_from_scanner()
                    if barcode:
                        print(f"📷 Barcode terbaca: {barcode}")
                        self.send_scan(barcode)
                        
            except KeyboardInterrupt:
                print("\n⏹️  Daemon dihentikan oleh user")
                
        else:
            # Run simulation mode
            self.simulate_scanner()
        
        print("=" * 50)
        print("Scanner Daemon berhenti")
        print("=" * 50)

if __name__ == '__main__':
    daemon = ScannerDaemon()
    daemon.run()