from io import BytesIO
from PyPDF2 import PdfFileWriter, PdfFileReader


def add_password_pdf(pdf_file, password):
    if not password:
        return pdf_file
    input_buffer = BytesIO(pdf_file)
    reader = PdfFileReader(input_buffer)
    writer = PdfFileWriter()
    writer.appendPagesFromReader(reader)
    writer.encrypt(user_pwd=password, owner_pwd=None, use_128bit=True)
    output_buffer = BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer.read()
