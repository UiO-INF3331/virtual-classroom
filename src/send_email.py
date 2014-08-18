from __future__ import print_function
from getpass import getpass
from smtplib import SMTP
from docutils import core
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sys import exit

# Python3 and 2 compatible
try: input = raw_input
except NameError: pass


class Email():

    def __init__(self):
        self.username = input("\nFor Gmail\nEmail address: ")
        self.password = getpass("Password:")
        try:
            server = SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login(self.username, self.password)
            server.quit()
        except:
            print('Username or password is wrong (Gmail), please try again!')
            exit(1)

    def get_text(self, filename):
        file = open(filename, 'r')
        text = file.read()
        file.close()
        return text
    
    def rst_to_html(self, text):
        parts = core.publish_parts(source=text, writer_name='html')
        return parts['body_pre_docinfo']+parts['fragment']

    def new_student(self, student):
        text = self.get_text('message_new_student.rst')

        # Variables for the email
        recipient = student.email
        email_var = {}
        email_var['name'] = student.name.split(' ')[0]
        email_var['repo_name'] = student.repo_name
        email_var['repo_adress'] = 'https://github.com/%s/%s' % \
                                        (student.org, student.repo_name)

        # Compose message
        text = self.get_text('message_new_student.rst')
        text = text % email_var
        text = self.rst_to_html(text)
   
        # Compose email       
        msg = MIMEMultipart()
        msg['Subject']  = 'New repository'
        msg['To'] = recipient
        msg['From'] = self.username
        body_text = MIMEText(text, 'html')
        msg.attach(body_text)

        self.send(msg, recipient)

    def new_group(self, group, team_name, correcting):

        # Variables for the email
        email_var = {}
        get_repos = ""
        correcting_names = ""
        for student in correcting:
            correcting_names += " "*4 + "* %s\n" % student.name
            get_repos += ' '*4 + 'git clone https://github.com/%s/%s\n' % \
                                       (student.org, student.repo_name)

        email_var['get_repos'] = get_repos
        email_var['correcting_names'] = correcting_names
        email_var['team_name'] = team_name

        for student in group:
            recipient = student.email
            email_var['name'] = student.name.split(' ')[0]
            rest_of_group = [s.name for s in group if s.name != student.name]
            email_var['group_names'] = ", ".join(rest_of_group[:-1]) + " and " + \
                                       rest_of_group[-1]

            # Compose message
            text = self.get_text('message_collaboration.rst')
            text = text % email_var
            text = self.rst_to_html(text).encode('utf-8') # ae, o, aa support

            # Compose email       
            msg = MIMEMultipart()
            msg['Subject']  = 'New group'
            msg['To'] = recipient
            msg['From'] = self.username
            body_text = MIMEText(text, 'html', 'utf-8')
            msg.attach(body_text)

            self.send(msg, recipient)

    def send(self, msg, recipients):

        # Send email
        server = SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(self.username, self.password)
        failed_deliveries = server.sendmail(self.username, recipients, msg.as_string())
        if failed_deliveries:
            print('Could not reach these addresses:', failed_deliveries)
        else:
            print('Email successfully sent to %s' % recipients)
        server.quit()