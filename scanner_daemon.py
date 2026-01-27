# /home/pi/scanner_daemon.py
#!/usr/bin/env python3
"""
Daemon untuk membaca scanner dan mengirim ke API
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
        self.api_url = "http://localhost:5000/api/scan"
        self.running = True
        self.device = None
        self.setup_scanner()
    
    def setup_scanner(self):
        """Setup USB scanner"""
        print("Mencari scanner...")
        
        # Try common scanner VID/PID
        scanner_ids = [
            (0x1a86, 0x7523),  # Generic CH340
            (0x0c2e, 0x0b00),  # Datalogic
            (0x05fe, 0x1010),  # Honeywell
            (0x1a40, 0x0101),  # Terminus
        ]
        
        for vid, pid in scanner_ids:
            self.device = usb.core.find(idVendor=vid, idProduct=pid)
            if self.device:
                print(f"Scanner ditemukan: VID={vid:04x}, PID={pid:04x}")
                break
        
        if not self.device:
            print("Scanner fisik tidak ditemukan. Mode simulasi aktif.")
    
    def send_to_api(self, nis):
        """Send scan data to API"""
        try:
            data = {'nis': nis}
            response = requests.post(
                self.api_url,
                json=data,
                timeout=5
            )
            
            result = response.json()
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if result.get('success'):
                siswa = result.get('siswa', {})
                print(f"[{timestamp}] ✓ {siswa.get('nama')} ({nis}) - {siswa.get('kelas')}")
            else:
                print(f"[{timestamp}] ✗ {result.get('message')}")
                
        except requests.exceptions.RequestException as e:
            print(f"[{timestamp}] ! Error API: {e}")
    
    def read_scanner(self):
        """Read data from physical scanner"""
        if not self.device:
            return None
        
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
        test_nis = ['2023001', '2023002', '2023003', '2023004', '2023005']
        import random
        
        while self.running:
            time.sleep(random.uniform(2, 5))
            if self.running:
                nis = random.choice(test_nis)
                print(f"[SIMULASI] Scan NIS: {nis}")
                self.send_to_api(nis)
    
    def run(self):
        """Main loop"""
        print("Scanner Daemon started. Press Ctrl+C to stop.")
        print("Ready to scan barcode...")
        
        if not self.device:
            print("Running in simulation mode")
            self.simulate_scanner()
            return
        
        buffer = ""
        try:
            while self.running:
                barcode = self.read_scanner()
                if barcode:
                    print(f"Scan detected: {barcode}")
                    self.send_to_api(barcode)
                    
        except KeyboardInterrupt:
            print("\nDaemon stopped by user")
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            self.running = False

if __name__ == '__main__':
    daemon = ScannerDaemon()
    daemon.run()
