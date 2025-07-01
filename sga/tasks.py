# -*- coding: latin-1 -*-
import cgi
from random import choice
import re
import threading
from django.core.mail.message import EmailMessage
from django.template.context import Context
from django.template.loader import get_template
from settings import EMAIL_HOST_USER
import string


class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list):
        self.subject = subject
        self.recipient_list = recipient_list
        self.html_content = html_content
        threading.Thread.__init__(self)

    def run (self):
        msg = EmailMessage(self.subject, self.html_content, EMAIL_HOST_USER, self.recipient_list)
        msg.content_subtype = "html"
        msg.send()

def send_html_mail(subject, html_template, data, recipient_list):

    template = get_template(html_template)
    # d = Context(data)
    html_content = template.render(data)

    EmailThread(subject, html_content, recipient_list).start()


re_string = re.compile(r'(?P<htmlchars>[<&>])|(?P<space>^[ \t]+)|(?P<lineend>\r\n|\r|\n)|(?P<protocal>(^|\s)((http|ftp)://.*?))(\s|$)', re.S|re.M|re.I)
def plaintext2html(text, tabstop=4):
    def do_sub(m):
        c = m.groupdict()
        if c['htmlchars']:
            return cgi.escape(c['htmlchars'])
        if c['lineend']:
            return '<br>'
        elif c['space']:
            t = m.group().replace('\t', '&nbsp;'*tabstop)
            t = t.replace(' ', '&nbsp;')
            return t
        elif c['space'] == '\t':
            return ' '*tabstop
        else:
            url = m.group('protocal')
            if url.startswith(' '):
                prefix = ' '
                url = url[1:]
            else:
                prefix = ''
            last = m.groups()[-1]
            if last in ['\n', '\r', '\r\n']:
                last = '<br>'
            return '%s<a href="%s">%s</a>%s' % (prefix, url, url, last)
    return re.sub(re_string, do_sub, text)



def GenPasswd():
    chars = string.ascii_letters + string.digits
    newpasswd = ''
    for i in range(6):
        newpasswd = newpasswd + choice(chars)
    return newpasswd

def gen_passwd(length=6, chars=string.ascii_letters + string.digits):
    return ''.join([choice(chars) for i in range(length)])


