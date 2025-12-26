# XBOSS REPORT

### Docker Debian 9:
Libreoffice 24.8.4:

```
RUN apt-get update -y && \
    apt-get install -y wget libxinerama1 libdbus-1-3 libglib2.0-0 libcups2 libsm6 openjdk-8-jre && \
    cd /tmp/ && \
    wget http://download.documentfoundation.org/libreoffice/stable/24.8.4/deb/x86_64/LibreOffice_24.8.4_Linux_x86-64_deb.tar.gz && \
    tar xvf LibreOffice_24.8.4_Linux_x86-64_deb.tar.gz && \
    cd LibreOffice_24.8.4.2_Linux_x86-64_deb/DEBS/ && \
    dpkg -i *.deb && \
    ln -s /usr/local/bin/libreoffice24.8 /usr/local/bin/libreoffice && \
    rm -rf /tmp/LibreOffice_24.8.4.2_Linux_x86-64_deb*
```

Libreoffice 6.2.5:

```
RUN apt-get update -y && \
apt-get install wget -y && \
cd /tmp/ && \
wget https://mirror.freedif.org/TDF/libreoffice/stable/6.2.5/deb/x86_64/LibreOffice_6.2.5_Linux_x86-64_deb.tar.gz && \
tar xvf LibreOffice_6.2.5_Linux_x86-64_deb.tar.gz && \
cd ./LibreOffice_6.2.5.2_Linux_x86-64_deb/DEBS/ && \
dpkg -i *.deb && \
apt-get install libxinerama1 -y && \
apt-get install libdbus-1-3 -y && \
apt-get install libglib2.0-0 -y && \
apt-get install libcups2 -y && \
apt-get install libsm6 -y && \
echo "deb http://ftp.debian.org/debian stretch main" | tee -a /etc/apt/sources.list  && \
apt-get update -y && \
apt-get install openjdk-8-jre -y && \
ln -s /usr/local/bin/libreoffice6.2 /usr/local/bin/libreoffice
```

Fonts
```
RUN apt-get update && \
apt-get install wget -y && \
cd /tmp/ && \
wget http://ftp.debian.org/debian/pool/contrib/m/msttcorefonts/ttf-mscorefonts-installer_3.6_all.deb && \
apt install ./ttf-mscorefonts-installer_3.6_all.deb -y
```

QR code
```
from odoo.addons.xb_report.models import qr_code_mail_merge
from io import BytesIO
import base64


@api.model
def get_data_export(self):
    result = super(HrRecruitmentRequest, self).get_data_export()
    if self.job_id:
        ...
        file_content = BytesIO(base64.decodestring(self.env.user.company_id.request_template_id.file))
        qr_code = qr_code_mail_merge.XBQRCode(2.2, 0.5, 'XBOSS Test', file_content)
        #         box_size	border	string to QR	Template
        #XBQRCode(2.2,		0.5, 	'XBOSS Test',	file_content)
        new_file_bytes_io = qr_code.write_file()

    return result
```