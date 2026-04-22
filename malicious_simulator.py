import socket
import time
import requests

while True:
    try:
        # Repeated outbound requests (suspicious pattern)
        requests.get("http://example.com")
        
        # Raw socket connection to random port
        s = socket.socket()
        s.connect(("93.184.216.34", 80))  # example.com IP
        s.close()

        print("Sending background traffic...")
        
        time.sleep(2)  # frequent requests
    except:
        pass