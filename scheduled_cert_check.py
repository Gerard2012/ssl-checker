##############################################################################################
# Modules
##############################################################################################

import csv
import time
from datetime import date
import schedule
import smtplib
from email.message import EmailMessage

from ssl_checker import SSLChecker
from email_settings import smtp_server, from_email, to_email, cc_email_1, cc_email_2


##############################################################################################
# Globals
##############################################################################################

## Create a list of target IP addresses from the csv.
with open('NetOpsCerts.csv') as f:
    targets = [row['IP Address'] for row in csv.DictReader(f)]


SSLChecker = SSLChecker()

expiring_certs = []

##############################################################################################
# Functions
##############################################################################################

def get_expiring_certs():

    args = {
        'hosts': targets
    }

    results = SSLChecker.show_result(SSLChecker.get_args(json_args=args))

    for key, value in results.items():
        if int(value['days_left']) < 28:
            with open('NetOpsCerts.csv') as f:
                for row in csv.DictReader(f):
                    if value['host'] == row['IP Address']:
                        if 'sslvpn' in row['Hostname'] or 'myallenovery' in row['Hostname']:
                            expiring_certs.append((row['Supported Service'], value['days_left']))
                        else:
                            expiring_certs.append((row['Hostname'], value['days_left']))


    return expiring_certs


##############################################################################################

def run_and_email():

    """
    Calls the get_expiring_certs() function, writes the results to a log file and to an email.

    """

    get_expiring_certs()

    today = date.today()

    msg = EmailMessage()

    if expiring_certs:

        results_file = f'netops_certs_{today}.txt'

        with open(results_file, 'a') as f:

            f.write('NET OPS CERTS EXPIRING < 28 DAYS\n')
            f.write('='*len('NET OPS CERTS EXPIRING < 28 DAYS'))
            f.write('\n')
            for elem in expiring_certs: f.write(str(elem[0]) + ': ' + str(elem[1]) + ' Days\n')
            f.write('\n\n')

        with open(results_file) as rf:
            msg.set_content(rf.read())

        msg['Subject'] = f'Weekly Net Ops Certs Check - {today}'
        msg['From'] = f'{from_email}'
        msg['To'] = f'{to_email}'
        msg['Cc'] = f'{cc_email_1}, {cc_email_2}'

        s = smtplib.SMTP(f'{smtp_server}')
        s.send_message(msg)
        s.quit()

    else:

        email_content = f"""
No certs due to expire as of {today}.
All is well. Have a fantastic day.
"""
        msg.set_content(email_content)

        msg['Subject'] = f'Weekly Net Ops Certs Check - {today}'
        msg['From'] = f'{from_email}'
        msg['To'] = f'{to_email}'
        msg['Cc'] = f'{cc_email_1}'

        s = smtplib.SMTP(f'{smtp_server}')
        s.send_message(msg)
        s.quit()


    del expiring_certs[:]


##############################################################################################

def scheduler(start_time):

    """
    Small function to schedule when the script will be run.

        : param start_time: The time of day the script will be run.

    """

    schedule.every().tuesday.at(start_time).do(run_and_email)

    while True:
        schedule.run_pending()
        time.sleep(1)


##############################################################################################
# Run
##############################################################################################

if __name__ == '__main__':
    
    scheduler('07:00')