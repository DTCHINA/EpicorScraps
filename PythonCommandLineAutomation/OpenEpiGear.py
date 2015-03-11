'''

Copyright 2013 Jeffrey Johnson

This file is part of OpenEpiGear.

    OpenEpiGear is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenEpiGear is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenEpiGear.  If not, see <http://www.gnu.org/licenses/>.

    Any product names, logos, brands, and other trademarks or images
    featured or referred to within the OpenEpiGear source are the
    property of their respective trademark holders. These trademark
    holders are not affiliated with the author, product, or any
    source code. They do not sponsor or endorse the author or OpenEpiGear.

'''


# coding=utf-8
__version__ = '0.9.1'
import os
import sys
import re  # regex
import datetime
import csv
import configparser
import time  # wibbly wobbly timey-wimey stuff.
import subprocess as sp
import logging.handlers
import depends.pypyodbc as pypyodbc

'''

EpicorDatabase Class

The one python class to do everything I want and need for Epicor scripting.
Branched off from my previous project on GitHub, "Epicor AutoPilot"

    note: If you use PEP8, I've changed my max_line_length to 140 characters, because 79 is stupid. Yeah I said it.
'''


def GetDay(delta=0):
    '''
    GetDay is in here because I use it all the time for naming
    backups & setting the Pilot/Test server company name to the restore date.
    Just makes things easier, ya'know?
    Returns a string in the format 'Jan1'
    '''
    deltaday = datetime.datetime.now() + datetime.timedelta(days=delta)
    return str(deltaday.strftime("%B")[:3]) + str(deltaday.day)


class Command(object):
    '''
    Command class to simplify running shell commands. Usage: Command(str).run()
    '''
    def __init__(self, command, cmd_timeout=2400):  # default timeout of 40 minutes.
        self.command = command
        self.cmd_timeout = cmd_timeout
        self.output = ""  # hacky hacky hack hack.

    def run(self, shell=True):
        start_time = time.time()
        process = sp.check_output(self.command, shell=shell, \
                                  stderr=sp.PIPE, timeout=self.cmd_timeout)
        self.output = process.decode(encoding='UTF-8')  # fracking unicode...
        self.ptime = time.time() - start_time
        self.timedresults = self.output + " Completed in " + \
        "{0:.2f}".format(self.ptime) + " Seconds" + "(" + \
        "{0:.0f}".format(self.ptime / 60) + " mins)"
        self.logtxt = str(self.output) + " : " + str(self.ptime)
        return self


