# /home/pi/scanner_test.py
#!/usr/bin/env python3
import usb.core
import usb.util
import sys

# Cari device USB scanner
# Ganti VID/PID dengan scanner Anda
dev = usb.core.find(idVendor=0x9901, idProduct=0x301)

if dev is None:
    print("Scanner tidak ditemukan!")
    # Coba device HID umum
    dev = usb.core.find(idVendor=0x1a86, idProduct=0x7523)

if dev is None:
    print("Mode simulasi - Scanner tidak terdeteksi")
    print("Tekan Ctrl+C untuk keluar")
    
    # Simulasi input
    import time
    counter = 1
    while True:
        time.sleep(2)
        print(f"[SIMULASI] Scan NIS: 202300{counter}")
        counter += 1
        if counter > 5:
            counter = 1
else:
    print(f"Scanner ditemukan: {dev}")
    print("Ready untuk scanning...")
    
    try:
        # Detach kernel driver jika perlu
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
        
        # Set configuration
        dev.set_configuration()
        
        # Endpoint untuk baca data
        endpoint = dev[0][(0,0)][0]
        
        buffer = ""
        while True:
            try:
                data = dev.read(endpoint.bEndpointAddress, 
                              endpoint.wMaxPacketSize, 
                              timeout=5000)
                
                # Decode data
                if data:
                    # Convert ke karakter
                    for byte in data:
                        if 32 <= byte < 127:  # ASCII printable
                            buffer += chr(byte)
                    
                    # Jika ada newline, proses
                    if '\r' in buffer or '\n' in buffer:
                        barcode = buffer.strip('\r\n')
                        print(f"Scan: {barcode}")
                        buffer = ""
                        
            except usb.core.USBTimeoutError:
                continue
                
    except KeyboardInterrupt:
        print("\nProgram dihentikan")
