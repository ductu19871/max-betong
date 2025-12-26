# -*- coding: utf-8 -*-
# Author: Artiel
# Company : XBOSS
# Date: 03/08/2017 15:39
# Last Updated: 30/07/2019
# -*- coding: utf-8 -*-

import os
import io
import base64
import shutil
import urllib
import logging
import tempfile
import mimetypes
import subprocess

from contextlib import closing

logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

WD_FORMAT_PDF = 17
PP_FORMAT_PDF = 32
EX_FORMAT_PDF = 57


def convert_multiple_file(binary, mimetype=None, filename=None, format="path", mime_export='pdf'):
    """
    Converts a binary value to a mime file.

    :param binary: The binary value
    :param mimetype: The mime tpye of the binary value
    :param filename: The filename of the binary value
    :param format: The output format (path, binary, file, base64 | default: path)
    :return: returns output depending on the given format
    """
    ext = ''
    if mime_export:
        ext = '.' + mime_export
    else:
        ext = '.pdf'
    if not mimetype and not filename:
        raise ValueError("Either a mime type or a filename has to be given as argument.")
    else:
        if not mimetype:
            mimetype = mimetypes.guess_type(urllib.pathname2url(filename))[0]
        if not filename:
            extension = mimetypes.guess_extension(mimetype)
        else:
            extension = os.path.splitext(filename)[1]
        if os.path.isdir('/tmp/xb_report') == False:
            os.mkdir('/tmp/xb_report')
        tmp_wfile, tmp_wpath = tempfile.mkstemp(suffix=extension, dir='/tmp/xb_report')
        tmp_ppath = tmp_wpath.replace(extension, ext)
        if os.name == 'nt':
            tmp_wpath = tmp_wpath.replace("\\", "\\\\")
            tmp_ppath = tmp_ppath.replace("\\", "\\\\")
        with closing(os.fdopen(tmp_wfile, 'wb')) as file:
            file.write(binary)
        # print mimetype
        try:
            if mime_export == 'docx':
                __dispatch_docx[mimetype](tmp_wpath, tmp_ppath)
            elif mime_export == 'doc':
                __dispatch_doc[mimetype](tmp_wpath, tmp_ppath)
            elif mime_export == 'xlsx':
                __dispatch_xlsx[mimetype](tmp_wpath, tmp_ppath)
            elif mime_export == 'xls':
                __dispatch_xls[mimetype](tmp_wpath, tmp_ppath)
            elif mime_export == 'ods':
                __dispatch_ods[mimetype](tmp_wpath, tmp_ppath)
            elif mime_export == 'odt':
                __dispatch_odt[mimetype](tmp_wpath, tmp_ppath)
            elif mime_export == 'rtf':
                __dispatch_rtf[mimetype](tmp_wpath, tmp_ppath)
            elif mime_export == 'pdf':
                __dispatch_pdf[mimetype](tmp_wpath, tmp_ppath)
            else:
                raise ValueError("Minetype don't support!")
        except:
            raise ValueError("Don't support covert *%s to *%s!" % (extension, ext))
        if format == 'path':
            return tmp_ppath
        else:
            try:
                with closing(open(tmp_ppath, 'rb')) as file:
                    if format == 'binary':
                        return file.read()
                    elif format == 'file':
                        output = io.BytesIO()
                        output.write(file.read())
                        output.close()
                        return output
                    elif format == 'base64':
                        return base64.b64encode(file.read())
                    else:
                        raise ValueError("Unknown format type. Use one of these: path, binary, file, base64")
            finally:
                os.remove(tmp_wpath)
                os.remove(tmp_ppath)


def convert_document2pdf(input_path, output_path):
    """
    Converts a file to a mime file.

    :param input_path: The input path
    :param output_path: The output path
    :return: returns nothing
    """
    if os.name == 'nt':
        try:
            _convert_word2pdf(input_path, output_path)
        except IOError as error:
            raise
        except (ImportError, WindowsError) as error:
            logger.info("Failed to use MS Office | %s | Fallback to unoconv" % error)
            _libreoffice_converter(input_path, output_path)
    else:
        _libreoffice_converter(input_path, output_path)


