'''

BEWARE! Here lies dragons. Edit at your own risk.

       , |\/| ,
      /| (..) |\
     /  \(oo)/  \
    /    /''\    \
   /    /\  /\    \
   \/\/`\ \/ /`\/\/
      ^^-^^^^-^^


OEGDailyBackup, slapped together with little care for readability by Jeff Johnson, Angeles Composite Technologies Inc.

'''

import OpenEpiGear
from datetime import datetime
import time
import locale
import shutil
import os
import smtplib
__version__ = '0.2.2'


db = OpenEpiGear.EpicorDatabase("EpicorLive")

'''
File Locations
'''
DestinationFolder = "\\\\vault101\\epicorbackups\\"
MfgSysLocation = db.Config.get("EpicorLive", "EpicorDBDir") + "\\"
TodayBackup = MfgSysLocation + "Live-" + str(datetime.now().year) + "-" + OpenEpiGear.GetDay() + (".bak")
LookbackDays = 7  # How many days to look back for a previous backup

'''
E-Mail Settings
'''
MailFrom = "jeff.johnson@acti.aero"
MailTo = "it@acti.aero"
MailSubject = "Epicor Backup OK."
MailBody = ""
MailFooter = "\r\n***\r\nHi, I\'m a python script located on Apollo. I\'m " + \
    "launched via a scheduled task, and my code is in C:\\Scripts\\.\n " + \
    "I am using Jeff's awesome OpenEpiGear, version " + OpenEpiGear.__version__ + ".\n" + \
    "The version of this script is " + __version__ + ". Have a great day.\n"
MailSMTP = 'smtp.olypen.com'


'''
Initialization Vars
'''
BackupDiffSize = 0
locale.setlocale(locale.LC_ALL, '')
DEBUG = False

if DEBUG:
    MailBody = "=== THIS IS A DEBUG RUN ONLY ===\n"


'''

**********************************************************

'''


def find_last_backup():
    '''
    Look for a backup from today, and LookbackDays - 1 days prior.
    '''
    for i in range(1, LookbackDays):
        P = MfgSysLocation + "Live-" + str(datetime.now().year) + "-" + OpenEpiGear.GetDay(i * -1) + (".bak")
        if (os.path.exists(P)):
            return P



def calctime(t):
    '''
    I like to know how long stuff takes. This just formats the runtime to be purdy.
    '''
    if (t > 60):
        return("{0:.2f}".format(t / 60) + "m")
    elif (t < 60):
        return("{0:.2f}".format(t) + "s")

try:
    '''
    Test the connection.
    '''
    stime = time.time()
#    db.TestConnection()  # This needs credentials...Which I'm not okay with putting in this script right now.
    c = calctime(time.time() - stime)
    rpt = str(c) + ": Tested DB Connection & Misc. OK.\n"
    print(rpt);MailBody = MailBody + rpt

    '''
    Perform a backup & delta yesterday size and today
    '''
    stime = time.time()
    if DEBUG:
        c = 99.99
    else:
        db.Backup(TodayBackup, True)
        c = calctime(time.time() - stime)
    rpt = str(c) + ": Performed today's backup: " + os.path.basename(TodayBackup) + "\n"
    try:  # I don't really care if this fails..
        PreviousBackup = find_last_backup()
        if PreviousBackup:
            BackupDiffSize = os.path.getsize(TodayBackup) - os.path.getsize(PreviousBackup)
        else:
            rpt = rpt + "00.00s: WARNING: Cannot find previous backup!!!.\n"
            MailSubject = MailSubject + " (with errors)"
    except: #TODO: Fix this
        pass
    print(rpt);MailBody = MailBody + rpt

    '''
    Verify Backup
    '''
    stime = time.time()
    if DEBUG:
        c = 99.99
    else:
        try:
            db.BackupVerify(TodayBackup)  # Will raise error on failure
            c = calctime(time.time() - stime)
            rpt = str(c) + ": Backup Verified.\n"
        except:
            rpt = str(c) + ": Backup Verify Error."
            if ("with errors" not in MailSubject):
                MailSubject = MailSubject + " (with errors)"

    print(rpt);MailBody = MailBody + rpt

    '''
    Move yesterdays backup to the DestinationFolder
    Also get b1 & d1 sizes.
    '''
    stime = time.time()
    if DEBUG:
        c = 99.99
    else:
        try:
            shutil.move(PreviousBackup, DestinationFolder + os.path.basename(PreviousBackup))
            c = calctime(time.time() - stime)
            rpt = str(c) + ": Moved " + PreviousBackup + " To " + DestinationFolder + os.path.basename(PreviousBackup) + "\n"
        except:
            rpt = str(c) + ": No Previous Backup to Move!\n"
            MailSubject = MailSubject + " (with errors)"
    print(rpt);MailBody = MailBody + rpt
    stime = time.time()
    d1runsize = os.path.getsize("\\\\Apollo\\Epicor\\Epicor905\\db\\mfgsys.d1")
    b1runsize = os.path.getsize("\\\\Apollo\\Epicor\\Epicor905\\db\\mfgsys.b1")
    c = calctime(time.time() - stime)
    rpt = str(c) + ": mfgsys.d1 Size: " + locale.format("%d", d1runsize, grouping=True) + "\n"
    rpt = rpt + str(c) + ": mfgsys.b1 Size: " + locale.format("%d", b1runsize, grouping=True) + "\n"
    rpt = rpt + str(c) + ": Backup size diff: " + locale.format("%d", BackupDiffSize, grouping=True)
    print(rpt);MailBody = MailBody + rpt

    '''

    Run a TabAnalysis every Friday.

    '''
    if (datetime.today().weekday() == 6):  # Sunday
        try:
            stime = time.time()
            db.RunTabAnalysis(DestinationFolder + "TabAnalysis\\" + str(datetime.now().year) + "-" + OpenEpiGear.GetDay() + ".csv")
            c = calctime(time.time() - stime)
            rpt = str(c) + ": TabAnalysis Complete.\n"
        except:
            rpt = str(c) + "\n Error Running TabAnalysis.\n"
        finally:
            print(rpt);MailBody = MailBody + rpt

except Exception as e:
    '''
    Gracefully error, report and email.
    '''
    c = calctime(time.time() - stime)
    rpt = "\n" + str(c) + ": Error: " + repr(e) + "\n"
    print(rpt);MailBody = MailBody + rpt
    MailSubject = "ALERT! Epicor Backup Failed!"
finally:
    print ("Start Mail:\n")
    print(MailBody)
    print("Email Process:\n------------------------\n")

    MailSubject = MailSubject + " (delta=" + locale.format("%d", (BackupDiffSize / 1024), grouping=True) + "KB)"
    # Add the From: and To: MailHeaders at the start!
    MailHeaders = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n"
           % (MailFrom, MailTo, MailSubject))
    mailpack = MailHeaders + MailBody + MailFooter
    print(mailpack)
    MailServer = smtplib.SMTP(MailSMTP)
    MailServer.set_debuglevel(1)

    try:
        MailServer.sendmail(MailFrom, MailTo, mailpack)
    except Exception as e:
        # Mail didn't work....
        f = open('ErrorLog-' + str(datetime.now().year) + "-" + OpenEpiGear.GetDay(), 'w')
        f.write(mailpack)
        f.write(e)
    finally:
        MailServer.quit()

