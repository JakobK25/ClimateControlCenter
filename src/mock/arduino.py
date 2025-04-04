import random
import time

class MockBoard:
    """A mock Arduino board for testing without hardware."""
    
    def __init__(self):
        self.analog = [MockAnalogPin(i) for i in range(6)]
        self.digital = [MockDigitalPin(i) for i in range(14)]
        print("Initialized mock Arduino board")

class MockAnalogPin:
    """A mock analog pin that generates random values."""
    
    def __init__(self, pin_number):
        self.pin_number = pin_number
        self.reporting = False
        self._base_value = random.random()  # Initial base value
        
    def read(self):
        """Return a slightly fluctuating value based on the pin number."""
        if self.pin_number == 0:  # Temperature
            return 0.5 + (random.random() - 0.5) * 0.05  # ~20°C with small fluctuations
        elif self.pin_number == 1:  # Light
            return 0.6 + (random.random() - 0.5) * 0.1   # 60% light with fluctuations
        elif self.pin_number == 2:  # Humidity
            return 0.4 + (random.random() - 0.5) * 0.08  # 40% humidity with fluctuations
        else:
            return random.random()

    def enable_reporting(self):
        self.reporting = True

class MockDigitalPin:
    """A mock digital pin."""
    
    def __init__(self, pin_number):
        self.pin_number = pin_number
        self.value = 0
        self.mode = None
        
    def write(self, value):
        self.value = value
        print(f"Digital pin {self.pin_number} set to {'HIGH' if value else 'LOW'}")

def setup_arduino(port):
    """Initialize a mock Arduino board."""
    print(f"Mock mode active. Ignoring real port: {port}")
    time.sleep(1)  # Simulate connection delay
    return MockBoard()