def convert_presentation2pdf(input_path, output_path):
    """
    Converts a file to a mime file.

    :param input_path: The input path
    :param output_path: The output path
    :return: returns nothing
    """
    if os.name == 'nt':
        try:
            _convert_powerpoint2pdf(input_path, output_path)
        except IOError as error:
            raise
        except (ImportError, WindowsError) as error:
            logger.info("Failed to use MS Office | %s | Fallback to unoconv" % error)
            _libreoffice_converter(input_path, output_path)
    else:
        _libreoffice_converter(input_path, output_path)


def convert_spreadsheet2pdf(input_path, output_path):
    """
    Converts a file to a mime file.

    :param input_path: The input path
    :param output_path: The output path
    :return: returns nothing
    """
    if os.name == 'nt':
        try:
            _convert_excel2pdf(input_path, output_path)
        except IOError as error:
            raise
        except (ImportError, WindowsError) as error:
            logger.info("Failed to use MS Office | %s | Fallback to unoconv" % error)
            _libreoffice_converter(input_path, output_path)
    else:
        _libreoffice_converter(input_path, output_path)


def _convert_word2pdf(input_path, output_path):
    try:
        import pythoncom
        import comtypes
        import comtypes.client
    except ImportError as error:
        raise
    else:
        word = doc = None
        try:
            comtypes.CoInitialize()
            word = comtypes.client.CreateObject('Word.Application')
            doc = word.Documents.Open(input_path)
            doc.SaveAs(output_path, FileFormat=WD_FORMAT_PDF)
        except WindowsError as error:
            raise
        except comtypes.COMError as error:
            raise IOError(error)
        finally:
            doc and doc.Close()
            word and word.Quit()
            comtypes.CoUninitialize()


def _convert_powerpoint2pdf(input_path, output_path):
    try:
        import comtypes
        import comtypes.client
    except ImportError as error:
        raise
    else:
        powerpoint = slides = None
        try:
            comtypes.CoInitialize()
            powerpoint = comtypes.client.CreateObject('Powerpoint.Application')
            slides = powerpoint.Presentations.Open(input_path)
            slides.SaveAs(output_path, FileFormat=PP_FORMAT_PDF)
        except WindowsError as error:
            raise
        except comtypes.COMError as error:
            raise IOError(error)
        finally:
            slides and slides.Close()
            powerpoint and powerpoint.Quit()
            comtypes.CoUninitialize()


def _convert_excel2pdf(input_path, output_path):
    if os.name == 'nt':
        try:
            import comtypes
            import comtypes.client
        except ImportError as error:
            raise
        else:
            excel = wb = None
            try:
                comtypes.CoInitialize()
                excel = comtypes.client.CreateObject('Excel.Application')
                wb = excel.Workbooks.Open(input_path)
                wb.SaveAs(output_path, FileFormat=EX_FORMAT_PDF)
            except WindowsError as error:
                raise
            except comtypes.COMError as error:
                raise IOError(error)
            finally:
                wb and wb.Close()
                excel and excel.Quit()
                comtypes.CoUninitialize()
    else:
        # print input_path, output_path
        _libreoffice_converter(input_path, output_path)


def _libreoffice_converter(input_path, output_path, mime_type='pdf'):
    try:
        logger.exception(input_path)
        logger.exception(output_path)
        p = subprocess.Popen(['libreoffice', '--headless', "-env:UserInstallation=file:///tmp/LibreOffice_Conversion_${USER}", "-env:HOME=/tmp", '--convert-to', mime_type, '--outdir', "/tmp/xb_report", input_path], stdout=subprocess.PIPE)
        p.communicate()
        p.wait()
    except subprocess.CalledProcessError as error:
        raise
    except WindowsError as error:
        raise

# Convert to Docx

