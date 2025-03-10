import network
import socket
import json
import time
from machine import Pin

# WiFi credentials
SSID = "Airtel_Ukshati"
PASSWORD = "32addeepi"

# Setup pins
flow_sensor = Pin(0, Pin.IN, Pin.PULL_UP)  # Flow sensor connected to GPIO0
relay = Pin(2, Pin.OUT)                     # Relay connected to GPIO2

# Global variables
pulse_count = 0
wlan = None

def count_pulse(pin):
    global pulse_count
    pulse_count += 1

# Setup interrupt for flow sensor
flow_sensor.irq(trigger=Pin.IRQ_FALLING, handler=count_pulse)

def connect_wifi():
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Disconnect if already connected
    if wlan.isconnected():
        wlan.disconnect()
        time.sleep(1)
    
    print('Connecting to WiFi...')
    wlan.connect(SSID, PASSWORD)
    
    # Wait for connection with timeout
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('Waiting for connection...')
        time.sleep(1)
    
    if wlan.status() != 3:
        raise RuntimeError('Network connection failed')
    else:
        print('Connected')
        status = wlan.ifconfig()
        print('IP:', status[0])
    
    return wlan

def calculate_flow_rate():
    global pulse_count
    start_time = time.ticks_ms()
    time.sleep(1)  # Measure over 1 second
    duration = time.ticks_diff(time.ticks_ms(), start_time) / 1000  # Convert to seconds
    
    # Convert pulses to L/min (adjust calibration factor based on your sensor)
    calibration_factor = 7.5  # Pulses per liter
    flow_rate = (pulse_count / calibration_factor) * (60 / duration)  # Convert to L/min
    
    pulse_count = 0  # Reset counter
    return round(flow_rate, 2)

def handle_cors_preflight(client_socket):
    response = 'HTTP/1.1 204 No Content\r\n'
    response += 'Access-Control-Allow-Origin: *\r\n'
    response += 'Access-Control-Allow-Methods: GET, OPTIONS\r\n'
    response += 'Access-Control-Allow-Headers: Content-Type\r\n'
    response += 'Access-Control-Max-Age: 3600\r\n'
    response += '\r\n'
    client_socket.send(response)

def handle_client_request(client_socket):
    try:
        request = client_socket.recv(1024).decode('utf-8')
        
        # Handle CORS preflight
        if 'OPTIONS' in request:
            handle_cors_preflight(client_socket)
            return
            
        # Handle relay control requests
        if 'GET /relay/on' in request:
            relay.value(1)
        elif 'GET /relay/off' in request:
            relay.value(0)
        
        # Get current flow rate
        flow_rate = calculate_flow_rate()
        
        # Auto-shutdown if no flow detected
        if flow_rate == 0:
            relay.value(0)
        
        # Prepare response data
        response_data = {
            'wifi_status': wlan.isconnected() if wlan else False,
            'flow_rate': flow_rate,
            'relay_status': relay.value()
        }
        
        # Send response with CORS headers
        response = 'HTTP/1.1 200 OK\r\n'
        response += 'Content-Type: application/json\r\n'
        response += 'Access-Control-Allow-Origin: *\r\n'
        response += 'Access-Control-Allow-Methods: GET, OPTIONS\r\n'
        response += 'Access-Control-Allow-Headers: Content-Type\r\n'
        response += 'Cache-Control: no-store\r\n'
        response += '\r\n'
        response += json.dumps(response_data)
        
        client_socket.send(response)
    except Exception as e:
        print('Error handling client:', e)
        # Send error response
        error_response = 'HTTP/1.1 500 Internal Server Error\r\n'
        error_response += 'Content-Type: application/json\r\n'
        error_response += 'Access-Control-Allow-Origin: *\r\n'
        error_response += '\r\n'
        error_response += json.dumps({'error': str(e)})
        try:
            client_socket.send(error_response)
        except:
            pass
    finally:
        client_socket.close()

def main():
    global wlan
    while True:
        try:
            # Ensure WiFi is connected
            if not wlan or not wlan.isconnected():
                wlan = connect_wifi()
            
            # Create server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(('', 80))
            server_socket.listen(5)
            print('Server started')
            
            while True:
                if not wlan.isconnected():
                    raise RuntimeError('WiFi connection lost')
                    
                try:
                    client, addr = server_socket.accept()
                    print('Client connected from', addr)
                    handle_client_request(client)
                except Exception as e:
                    print('Error accepting client:', e)
                    
        except Exception as e:
            print('Server error:', e)
            time.sleep(5)  # Wait before retrying
        finally:
            try:
                server_socket.close()
            except:
                pass

if __name__ == '__main__':
    main()