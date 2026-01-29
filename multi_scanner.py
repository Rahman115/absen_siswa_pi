# /home/pi/multi_scanner.py
#!/usr/bin/env python3
"""
Multi-scanner system untuk 4+ scanner
"""

import usb.core
import usb.util
import threading
import queue
import requests
import json
import time
from datetime import datetime

class MultiScanner:
    def __init__(self):
        self.scanners = []
        self.scan_queue = queue.Queue()
        self.api_url = "http://localhost:5000/api/scan"
        self.running = True
        
        # Scanner configurations
        self.scanner_configs = [
            {"name": "Scanner 1 - Gerbang Utama", "location": "Gerbang Utama"},
            {"name": "Scanner 2 - Lab Komputer", "location": "Lab Komputer"},
            {"name": "Scanner 3 - Perpustakaan", "location": "Perpustakaan"},
            {"name": "Scanner 4 - Kantin", "location": "Kantin"},
        ]
        
    def detect_scanners(self):
        """Detect all connected scanners"""
        print("Mendeteksi scanner...")
        
        devices = list(usb.core.find(find_all=True))
        scanner_devices = []
        
        for i, dev in enumerate(devices):
            try:
                # Cek apakah device HID (biasanya scanner)
                if dev.bDeviceClass == 0:  # HID device
                    scanner_info = {
                        'device': dev,
                        'name': f"Scanner {i+1}",
                        'location': self.scanner_configs[i]['location'] if i < len(self.scanner_configs) else f"Lokasi {i+1}",
                        'id': i
                    }
                    scanner_devices.append(scanner_info)
                    print(f"✓ Ditemukan: {scanner_info['name']} di {scanner_info['location']}")
            except:
                continue
        
        if not scanner_devices:
            print("Tidak ada scanner fisik ditemukan. Mode simulasi aktif.")
            self.start_simulation()
        else:
            self.scanners = scanner_devices
            self.start_all_scanners()
    
    def scanner_worker(self, scanner_info):
        """Worker thread untuk satu scanner"""
        device = scanner_info['device']
        scanner_name = scanner_info['name']
        location = scanner_info['location']
        
        print(f"Memulai {scanner_name}...")
        
        try:
            if device.is_kernel_driver_active(0):
                device.detach_kernel_driver(0)
            
            device.set_configuration()
            endpoint = device[0][(0,0)][0]
            
            buffer = ""
            while self.running:
                try:
                    data = device.read(
                        endpoint.bEndpointAddress,
                        endpoint.wMaxPacketSize,
                        timeout=1000
                    )
                    
                    if data:
                        for byte in data:
                            if 32 <= byte < 127:
                                buffer += chr(byte)
                        
                        if '\r' in buffer or '\n' in buffer:
                            barcode = buffer.strip('\r\n')
                            if barcode:
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                print(f"[{timestamp}] {scanner_name}: {barcode}")
                                
                                # Kirim ke API
                                self.send_scan(barcode, location)
                                
                            buffer = ""
                            
                except usb.core.USBTimeoutError:
                    continue
                    
        except Exception as e:
            print(f"Error di {scanner_name}: {e}")
    
    def send_scan(self, nis, location):
        """Send scan to API"""
        try:
            data = {'nis': nis, 'location': location}
            response = requests.post(self.api_url, json=data, timeout=3)
            result = response.json()
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            if result.get('success'):
                siswa = result.get('siswa', {})
                print(f"[{timestamp}] ✓ {siswa.get('nama')} - {location}")
            else:
                print(f"[{timestamp}] ✗ {result.get('message')} - {location}")
                
        except Exception as e:
            print(f"[ERROR] Gagal kirim ke API: {e}")
    
    def start_all_scanners(self):
        """Start all scanner threads"""
        threads = []
        
        for scanner in self.scanners:
            thread = threading.Thread(
                target=self.scanner_worker,
                args=(scanner,),
                daemon=True
            )
            thread.start()
            threads.append(thread)
            time.sleep(0.5)  # Delay antar scanner
        
        print(f"\n✅ {len(threads)} scanner aktif")
        print("Tekan Ctrl+C untuk berhenti\n")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nMenghentikan semua scanner...")
            self.running = False
    
    def start_simulation(self):
        """Start simulation mode"""
        print("Mode simulasi aktif dengan 4 scanner virtual")
        
        def simulate_scanner(scanner_id):
            test_nis = ['2026001', '2026002', '2026003', '2026004', '2026005']
            import random
            
            while self.running:
                time.sleep(random.uniform(1, 4))
                if self.running:
                    nis = random.choice(test_nis)
                    location = self.scanner_configs[scanner_id]['location']
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] {self.scanner_configs[scanner_id]['name']}: {nis}")
                    self.send_scan(nis, location)
        
        # Start 4 simulation threads
        threads = []
        for i in range(4):
            thread = threading.Thread(
                target=simulate_scanner,
                args=(i,),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nMenghentikan simulasi...")
            self.running = False
    
    def run(self):
        """Main entry point"""
        print("=" * 50)
        print("MULTI-SCANNER ABSENSI SISTEM")
        print("=" * 50)
        
        self.detect_scanners()

if __name__ == '__main__':
    system = MultiScanner()
    system.run()