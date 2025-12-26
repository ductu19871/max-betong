import re
import logging
from num2words import num2words
from dateutil import rrule
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
try:
     # NOTE: import for version > 1.8.6
    # from openpyxl.compat import unicode
    from openpyxl.cell import cell
    ILLEGAL_CHARACTERS_RE = cell.ILLEGAL_CHARACTERS_RE
except ImportError:
    try:
        # NOTE: import for version <= 1.8.6
        from openpyxl import cell
        # from openpyxl.shared.compat import unicode
    except ImportError:
        _logger.debug(
            'Cannot import "openpyxl". Please make sure it is installed.')

from odoo import tools,_
from odoo.tools import float_is_zero
from odoo.tools.date_utils import start_of, end_of

# NOTE: hook default check_string
def check_string(self, value):
    """Check string coding, length, and line break character"""
    if value is None:
        return
    # convert to unicode string, python 3 str is unicode
    if not isinstance(value, str):
        value = str(value, self.encoding)
    value = str(value)
    # string must never be longer than 32,767 characters
    # truncate if necessary
    value = value[:32767]
    if re.search(ILLEGAL_CHARACTERS_RE, value):
        # NOTE: just replace illegal char instead of raising exception
        value = re.sub(ILLEGAL_CHARACTERS_RE, '', value)
    return value

try:
    cell.Cell.check_string = check_string
except:
    pass

def amount_to_text(env, amount, decimal_places=2,precision_digits =1):
    def _num2words(number, lang):
        try:
            return num2words(number, lang=lang).title()
        except NotImplementedError:
            return num2words(number, lang='en').title()

    if num2words is None:
        logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
        return ""

    formatted = "%.{0}f".format(decimal_places) % amount
    parts = formatted.partition('.')
    integer_value = int(parts[0])
    fractional_value = int(parts[2] or 0)

    lang_code = env.context.get('lang') or env.user.lang
    lang = env['res.lang'].with_context(active_test=False).search([('code', '=', lang_code)])
    amount_words = tools.ustr('{amt_value}').format(
                    amt_value=_num2words(integer_value, lang=lang.iso_code))
    if not float_is_zero(amount - integer_value,precision_digits): 
        amount_words += ' ' + _('and') + tools.ustr(' {amt_value}').format(
                    amt_value=_num2words(fractional_value, lang=lang.iso_code),)
    return amount_words

    # TODO: Function that converts numbers to roman letters
def int_to_Roman(num, upper=False):
    lookup = [
        (1000, 'M'),
        (900, 'CM'),
        (500, 'D'),
        (400, 'CD'),
        (100, 'C'),
        (90, 'XC'),
        (50, 'L'),
        (40, 'XL'),
        (10, 'X'),
        (9, 'IX'),
        (5, 'V'),
        (4, 'IV'),
        (1, 'I'),
    ]
    res = ''
    for (n, roman) in lookup:
        (d, num) = divmod(num, n)
        res += roman * d
    return res.upper() if upper else res

def remove_trailing_zeros(num):
    str_num = str(num)
    if '.' not in str_num: #ignore integer
        return str_num
    str_num = str_num.rstrip('0')
    str_num = str_num.rstrip('.')
    return str_num

def _get_previous_period(date_from, date_to):
    if not date_from or not date_to or date_from > date_to:
        return False, False
    
    if start_of(date_from, 'month') == date_from and \
            end_of(date_to, 'month') == date_to:
        '''
            date_from = datetime.date(2023, 1, 1)
            date_to = datetime.date(2023, 12, 31)
            ---> Rrule:
                        [datetime.datetime(2023, 1, 1, 0, 0),
                        ...
                        datetime.datetime(2023, 12, 1, 0, 0)]
            len_range_month = 12

            previous_date_from = datetime.date(2023, 1, 1):
            while 12 > 0:
                previous_date_from = datetime.date(2022, 12, 1)
                len_range_month = 11
                ...
            previous_date_from = datetime.date(2022, 1, 1)
            previous_date_to = datetime.date(2022, 12, 31)
        '''
        len_range_month = len(list(rrule.rrule(rrule.MONTHLY, dtstart=date_from, until=date_to)))
        previous_date_from = date_from
        previous_date_to = date_from - timedelta(days=1)

        while len_range_month > 0:
            previous_date_from = start_of(previous_date_from - timedelta(days=1), 'month')
            len_range_month -= 1
        
        return previous_date_from, previous_date_to
    else:
        '''
            date_to:    datetime.date(2023, 3, 15)
            date_from:  datetime.date(2023, 3, 1)
            previous_day = 14 + 1
        '''
        previous_day = (date_to - date_from).days + 1
        previous_date_from = (datetime.combine(date_from, datetime.min.time()) - timedelta(days=previous_day)).date()
        previous_date_to = (datetime.combine(date_from, datetime.min.time()) - timedelta(days=1)).date()
        return previous_date_from, previous_date_to

def get_decimal_place(float_value):
    idx = str(float_value)[::-1].find('.')
    if idx == 1 and str(float_value)[-idx] == '0':
        return 0
    return idx