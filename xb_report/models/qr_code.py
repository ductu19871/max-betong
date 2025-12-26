# -*- coding: utf-8 -*-
# Update 1: 20/11/2019 11:42:00
# Created by Mai Tien Dung
# Depended on : qrcode-6.1 and python-docx-0.8.10

import qrcode
from io import BytesIO
import hashlib
from docx import Document
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree

NAMESPACES = {
    'rl': 'http://schemas.openxmlformats.org/package/2006/relationships',
}

class XBQRCode:

    def __init__(self, qr_box_size, qr_border, qr_string, docx_data):
        """
        :param qr_box_size: box_size option of qrcode library
        :param qr_border: border option of qrcode library
        :param qr_string: string want to convert qr code image
        :param docx_data: BytesIO data of a docx
        """
        # Define Box Size of QR Code
        if not qr_box_size:
            self.qr_box_size = 1.5
        else:
            self.qr_box_size = qr_box_size
        # Define Border of QR Code
        if not qr_border:
            self.qr_border = 0.5
        else:
            self.qr_border = qr_border
        # Define String of QR Code
        if not qr_string:
            self.qr_string = ''
        else:
            self.qr_string = qr_string
        # Define 'BytesIO' data of a document
        self.docx_data = docx_data
        # Define SHA1 of images want to replace
        self.sha1_image = '78b3b1e01e6aa9c1ee273ff4a751e230d5b98622'

    def _general_qr_code(self):
        """
        General QR Code from string
        :return: BytesIO of an image QR Code
        """
        byte_io_data = BytesIO()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=self.qr_box_size,
            border=self.qr_border
        )
        qr.add_data(self.qr_string)
        qr.make(fit=True)

        qr_code_data_img = qr.make_image(fill_color="white", back_color="black")
        qr_code_data_img.save(byte_io_data)

        return byte_io_data

    def _qr_code_sha1(self, qr_code):
        """
        :param qr_code: BytesIO of an image
        :return: SHA1 of QR Code
        """
        qr_code.seek(0)
        binary_data = qr_code.read()
        qr_binary_sha1 = hashlib.sha1(binary_data).hexdigest()
        return qr_binary_sha1

    def _find_id_image(self, docx_file):
        """
        :param docx_file: BytesIO of an image
        :return: id
        Find an id image in ./word/_rels/document.xml.rels
        Result must be 'rId' + number: Ex: rId7
        """
        document = Document(docx_file)
        result = False
        rels = dict(document.part.rels)
        for item in rels:
            if rels[item]._target._content_type == 'image/png' and rels[item]._target.sha1 == self.sha1_image:
                result = item
                break
        del document
        return result

    def _get_image_replace_path(self):
        """
        :return: an image path. Ex: 'word/media/image1.png'
        """
        document = ZipFile(self.docx_data, mode='r')
        xml_content = document.read('word/_rels/document.xml.rels')
        tree = etree.fromstring(xml_content)
        image_xml_id = self._find_id_image(self.docx_data)
        document.close()

        if image_xml_id:
            rId = tree.find(".//{%s}Relationship[@Id='%s']" % (NAMESPACES['rl'], image_xml_id))
            if rId is not None or not False:
                return 'word/' + dict(rId.attrib)['Target']
        return False

    def _add_qrcode_image_into_docx(self, qr_byte_io):
        """
        :param qr_byte_io: BytesIO of QR Code
        :return: a zip file which has an element picture
        """
        qr_byte_io.seek(0)
        qr_bytes = qr_byte_io.read()
        new_file = BytesIO()
        new_path = self._get_image_replace_path()

        if new_path:
            with ZipFile(new_file, 'w', ZIP_DEFLATED) as output:
                output.writestr(new_path, qr_bytes)

        return new_file

    def write_file(self):
        qr_byte_io = self._general_qr_code()
        byte_io_new_qr = self._add_qrcode_image_into_docx(qr_byte_io)
        new_path = self._get_image_replace_path()
        new_file = BytesIO()
        #
        if new_path:
            document = ZipFile(self.docx_data, mode='r')
            new_qr_zip = ZipFile(byte_io_new_qr, mode='r')
            with ZipFile(new_file, 'w', ZIP_DEFLATED) as output:
                for item in document.filelist:
                    if item.filename != new_path:
                        copy_file = document.read(item)
                        output.writestr(item.filename, copy_file)
                output.writestr(new_qr_zip.filelist[0].filename, new_qr_zip.read(new_qr_zip.filelist[0]))
            document.close()
            new_qr_zip.close()
        return new_file