import utime
from lcd_project.lcd_api import LcdApi
from machine import I2C

# PCF8574 pin definitions
MASK_RS = 0x01
MASK_RW = 0x02
MASK_E = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4


class I2cLcd(LcdApi):
    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.i2c_data = bytearray(1)
        super().__init__(num_lines, num_columns)

        # Initialize display
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(5)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(1)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(1)

        # Set 4-bit mode
        self.hal_write_init_nibble(self.LCD_FUNCTION)
        utime.sleep_ms(1)

        # Configure display
        cmd = self.LCD_FUNCTION
        if num_lines > 1:
            cmd |= self.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)

        # Display & cursor configuration
        self.display_on()
        self.clear()

        # Set entry mode to increment cursor position
        self.hal_write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)

    def hal_backlight_on(self):
        self.i2c_data[0] = 1 << SHIFT_BACKLIGHT
        self.i2c.writeto(self.i2c_addr, self.i2c_data)

    def hal_backlight_off(self):
        self.i2c_data[0] = 0
        self.i2c.writeto(self.i2c_addr, self.i2c_data)

    def hal_write_init_nibble(self, nibble):
        # Send upper 4 bits for initialization
        b = ((nibble >> 4) & 0x0f) << SHIFT_DATA
        b |= MASK_E
        self.i2c_data[0] = b
        self.i2c.writeto(self.i2c_addr, self.i2c_data)
        utime.sleep_us(1)
        self.i2c_data[0] = b & ~MASK_E
        self.i2c.writeto(self.i2c_addr, self.i2c_data)
        utime.sleep_us(50)

    def hal_write_command(self, cmd):
        # Send command to LCD
        self._write_upper_nibble(cmd)
        self._write_lower_nibble(cmd)

    def hal_write_data(self, data):
        # Send data to LCD
        self._write_upper_nibble(data, MASK_RS)
        self._write_lower_nibble(data, MASK_RS)

    def _write_upper_nibble(self, nibble, rs=0):
        # Send upper 4 bits of data or command
        b = (((nibble >> 4) & 0x0f) << SHIFT_DATA) | (1 << SHIFT_BACKLIGHT) | rs
        b |= MASK_E
        self.i2c_data[0] = b
        self.i2c.writeto(self.i2c_addr, self.i2c_data)
        utime.sleep_us(1)
        self.i2c_data[0] = b & ~MASK_E
        self.i2c.writeto(self.i2c_addr, self.i2c_data)
        utime.sleep_us(50)

    def _write_lower_nibble(self, nibble, rs=0):
        # Send lower 4 bits of data or command
        b = ((nibble & 0x0f) << SHIFT_DATA) | (1 << SHIFT_BACKLIGHT) | rs
        b |= MASK_E
        self.i2c_data[0] = b
        self.i2c.writeto(self.i2c_addr, self.i2c_data)
        utime.sleep_us(1)
        self.i2c_data[0] = b & ~MASK_E
        self.i2c.writeto(self.i2c_addr, self.i2c_data)
        utime.sleep_us(50)
