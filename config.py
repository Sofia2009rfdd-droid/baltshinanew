from enum import Enum


token = '8484781817:AAFkB0_RAK77SlQwiZ5Xcjzh2GxbCxVqyWs'

db_file = "database.db"

class States(Enum):
    S_START = "0"
    S_TART = "1"
    S_ENTER_DATA = "2"
    S_ENTER_TOTAL = "3"
    S_ENTER_TIME = "4"
    S_ENTER_TEL = "5"
    S_ENTER_NAME = "6"
    S_ENTER_N_AME = "7"

    S_SEND_PIC = "8"
    S_SEND_PIC_OUT = "9"
    CANCEL = "10"