class EpicorDatabase:

    # Disallow these from SQL commands against live db.
    FORBIDDEN_WORDS = \
    ['DELETE', 'UPDATE', 'TRUNCATE', 'INSERT', 'YOLO', 'SWAG']

    # Setup Config
    Config = configparser.RawConfigParser()
    Config.optionxform = str  # Required override to preserve case sensitivity.

    # Setup a logging instance, since we're doing database-y things here.
    log = logging.getLogger('EpicorData')
    hdlr = logging.handlers.RotatingFileHandler("EpicorDatabase.log",
                                                mode='a', maxBytes=(102400),
                                                backupCount=2, encoding=None,
                                                delay=0)  # 3x100k rotating log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(logging.INFO)

    # TODO: Each DB should be it's own .ini,
    #    ConfigParser supports reading multiple files at once
    #    and this would be much cleaner and more modular.
    def CreateDefaultConfig(self):
        '''
        Setup configuration for working with an Epicor (Progress Only) database.
        '''
        self.Config = configparser.RawConfigParser()
        self.Config.optionxform = str

        '''
        LIVE

        WARNING  -  WARNING  -  WARNING  -  WARNING  -  WARNING  -  WARNING

        If you don't plan on changing things in your live database, it
        might serve you to blank out most of this section in order to
        ABSOLUTELY ensure you never shut down or reconfig your live
        environment. I try to keep it from happening with checks, but
        for most uses I can't imagine needing to use this script to
        shut your live environment down. YOU HAVE BEEN WARNED.

        '''
        DefaultConfig = self.Config
        DefaultConfig.add_section('EpicorLive')
        DefaultConfig.set('EpicorLive', 'DSN', 'EpicorLive')
        DefaultConfig.set('EpicorLive', 'Live', 'YES')
        DefaultConfig.set('EpicorLive', 'DatabaseName', 'mfgsys')
        DefaultConfig.set('EpicorLive', 'Company Name', 'YOURCOMPANY')
        DefaultConfig.set('EpicorLive', 'EpicorDBDir', r'c:\epicor\epicor905\db')
        DefaultConfig.set('EpicorLive', 'AppServerURL', r'AppServerDC://localhost:9403')
        DefaultConfig.set('EpicorLive', 'MfgSysAppServerURL', r'AppServerDC://localhost:9401')
        DefaultConfig.set('EpicorLive', 'DBName', r'Epicor905')
        DefaultConfig.set('EpicorLive', 'AppName', r'Epicor905')
        DefaultConfig.set('EpicorLive', 'ProcName', r'Epicor905ProcessServer')
        DefaultConfig.set('EpicorLive', 'TaskName', r'Epicor905TaskAgent')
        DefaultConfig.set('EpicorLive', 'FileRootDir',
                   r'\\apollo\epicor\epicor905,C:\epicor\epicordata,\\apollo\epicor\epicor905\server')
        '''
        PILOT
        '''
        DefaultConfig.add_section('EpicorPilot')
        DefaultConfig.set('EpicorPilot', 'DSN', 'EpicorPilot')
        DefaultConfig.set('EpicorPilot', 'Live', 'NO')
        DefaultConfig.set('EpicorPilot', 'DatabaseName', 'mfgsys')
        DefaultConfig.set('EpicorPilot', 'Company Name', '--PILOT SERVER--')
        DefaultConfig.set('EpicorPilot', 'EpicorDBDir', r'c:\epicor\epicor905\pilot\db')
        DefaultConfig.set('EpicorPilot', 'AppServerURL', r'AppServerDC://localhost:9433')
        DefaultConfig.set('EpicorPilot', 'MfgSysAppServerURL', 'AppServerDC://localhost:9431')
        DefaultConfig.set('EpicorPilot', 'DBName', r'EpicorPilot905')
        DefaultConfig.set('EpicorPilot', 'AppName', r'EpicorPilot905')
        DefaultConfig.set('EpicorPilot', 'ProcName', 'EpicorPilot905ProcessServer')
        DefaultConfig.set('EpicorPilot', 'TaskName', r'EpicorPilot905TaskAgent')
        DefaultConfig.set('EpicorPilot', 'FileRootDir',
                   r'\\apollo\epicor\epicor905,C:\epicor\epicordataPilot,\\apollo\epicor\epicor905\server')
        '''
        TEST
        '''
        DefaultConfig.add_section('EpicorTest')
        DefaultConfig.set('EpicorTest', 'DSN', 'EpicorTest')
        DefaultConfig.set('EpicorTest', 'Live', 'NO')
        DefaultConfig.set('EpicorTest', 'DatabaseName', 'mfgsys')
        DefaultConfig.set('EpicorTest', 'Company Name', '--TEST SERVER--')
        DefaultConfig.set('EpicorTest', 'EpicorDBDir', r'c:\epicor\epicor905\test\db')
        DefaultConfig.set('EpicorTest', 'AppServerURL', r'AppServerDC://localhost:9423')
        DefaultConfig.set('EpicorTest', 'MfgSysAppServerURL', 'AppServerDC://localhost:9421')
        DefaultConfig.set('EpicorTest', 'DBName', r'EpicorTest905')
        DefaultConfig.set('EpicorTest', 'AppName', r'EpicorTest905')
        DefaultConfig.set('EpicorTest', 'ProcName', 'EpicorTest905ProcessServer')
        DefaultConfig.set('EpicorTest', 'TaskName', r'EpicorTest905TaskAgent')
        DefaultConfig.set('EpicorTest', 'FileRootDir',
                   r'\\apollo\epicor\epicor905,C:\epicor\epicordataTest,\\apollo\epicor\epicor905\server')
        '''
        OPENEDGE
        '''
        DefaultConfig.add_section('OpenEdge')
        DefaultConfig.set('OpenEdge', 'OpenEdgeDir', r'c:\epicor\oe102a')
        DefaultConfig.set('OpenEdge', 'ProBkup', r'\bin\probkup.bat')
        DefaultConfig.set('OpenEdge', 'ProRest', r'\bin\prorest.bat')
        DefaultConfig.set('OpenEdge', 'ASBMan', r'\bin\asbman.bat')
        DefaultConfig.set('OpenEdge', 'DBMan', r'\bin\dbman.bat')
        '''
        APPLICATION
        '''
        DefaultConfig.add_section('Application')
        DefaultConfig.set('Application', 'Sleepytime', '3')
        DefaultConfig.set('Application', 'Restore Wait', 600)  # 10mins
        DefaultConfig.set('Application', 'AppServer Timeout', 45)  # 45sec
        DefaultConfig.set('Application', 'DB Wait', 45)  # 45sec
        DefaultConfig.set('Application', 'TabTimeout', 240)  # 4min
        '''
        BACKUP
        '''
        DefaultConfig.add_section('Backup')
        DefaultConfig.set('Backup', 'EpicorBackupDir', r'c:\epicor\epicor905\db')
        cfgfile = open('OEG.ini', 'w')
        DefaultConfig.write(cfgfile)
        self.Config = DefaultConfig

    def __init__(self, db=None):
        Config = self.Config
        if (os.path.isfile('OEG.ini')):
            Config.read('OEG.ini')
            self.Config = Config
        else:
            self.log.warning("No Config file found. Creating new config with defaults.")
            self.CreateDefaultConfig()
        if (db != None):
            try:
                self.Select(db)
            except:
                raise

    def VerifyConfig(self, configname=None):
        '''
        Friendly helper method to catch path/misc errors in config ini.
        Returns big friendly string to tell you what you screwed up.
        '''
        # TODO: More config checks, namely validate DSN.
        if configname == None and self.Selected != None:
            configname = self.Selected()
        else:
            results = "Error: No Config Selected."
            return results

        results = 'EpicorDBDir is ' + ['NOT', ''][os.path.exists(self.Config.get(configname, 'EpicorDBDir')) == True] + \
        ' OK [' + self.Config.get(configname, 'EpicorDBDir') + "]\n"

        results += 'DatabaseName is ' + \
        ['NOT ', ''][os.path.isfile(self.Config.get(configname, 'EpicorDBDir') + '\\' + \
                                  self.Config.get(configname, 'DatabaseName') + '.db') == True] + \
                                  'OK [' + self.Config.get(configname, 'DatabaseName') + ']\n'

        if ('9401' in self.Config.get(configname, 'MfgSysAppServerURL') and self.Config.get(configname, 'Live') == False):
            results += "Warning: You have configured this database as NOT live, yet the MfgSys URL contains port 9401!\n"

        oepath = self.Config.get('OpenEdge', 'OpenEdgeDir')  # save some typing right hyah

        results += 'OpenEdgeDir is ' + ['NOT ', ''][os.path.exists(oepath) == True] + 'OK [' + oepath + ']\n'

        results += 'ProBkup path is ' + ['NOT ', ''][os.path.isfile(oepath + self.Config.get('OpenEdge', 'ProBkup')) == True] + \
        'OK [' + oepath + self.Config.get('OpenEdge', 'ProBkup') + ']\n'

        results += 'ProRest path is ' + ['NOT ', ''][os.path.isfile(oepath + self.Config.get('OpenEdge', 'ProRest')) == True] + \
        'OK [' + oepath + self.Config.get('OpenEdge', 'ProRest') + ']\n'

        results += 'ASBMan path is ' + ['NOT ', ''][os.path.isfile(oepath + self.Config.get('OpenEdge', 'ASBMan')) == True] + \
        'OK [' + oepath + self.Config.get('OpenEdge', 'ASBMan') + ']\n'

        results += 'DBMan path is ' + ['NOT ', ''][os.path.isfile(oepath + self.Config.get('OpenEdge', 'DBMan')) == True] + \
        'OK [' + oepath + self.Config.get('OpenEdge', 'DBMan') + ']\n'
        return results

    def AddDatabaseConfig(self):
        # TODO: AddDatabaseConfig -- I have no idea what I'm doing...
        pass

    def ModifyDatabaseConfig(self):
        # TODO: ModifyDatabaseConfig
        pass

    def DeleteDatabaseConfig(self):
        # TODO: DeleteDatabaseConfig
        pass

    def isRestricted(self):
        '''
        This is called whenever another def is about to modify
        an appserver or database. If the Selected() database is defined
        as Live in the Config, it raises a RuntimeError and quits.
        '''

        if (self.Config.get(self.database, 'Live') != 'NO'):
            self.log.error("I tried to edit my live environment!")
            raise RuntimeError("Can't do this on a live environment boss.")
            sys.exit("Did something stupid.")  # just to make sure we call it quits...

    def Select(self, database):
        if self.Config.has_section(database):
            self.database = database
        else:
            self.log.error("Tried selecting non-existing database.")
            raise RuntimeError('Tried selecting non-existing database.')

    def Selected(self):
        '''
        Returns selected database.
        '''
        return self.database

    def UpdateAgent(self):
        '''
        This is used for updating and stripping the pilot and test databases after a restore
         * Updates the SystemAgent to Selected() Config parameters
         * Turns off global alerts
         * Turns off chglog e-mails
         * Deletes scheduled tasks
        '''
        self.TestConnection()
        self.isRestricted()
        try:
            self.Sql('select name from pub.company')
            self.Sql("UPDATE pub.company set name = \'" + self.Config.get(self.database, 'Company Name') + "\'")
            self.Sql("UPDATE pub.SysAgent set AppServerURL = \'" + self.Config.get(self.database, 'AppServerURL') + "\'")
            self.Sql("UPDATE pub.SysAgent set MfgSysAppServerURL = \'" + self.Config.get(self.database, 'MfgSysAppServerURL') + "\'")
            self.Sql("UPDATE pub.SysAgent set FileRootDir = \'" + self.Config.get(self.database, 'FileRootDir') + "\'")

            # Remove Global Alerts / Task Scheduler
            self.Sql("UPDATE pub.glbalert set active=0 where active=1")
            self.Sql("UPDATE pub.chglogGA set SendEmail=0 where SendEmail=1")
            self.Sql("DELETE from pub.SysAgentTask")

            # Commit changes
            self.Commit()

        except pypyodbc.ProgrammingError as e:
            self.log.error("UpdateAgent: + " + e.args + " : " + e.value)
            raise

    def Connect(self, usr, pwd):
        self.conn = pypyodbc.connect('DSN=' + self.Config.get(self.database, 'DSN') + ';UID=' + usr + ';PWD=' + pwd + ';')
        self.log.info("Connecting to " + self.Config.get(self.database, 'DSN') + " as " + usr)
        return("Connecting to " + self.Config.get(self.database, 'DSN') + " as " + usr)

    def Sql(self, statement):
        '''
        Executes SQL statement on Selected() database.
        PLEASE NOTE: This method does NOT commit changes. YOU MUST CALL self.Commit()!!!
        Returns THREE results: raw rows, column names, dict format output
        For console output the simplest method of printing formatted results would be:
        x,y,z = Sql(expression)
        print(y)  # Headers
        print('\n'.join(z))

        Usage: Sql(statement)
        '''
        if any(self.FORBIDDEN_WORDS in statement for self.FORBIDDEN_WORDS in statement):
            self.isRestricted()  # No writing to the live db!

        self.log.info("Execute SQL: " + statement)
        try:
            self.cur = self.conn.cursor()
            self.cur.execute(statement)
        except Exception as e:
            self.log.error("SQL ERROR: " + e.args + " : " + e.value)

        # TODO: The following is a fairly lazy way of avoiding cursor errors if the statement doesn't return results:
        try:
            results = self.cur.fetchall()
            columns = self.cur.description
            # lol magic here
            # But really, this pretties things up so I can just grab the table and KA-POW: print ('\n'.join(table))
            #s = [[str(e.decode(encoding='UTF-8')) for e in row] for row in results]
            s = [[str(e) for e in row] for row in results]
            lens = [len(max(col, key=len)) for col in zip(*s)]
            fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
            table = [fmt.format(*row) for row in s]
            return results, columns, table
        except pypyodbc.ProgrammingError as e:
            return "Error", "No Results or SQL Execute Error."

    def Sql2CSV(self, sqlstring, outputfile):
        r, cols, table = self.Sql(sqlstring)

        # Cleanup for Unicode output
        rows = []
        columns = []
        items = []

        for i in r:  # TODO: This is messy, I know...
            for x in i:
                #items.append(x.decode('UTF-8'))
                items.append(str(x))
            rows.append(items)
            items = []

        for d in cols:
            #columns.append(str(d[0].decode('UTF-8')))
            columns.append(str(d[0]))

        with open(outputfile, 'w', newline='') as csvfile:
            dwriter = csv.writer(csvfile, dialect='excel')
            dwriter.writerow(columns)
            for line in rows:
                    dwriter.writerow(line)

    def Commit(self):
        self.isRestricted()  # TODO: Allow Commits to Live db; this is probably too restrictive
        try:
            self.conn.commit()
        except Exception as e:  # Well now I'm just getting lazy
            self.log.error("Commit Error: " + e.args + " : " + e.value)
            raise

    def Close(self):
        try:
            self.conn.close()
            self.log.info("Closing Connection.")
        except pypyodbc.ProgrammingError:
            self.log.error("Error Closing Connection. Did we already close?")
        except AttributeError:
            self.log.Error("Attribute Error. Did we connect with this database?")

    def Rollback(self):
        self.conn.rollback()

    def Restore(self, filename):
        '''
        ProRest the Selected() database with file. Args: filename
        '''
        # Initiate ProRest. Note the 'echo y' pipe is necessary to overwrite the existing db.
        # TODO: What if there isn't a db to overwrite?
        try:
            r = Command(
                        'echo y | ' +
                        self.Config.get(self.database, 'OpenEdgeDir') +
                        self.Config.get(self.database, 'ProRest') + " " +
                        self.Config.get(self.database, 'EpicorPilotDBDir') + '\\' +
                        self.Config.get(self.database, 'Database Name') + " " + filename,
                        self.Config.get('Application', 'Restore Wait')
                        ).run()
        except sp.TimeoutExpired as e:
            print("Command timed out." + str(e.args))
            self.log.error("TimeoutExpired: " + str(e.args))
            raise
        except sp.CalledProcessError as e:
            print("Command Error." + str(e.args))
            self.log.error("CalledProcessError: " + str(e.args))
            raise
        self.log.info(r.logtxt)

    def ShutdownAppServers(self):
        '''
        Shutdown ProcessServer, TaskServer, then AppServer of the Selected() db.
        '''
        self.isRestricted()
        try:
            r = Command(self.Config.get('OpenEdge', 'OpenEdgeDir') +
                        self.Config.get('OpenEdge', 'ASBMan') + " -name " +
                        self.Config.get(self.database, 'ProcName') + " -stop",
                        self.Config.getfloat('Application', 'AppServer Timeout')
                        ).run()  # Process Server

            self.log.info(r.logtxt)

            r = Command(self.Config.get('OpenEdge', 'OpenEdgeDir') +
                        self.Config.get('OpenEdge', 'ASBMan') + " -name " +
                        self.Config.get(self.database, 'TaskName') + " -stop",
                        self.Config.getfloat('Application', 'AppServer Timeout')
                        ).run()  # Task Server

            self.log.info(r.logtxt)

            r = Command(self.Config.get('OpenEdge', 'OpenEdgeDir') +
                        self.Config.get('OpenEdge', 'ASBMan') + " -name " +
                        self.Config.get(self.database, 'AppName') + " -stop",
                        self.Config.getfloat('Application', 'AppServer Timeout')
                        ).run()  # App Server

            self.log.info(r.logtxt)

        except sp.TimeoutExpired as e:
            print("Command timed out." + str(e.args))
            self.log.error("TimeoutExpired: " + str(e.args))
            raise
        except sp.CalledProcessError as e:
            print("Command Error." + str(e.args))
            self.log.error("CalledProcessError: " + str(e.args))
            raise  # the roof ya'll

    def ShutdownDB(self):
        '''
        Shutdown Selected() database.
        '''
        self.isRestricted()
        try:
            r = Command(self.Config.get('OpenEdge',
                                        'OpenEdgeDir') +
                        self.Config.get('OpenEdge', 'DBMan') + " -db " +
                        self.Config.get(self.database, 'DBName') + " -stop",
                        self.Config.getfloat('Application', 'DB Wait')).run()

            self.log.info(r.logtxt)

        except sp.TimeoutExpired as e:
            print("Command timed out." + str(e.args))
            self.log.error("TimeoutExpired: " + str(e.args))
            raise
        except sp.CalledProcessError as e:
            print("Command Error." + str(e.args))
            self.log.error("CalledProcessError: " + str(e.args))
            raise

    def StartupAppServers(self):
        '''
        Start TaskServer, ProcessServer, then AppServer of the Selected() db.
        '''
        try:
            r = Command(self.Config.get('OpenEdge', 'OpenEdgeDir') +
                        self.Config.get('OpenEdge', 'ASBMan') + " -name " +
                        self.Config.get(self.database, 'TaskName') + " -start",
                        self.Config.getfloat('Application', 'AppServer Timeout')
                        ).run()  # Task Server
            self.log.info(r.logtxt)

            r = Command(self.Config.get('OpenEdge', 'OpenEdgeDir') +
                        self.Config.get('OpenEdge', 'ASBMan') + " -name " +
                        self.Config.get(self.database, 'ProcName') + " -start",
                        self.Config.getfloat('Application', 'AppServer Timeout')
                        ).run()  # Process Server

            self.log.info(r.logtxt)

            r = Command(self.Config.get('OpenEdge', 'OpenEdgeDir') +
                        self.Config.get('OpenEdge', 'ASBMan') + " -name " +
                        self.Config.get(self.database, 'AppName') + " -start",
                        self.Config.getfloat('Application', 'AppServer Timeout')
                        ).run()  # App Server

            self.log.info(r.logtxt)

        except sp.TimeoutExpired as e:
            print("Command timed out." + str(e.args))
            self.log.error("TimeoutExpired: " + str(e.args))
            raise
        except sp.CalledProcessError as e:
            print("Command Error." + str(e.args))
            self.log.error("CalledProcessError: " + str(e.args))
            raise

    def StartupDB(self):
        '''
        Starts the Selected() database.
        '''
        try:
            self.log.info("Starting DB...")
            r = Command(self.Config.get('OpenEdge', 'OpenEdgeDir') +
                        self.Config.get('OpenEdge', 'DBMan') + " -db " +
                        self.Config.get(self.database, 'DBName') + " -start",
                        self.Config.getfloat('Application', 'DB Wait')).run()
            self.log.info(r.logtxt)

        except sp.TimeoutExpired as e:
            print("Command timed out." + str(e.args))
            self.log.error("TimeoutExpired: " + str(e.args))
            raise
        except sp.CalledProcessError as e:
            print("Command Error." + str(e.args))
            self.log.error("CalledProcessError: " + str(e.args))
            raise

    def TestConnection(self):
        '''
        Poll the db cursor. Will return pypyodbc.ProgrammingError(e) if not connected.
        '''
        try:
            self.conn.cursor()  # will raise exception on no active connection.
            return True
        except pypyodbc.ProgrammingError as e:
            self.log.error("TestConnection Error: " + e.args + " : " + e.value)
            raise

    def RawTabAnalysis(self, destination):
        '''
        Runs a tabanalysis on the selected database and outputs to <destination>
        '''
        Command(self.Config.get('OpenEdge', 'OpenEdgeDir') +
                r'\bin\proutil.bat ' +
                self.Config.get(self.database, 'EpicorDBDir') + '\\' +
                self.Config.get(self.database, 'DatabaseName') +
                ' -C tabanalys > ' + destination,
                float(self.Config.get('Application', 'TabTimeout'))
                ).run()

    def CleanTabAnalysis(self, sourcefile, destfile):
        '''
        Clean <sourcefile> tabanalysis and output to <destfile>. Creates a nice clean CSV.
        '''
        # None of this is pretty, but it works

        src = open(sourcefile, 'r')
        dst = open(destfile, 'w')
        dst.write(
                  '\"Tables\",\"Records\",\"Size(bytes)\",'
                  '\"Record Size Min\",\"Record Size Max\",'
                  '\"Record Size Mean\",\"Fragment Count\",'
                  '\"Fragment Factor\",\"Scatter Factor\"'
                  )
        linenum = 1
        for line in src:
                if (line.find("PUB") == -1 and linenum > 0):
                    linenum = linenum + 1
                    line = ''
                    if (linenum > 200):
                        print ("Doesn't seem to be a tabanalys")
                        break
                elif (line.find("-------") != -1 and linenum == -1):  # end of table data
                        break
                else:
                    linenum = -1
                    # My RegEx-Foo is weak, forgive me as I do this in baby steps:
                    line = re.sub(r'([\s*]{1,25})', ',', line.rstrip())  # strip spaces and replace with commas
                    line = re.sub(r',,', ',', line.rstrip())  # strip double commas
                    line = re.sub(r'PUB\.', '\nPUB.', line.rstrip())  # insert newlines before PUBs
                    line = re.sub(r'(?P<nm>[0-9])(?P<dot>[\.])(?P<nx>[0-9])(?P<sz>[BKMG])', '\g<nm>\g<nx>\g<sz>', line.rstrip())  # strip decimals from values, but NOT tables
                    line = re.sub(r'(?P<nb>[0-9])B', '', line.rstrip())  # strip B's
                    line = re.sub(r'(?P<nk>[0-9])K', '\g<nk>00', line.rstrip())  # strip K's and add 00 (250.4K becomes 250400)
                    line = re.sub(r'(?P<nM>[0-9])M', '\g<nM>00000', line.rstrip())  # strip M's and add 00000
                    line = re.sub(r'(?P<nG>[0-9])G', '\g<nG>00000000', line.rstrip())  # strip G's and add 00000000
                    dst.write(line)
        dst.close()

    def RunTabAnalysis(self, output):
        self.RawTabAnalysis("tabtmp.tmp")
        self.CleanTabAnalysis("tabtmp.tmp", output)

    def BackupVerify(self, backup):
        '''
        Verify backup against Selected() database
        Args: backup
        '''
        r = Command(self.Config.get('OpenEdge', 'OpenEdgeDir') +
        r'\bin\prorest.bat ' +
        self.Config.get(self.database, 'EpicorDBDir') + '\\' +
        self.Config.get(self.database, 'DatabaseName') +
        ' -vp ' + backup,
        ).run()
        if 'error' in r.logtxt:
            raise RuntimeError("Backup Verify Failed")

    def Backup(self, destination, online=False):
        '''
        Perform backup on Selected() database
        Args: destination, online=True/False
        '''
        procmd = \
        self.Config.get('OpenEdge', 'OpenEdgeDir') + \
        self.Config.get('OpenEdge', 'ProBkup') + \
        [' ', ' online '][online == True] + \
        self.Config.get(self.Selected(), 'EpicorDBDir') + '\\' + \
        self.Config.get(self.Selected(), 'DatabaseName') + \
        ' ' + destination

        # if(os.path.isfile(destination)):
        #    self.log.error("Cannot backup to " + destination + ", file exists already.")
        #    raise RuntimeError("File Exists, Cannot Overwrite!")
        #else:
        r = Command(procmd).run()
        return procmd, r

    def DailyBackup(self, dest, online):
        '''
        TODO: NOT IMPLEMENTED: Daily Backup Function for ease
        This is a copy / paste from my script EpicorAutoPilot, the Paths dict doesn't exist here and needs
        to be updated to use Config.
        '''
        return
        PreviousBak = EpicorDatabase.Paths['EpicorDB'] + "\\" + GetDay(-1) + ".bak"
        CopyBack = "copy " + PreviousBak + " " + EpicorDatabase.Paths['BackupDest'] + "\\" + self.GetDay(-1) + ".bak"
        DelLocal = "del " + PreviousBak

        DoBack = EpicorDatabase.Paths['OEBin'] + "\\probkup online " + \
        EpicorDatabase.Paths['EpicorDB'] + "\\" + "mfgsys " + \
        EpicorDatabase.Paths['EpicorDB'] + "\\" + GetDay() + ".bak"

        # debug purposes, comment out second line when ready to go.
        #IsEcho = ""
        IsEcho = "echo "

        try:
            # Copy yesterday to backup location.
            print("\nCopy to backup location...\n" + CopyBack)

            # Does yesterdays backup exist?
            if (not(os.path.isfile(EpicorDatabase.Paths['EpicorDB'] + "\\" +
                                   GetDay(-1) + ".bak"))):
                if (EpicorDatabase.Settings['FailOnPathError']):
                    raise IOError
                print("\t# WARNING: No backup from yesterday!")
                noprevious = True
            else:
                noprevious = False
                x = Command(IsEcho + CopyBack).run()
                return x
                #print(x.timedresults)

            # Remove local backup copy.
            if (noprevious):
                print("\tNo Previus backup to remove.")
            else:
                print ("\nDelete local backup...\n" + DelLocal)
                x = Command(IsEcho + DelLocal).run()
                print(x.timedresults)

            # Probkup mfgsys
            print("\nProBkup...\n" + DoBack)
            x = Command(IsEcho + DoBack).run()
            print(x.timedresults)

        except IOError:
            print("# ERROR: File Does Not Exist, Exiting.\n")
            raise SystemExit

        except Exception as e:
            raise SystemExit
