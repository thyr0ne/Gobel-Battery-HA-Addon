import serial
import socket
import logging

class BMSCommunication:
    def __init__(self, interface='serial', serial_port=None, baud_rate=None, ethernet_ip=None, ethernet_port=None,buffer_size=1024,debug=0):
        self.interface = interface
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.ethernet_ip = ethernet_ip
        self.ethernet_port = ethernet_port
        self.buffer_size = buffer_size
        self.bms_connection = None

        # Configure logging
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def connect(self):
        if self.interface == 'serial' and self.serial_port and self.baud_rate:
            try:
                self.logger.info(f"Trying to connect BMS over {self.serial_port}:{self.baud_rate}")
                self.bms_connection = serial.Serial(self.serial_port, self.baud_rate, timeout=3)
                self.logger.info(f"Connected to BMS over serial port: {self.serial_port} with baud rate: {self.baud_rate}")
                self.logger.info("Please ensure the Baud Rate is correctly set. An incorrect baud rate may not raise an immediate error, but it can lead to communication failures or corrupted data.")

                return self.bms_connection
            except serial.SerialException as e:
                self.logger.error(f"Serial connection error: {e}")
                return None
        elif self.interface in ['ethernet', 'wifi'] and self.ethernet_ip and self.ethernet_port:
            try:
                self.logger.info(f"Trying to connect BMS over {self.ethernet_ip}:{self.ethernet_port}")
                self.bms_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.bms_connection.settimeout(3)
                self.bms_connection.connect((self.ethernet_ip, self.ethernet_port))
                self.logger.info(f"Connected to BMS over Ethernet: {self.ethernet_ip}:{self.ethernet_port}")
                return self.bms_connection
            except socket.error as e:
                self.logger.error(f"Ethernet connection error: {e}")
                return None
        else:
            self.logger.error("Invalid parameters or interface selection.")
            return None


    def disconnect(self):
        if self.bms_connection:
            if self.interface == 'serial':
                try:
                    self.bms_connection.close()
                    self.logger.debug(f"Disconnected from BMS over serial port: {self.serial_port}")
                except serial.SerialException as e:
                    self.logger.error(f"Error while disconnecting serial connection: {e}")
            
            elif self.interface in ['ethernet', 'wifi']:
                try:
                    self.bms_connection.close()
                    self.logger.debug(f"Disconnected from BMS over Ethernet: {self.ethernet_ip}:{self.ethernet_port}")
                except socket.error as e:
                    self.logger.error(f"Error while disconnecting Ethernet connection: {e}")
            
            # Set connection to None after closing it.
            self.bms_connection = None
        else:
            self.logger.warning("No active connection to disconnect.")




    def send_data(self, data):
        try:
            # Ensure data is in bytes format
            if isinstance(data, str):
                data = data.encode()  # Convert string to bytes if necessary

            # Check if the connection is a socket (Ethernet)
            if hasattr(self.bms_connection, 'send'):
                self.bms_connection.send(data)
            # Check if the connection is a serial connection
            elif hasattr(self.bms_connection, 'write'):
                self.bms_connection.write(data)
            else:
                raise ValueError("Unsupported connection type")
            return True

        except Exception as e:
            self.logger.error(f"Error sending data to BMS: {e}")
            self.connect()
            return False

    def receive_data(self):
        try:
            # Check if the connection is a serial connection
            if hasattr(self.bms_connection, 'readline'):
                raw_data = self.bms_connection.readline()
                received_data = raw_data.decode().strip()
            # Check if the connection is a socket (Ethernet)
            elif hasattr(self.bms_connection, 'recv'):
                # Assuming a buffer size of 1024 bytes for demonstration purposes
                raw_data = self.bms_connection.recv(self.buffer_size)
                received_data = raw_data.decode().strip()
            else:
                raise ValueError("Unsupported connection type")

            self.logger.debug(f"Received data from BMS: {received_data}")
            return received_data
        except Exception as e:
            # Log the raw data when there is a decoding error
            if 'raw_data' in locals():
                self.logger.error(f"Error receiving data from BMS: {e}. Raw data: {raw_data}")
                self.logger.error(f"Raw data (hex): {raw_data.hex()}")
            else:
                self.logger.warning(f"No data received from BMS: {e}")
            return None