def convert_x2docx(input_path, output_path):
    _libreoffice_converter(input_path, output_path, 'docx')

def convert_x2doc(input_path, output_path):
    _libreoffice_converter(input_path, output_path, 'doc')

def convert_x2xlsx(input_path, output_path):
    _libreoffice_converter(input_path, output_path, 'xlsx')

def convert_x2xls(input_path, output_path):
    _libreoffice_converter(input_path, output_path, 'xls')

def convert_x2ods(input_path, output_path):
    _libreoffice_converter(input_path, output_path, 'ods')

def convert_x2odt(input_path, output_path):
    _libreoffice_converter(input_path, output_path, 'odt')

def convert_x2rtf(input_path, output_path):
    _libreoffice_converter(input_path, output_path, 'rtf')

__dispatch_pdf = {
    'application/msword': convert_document2pdf,
    'application/ms-word': convert_document2pdf,
    'application/vnd.ms-word.document.macroEnabled.12': convert_document2pdf,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': convert_document2pdf,
    'application/vnd.oasis.opendocument.text': convert_document2pdf,
    'application/mspowerpoint': convert_presentation2pdf,
    'application/ms-powerpoint': convert_presentation2pdf,
    'application/vnd.ms-powerpoint': convert_presentation2pdf,
    'application/vnd.ms-powerpoint.addin.macroEnabled.12': convert_presentation2pdf,
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': convert_presentation2pdf,
    'application/vnd.oasis.opendocument.presentation': convert_presentation2pdf,
    'application/msexcel': _convert_excel2pdf,
    'application/ms-excel': _convert_excel2pdf,
    'application/vnd.ms-excel.sheet.macroEnabled.12': _convert_excel2pdf,
    'application/vnd.ms-excel.sheet.binary.macroEnabled.12': _convert_excel2pdf,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': _convert_excel2pdf,
    'application/vnd.oasis.opendocument.spreadsheet': _convert_excel2pdf,
    'application/vnd.ms-excel': _convert_excel2pdf,
}

__dispatch_docx = {
    'application/vnd.oasis.opendocument.text': convert_x2docx,
}

__dispatch_doc = {
    'application/vnd.oasis.opendocument.text': convert_x2doc,
}

__dispatch_xlsx = {
    'application/vnd.oasis.opendocument.spreadsheet': convert_x2xlsx,
}

__dispatch_xls = {
    'application/vnd.oasis.opendocument.spreadsheet': convert_x2xls,
}

__dispatch_ods = {
    'application/msexcel': convert_x2ods,
    'application/ms-excel': convert_x2ods,
    'application/vnd.ms-excel.sheet.macroEnabled.12': convert_x2ods,
    'application/vnd.ms-excel.sheet.binary.macroEnabled.12': convert_x2ods,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': convert_x2ods,
    'application/vnd.oasis.opendocument.spreadsheet': convert_x2ods,
    'application/vnd.ms-excel': convert_x2ods,
}

__dispatch_odt = {
    'application/msword': convert_x2odt,
    'application/ms-word': convert_x2odt,
    'application/vnd.ms-word.document.macroEnabled.12': convert_x2odt,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': convert_x2odt,
    'application/vnd.oasis.opendocument.text': convert_x2odt,
} 

__dispatch_rtf = {
    'application/vnd.oasis.opendocument.text': convert_x2rtf,
    'application/msword': convert_x2rtf,
    'application/ms-word': convert_x2rtf,
    'application/vnd.ms-word.document.macroEnabled.12': convert_x2rtf,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': convert_x2rtf,
    'application/vnd.oasis.opendocument.text': convert_x2rtf,
}

# Move from 'xb_report_office/models/report.py'

def convert_file(input_file, mimetype, format_out):
    with closing(open(input_file, 'rb')) as file:
        extension = mimetypes.guess_extension(mimetype).replace('.', '')
        file_convert = file.read()
        if format_out == extension:
            return file_convert
        return convert_multiple_file(file_convert, mimetype, None, format='binary', mime_export=format_out)