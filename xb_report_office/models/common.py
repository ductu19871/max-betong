# ---------------------------------------------------------------------------------------------
# Convert float to counting string
# ---------------------------------------------------------------------------------------------

to_19 = ('không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một', 'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín')
tens = ('hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi')
denom = ('', 'ngàn', 'triệu', 'tỷ', 'ngàn tỷ', 'triệu tỷ', 'tỷ tỷ', 'ngàn tỷ tỷ', 'triệu tỷ tỷ', 'tỷ tỷ tỷ', 'Nonillion', 'Décillion', 'Undecillion', 'Duodecillion', 'Tredecillion', 'Quattuordecillion', 'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Icosillion', 'Vigintillion')
BLANK_IMAGE = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='

def _convert_nn(val):
    """convert a value < 100 to Vietnamese.
    """
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if (val % 10) == 1:
                return dcap + ' mốt'
            elif (val % 10) == 5:
                return dcap + ' lăm'
            elif val % 10:
                return dcap + ' ' + to_19[val % 10]
            return dcap


def _convert_nnn(val):
    """
        convert a value < 1000 to Vietnamese, special cased because it is the level that kicks
        off the < 100 special case.  The rest are more general.  This also allows you to
        get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = to_19[rem] + ' trăm'
        if mod > 0:
            word += ' '
    if mod > 0:
        if mod < 10:
            word += 'lẻ '
        word = word + _convert_nn(mod)
    return word


def vi_number(val):
    if val < 100:
        return _convert_nn(val)
    if val < 1000:
        return _convert_nnn(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            if l < 10:
                ret = _convert_nn(l) + ' ' + denom[didx]
            else:
                ret = _convert_nnn(l) + ' ' + denom[didx]
            if r > 0:
                ret = ret + ', ' + vi_number(r)
            return ret


def vi_number_long_text(amount):
    Text = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    TextLuythua = ["", "ngàn", "triệu,", "tỷ,", "ngàn tỷ,", "triệu tỷ,", "tỷ tỷ,"]
    textnumber = ""
    length = len(amount)
    unread = []
    for i in range(0, length):
        unread.append(0)
    for i in range(0, length):
        so = amount[length - i - 1: length - i - 1 + 1]

        if so == 0 and i % 3 == 0 and unread[i] == 0:
            for j in range(0, length):
                so1 = amount[length - j - 1:length - j - 1 + 1]
                if so1 != 0:
                    break

            if int((j - i) / 3) > 0:
                for k in range(0, int((j - i) / 3) * 3 + i):
                    unread[k] = 1

    for i in range(0, length):
        so = amount[length - i - 1: length - i - 1 + 1]
        if unread[i] == 1:
            continue
        if i % 3 == 0 and i > 0:
            textnumber = TextLuythua[i / 3] + " " + textnumber
        if i % 3 == 2:
            textnumber = 'trăm ' + textnumber
        if i % 3 == 1:
            textnumber = 'mươi ' + textnumber

        textnumber = Text[int(so)] + " " + textnumber

    textnumber = textnumber.replace("không mươi", "lẻ")
    textnumber = textnumber.replace("lẻ không", "")
    textnumber = textnumber.replace("mươi không", "mươi")
    textnumber = textnumber.replace("một mươi", "mười")
    textnumber = textnumber.replace("mươi năm", "mươi lăm")
    textnumber = textnumber.replace("mươi một", "mươi mốt")
    textnumber = textnumber.replace("mười năm", "mười lăm")
    textnumber_dong = textnumber + "đồng"
    textnumber_dong = textnumber_dong.replace("triệu, đồng", "triệu đồng")
    textnumber_dong = textnumber_dong.replace("ngàn, đồng", "ngàn đồng")
    textnumber_dong = textnumber_dong.replace("không trăm  đồng", "đồng")
    textnumber_dong = textnumber_dong.replace("trăm  ngàn", "trăm ngàn")
    textnumber_dong = textnumber_dong.replace(", không trăm  triệu, không trăm ngàn", "")
    textnumber_dong = textnumber_dong.replace(", không trăm ngàn", "")
    textnumber_dong = textnumber_dong.replace(", không trăm triệu", "")

    return textnumber_dong


def amount_to_text_vi_long_text(number, currency=None):
    number = '%.2f' % abs(number)
    list = str(number).split('.')
    start_word = vi_number_long_text(list[0])
    cents_number = int(list[1])
    end_word = ''
    if cents_number > 0:
        end_word = ' ' + vi_number_long_text(list[1])
    cents_name = (cents_number > 1) and ' xu' or ''
    final_result = start_word + ' ' + end_word[1:].replace(" đồng", "") + cents_name
    return (final_result[0].upper() + final_result[1:]).strip()


def amount_to_text_vn(number, currency=None, long_text=False):
    if long_text:
        return amount_to_text_vi_long_text(number, currency)
    if not currency:
        currency = 'VND'
    if currency == 'VND':
        currency = 'đồng'
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = vi_number(abs(int(list[0])))
    cents_number = int(list[1])
    end_word = ''
    if cents_number > 0:
        end_word = ' ' + vi_number(int(list[1]))
    cents_name = (cents_number > 1) and ' xu' or ''
    final_result = start_word + ' ' + units_name + end_word + cents_name
    return final_result[0].upper() + final_result[1:]

