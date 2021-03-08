import re
import locale
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

SYMBOLS_IN_RECEIPT=56
MARGIN_LEFT=2

def to_camel(string:str):
    return ''.join(word.capitalize() for word in string.split('_'))

def from_camel(string:str):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()

def format_currency(v):
    return locale.format_string("%.2f", v, grouping = True, monetary=True)

def format_vat(v:float):
    return locale.format_string("%.2f", v, grouping = True, monetary=True)

def format_quantity(v:int):
    return locale.format_string("%.3f", v, grouping = True)

def format_spaces(reserved_symbols:int, inserted_var:object):
    return SYMBOLS_IN_RECEIPT-reserved_symbols-len(str(inserted_var))

def count_len(string:object):
    return len(str(string))

def align_blocks_w_delimiter(str1:str, str2:str, delimiter='|'):
    output=[]
    output.extend(list(str1))
    output.extend([' ']*(42-len(output)-len(list(str2))))
    output.extend(list(str2))
    if delimiter:
        output[len(output)//2] ='|'
    output_str = ''.join(output)
    return output_str

