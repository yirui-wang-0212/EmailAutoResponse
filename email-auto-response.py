# -*- coding: utf-8 -*-

from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from HTMLParser import HTMLParser

from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr

import time
import smtplib
import poplib

# 输入邮件地址, 口令和POP3服务器地址:

email = input('Email: ')
password = input('Password: ')
pop3_server = input('POP3 server: ')
smtp_server = input('smtp server: ')


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


# 去除html标签
def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


# 格式化一个邮件地址
def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def send_mail(to_addr):
    # from_addr = input('From: ')
    # password = input('Password: ')
    # to_addr = input('To: ')
    # smtp_server = input('SMTP server: ')

    msg = MIMEText('您好，您的邮件已收到！', 'plain', 'utf-8')
    msg['From'] = _format_addr('王依睿 <%s>' % email)
    msg['To'] = _format_addr('<%s>' % to_addr)
    msg['Subject'] = Header('来自王依睿的自动回复', 'utf-8').encode()

    server = smtplib.SMTP(smtp_server, 25)
    server.set_debuglevel(1)
    server.login(email, password)
    server.sendmail(email, [to_addr], msg.as_string())
    # server.quit()


def guess_charset(msg):
    charset = msg.get_charset()
    if charset is None:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
    return charset


def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value


def print_info(msg, indent=0):
    subject_value = None
    from_value = None
    content = None

    if indent == 0:
        for header in ['From', 'To', 'Subject']:
            value = msg.get(header, '')
            if value:
                if header == 'Subject':
                    value = decode_str(value)
                    subject_value = value;
                else:
                    hdr, addr = parseaddr(value)
                    name = decode_str(hdr)
                    value = u'%s <%s>' % (name, addr)
                    if header == 'From':
                        from_value = value

        print('%s%s: %s' % ('  ' * indent, header, value))

    if (msg.is_multipart()):
        parts = msg.get_payload()
        for n, part in enumerate(parts):
            print('%spart %s' % ('  ' * indent, n))
            print('%s--------------------' % ('  ' * indent))
            print_info(part, indent + 1)
    else:
        content_type = msg.get_content_type()
        if content_type == 'text/plain' or content_type == 'text/html':
            content = msg.get_payload(decode = True)
            charset = guess_charset(msg)
            if charset:
                content = content.decode(charset)
                if content_type == 'text/html':
                    content = strip_tags(content)
            print('%sText: %s' % ('  ' * indent, content + '...'))
        else:
            print('%sAttachment: %s' % ('  ' * indent, content_type))
    return subject_value, from_value, content

precontent = None
preaddress = None
while (1):
    # 连接到POP3服务器:
    server = poplib.POP3(pop3_server)
    # 可以打开或关闭调试信息:
    server.set_debuglevel(1)
    # 可选:打印POP3服务器的欢迎文字:
    print(server.getwelcome().decode('utf-8'))
    # 身份认证:
    server.user(email)
    server.pass_(password)
    # stat()返回邮件数量和占用空间:
    print('Messages: %s. Size: %s' % server.stat())
    # list()返回所有邮件的编号:
    resp, mails, octets = server.list()
    # 可以查看返回的列表类似[b'1 82923', b'2 2184', ...]
    print(mails)
    # 获取最新一封邮件, 注意索引号从1开始:
    index = len(mails)
    resp, lines, octets = server.retr(index)
    # lines存储了邮件的原始文本的每一行,
    # 可以获得整个邮件的原始文本:
    msg_content = b'\r\n'.join(lines).decode('utf-8')
    # 稍后解析出邮件:
    msg = Parser().parsestr(msg_content)
    print_info(msg)

    # 发邮件
    subject_value, from_value, content = print_info(msg)
    start = from_value.find('<')
    end = from_value.find('>')
    address = from_value[start + 1: end]
    address = address.encode('utf-8')
    # 判断是否是新邮件
    if precontent != content or preaddress != address:
        send_mail(address)

    precontent = content
    preaddress = address

    # 可以根据邮件索引号直接从服务器删除邮件:
    # server.dele(index)
    # 关闭连接:
    server.quit()
    time.sleep(20)
