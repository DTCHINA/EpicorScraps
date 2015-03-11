# coding=utf-8
import os
import sys
import argparse
from OpenEpiGear import EpicorDatabase

'''
Command Line Tool for OpenEpiGear.

'''
# If you want to avoid entering your password using this, you can create a file with no extension called 'correcthorse' in the same dir. put
# only your password in that file and set your permissions carefully on on it if you use it.
# https://xkcd.com/936/
if (os.path.isfile('correcthorse')):
    with open('correcthorse') as batterystaple:
        TMPPW = batterystaple.readline()
else:
    TMPPW = ''
parser = argparse.ArgumentParser(prog='OpenEpiGear', description='OpenEpiGear Command Line Tool')
group_auth = parser.add_argument_group("authentication")
group_backup = parser.add_argument_group("backup")
group_server = parser.add_argument_group("server")

parser.add_argument('--config', help='Loads Config Definition, specified in OEG.ini', metavar='')
parser.add_argument('--verify', help='Verify OEG.ini', action='store_true')
parser.add_argument('--dsntest', help='Tests A DSN Connection', action='store_true')
parser.add_argument('--sql', help='Execute SQL Command --sql \"SELECT <X> FROM <Y>\"', metavar='')
parser.add_argument('--csv', help='Output SQL results to CSV <out.csv>', metavar='')
parser.add_argument('--cleantab', help='Create a cleaned tab analysis for <tabfile.csv>', metavar='')
parser.add_argument('--resetdefaults', help='Create a new default OEG.ini', action='store_true')
# Not Implemented Yet
# parser.add_argument('--startserver', help='Start the ET Server')
# parser.add_argument('--listenport', help='Port for server to listen on.')

group_auth.add_argument('--user', help='Username ', metavar='')
group_auth.add_argument('--password', help='Password', metavar='', nargs='?', const=TMPPW, default=TMPPW)

group_backup.add_argument('--backup', help='Backup an Epicor database', metavar='')
group_backup.add_argument('--online', help='Used with --backup, performs backup while db is online', action='store_true')
group_backup.add_argument('--backupverify', help='Verify a backup', metavar='')

group_server.add_argument('--shutdownapps', help='Shutdown AppServers', action='store_true')
group_server.add_argument('--startupapps', help='Startup AppServers', action='store_true')
group_server.add_argument('--updateagent', help='Update Agent Config', action='store_true')
group_server.add_argument('--shutdowndb', help='Shutdown Database', action='store_true')
group_server.add_argument('--startupdb', help='Startup Database', action='store_true')
group_server.add_argument('--magicrestore', help='Easymode test db restoration: ' + \
                          'Shutdown the appservers and database of the connected database, ' + \
                          'then restore it to <backupfile>, then startup db and appservers\n', metavar='<backupfile>')

args = vars(parser.parse_args())


def verifyconfig(connect):  # TODO: Needs a proper check for True, to allow a verify without connection.
    '''
    connect = True if we need to test user and pass.
    '''
    if(args['config'] == None or (args['user'] == None and connect == True) or (args['password'] == None and connect == True)):
        print(
              ['', '--config Required\n'][args['config'] == None] +
              ['', '--user Required\n'][args['user'] == None and connect == True] +
              ['', '--password Required\n'][args['password'] == None and connect == True]
              )
        sys.exit()
    try:
        p = EpicorDatabase(args['config'])
        p.Connect(args['user'], args['password'])
        p.TestConnection()
        p.VerifyConfig(args['config'])
        p.Close()
    except:
        print('Connect Failure to ' + p.Selected() + '. Did you specify User/Pass?')
        sys.exit()

if args['resetdefaults']:
    p = EpicorDatabase()
    p.CreateDefaultConfig()
    print("Reset OEG.ini to default values.")

if args['magicrestore']:
    '''
    Shutdown appseervers, restore db, update agent, start appservers backup.
    '''
    if(args['config'] == None):
        print("--config Required")
        sys.exit()
    try:
        verifyconfig(True)
        p = EpicorDatabase(args['config'])
        os.path.isfile(args['magicrestore'])
        p.ShutdownAppServers()
        p.ShutdownDB()
        p.Restore(args['magicrestore'])
        p.UpdateAgent()
        p.StartupDB()
        p.StartupAppServers()
    except Exception as e:
        print(e)
        sys.exit()

if args['dsntest']:
    '''
    Test DSN Connection
    '''
    verifyconfig(True)
    print('Connect Success.')

if args['verify']:
    verifyconfig(False)
    try:
        p = EpicorDatabase(args['config'])
        print(p.VerifyConfig())
    except RuntimeError("Tried selecting non-existing database.") as e:
        print("Database not configured in Epicor.ini")
        sys.exit()

if args['updateagent']:
    '''
    Update Agent from Config
    '''
    if(args['config'] == None):
        print("--config Required")
        sys.exit()
    if(args['user'] == None or args['password'] == None):
        print('Username and Password required')
        sys.exit()
    p = EpicorDatabase(args['config'])
    p.Connect(args['user'], args['password'])
    p.UpdateAgent()
    p.Close()

if args['shutdownapps']:
    if(args['config'] == None):
        print("--config Required")
        sys.exit()
    try:
        p = EpicorDatabase(args['config'])
    except Exception as e:
        print(e)
        sys.exit()
    try:
        p.ShutdownAppServers()
    except Exception as e:
        print(e)
        sys.exit()

if args['startupapps']:
    if(args['config'] == None):
        print("--Config Required")
        sys.exit()
    try:
        p = EpicorDatabase(args['config'])
    except Exception as e:
        print(e)
        sys.exit()
    try:
        p.StartupAppServers()
    except Exception as e:
        print(e)
        raise
        sys.exit()

if args['startupdb']:
    if(args['config'] == None):
        print("--config Required")
        sys.exit()
    try:
        p = EpicorDatabase(args['config'])
    except Exception as e:
        print(e)
        raise  # TODO: debug
        sys.exit()
    try:
        p.StartupDB()
    except Exception as e:
        print(e)
        raise  # TODO: debug
        sys.exit()

if args['shutdowndb']:
    if(args['config'] == None):
        print("--config Required")
        sys.exit()
    try:
        p = EpicorDatabase(args['config'])
    except Exception as e:
        print(e)
        raise
        # TODO: debug
        sys.exit()
    try:
        p.ShutdownDB()
    except Exception as e:
        print(e)
        raise
        # TODO: debug
        sys.exit()

if args['sql']:
    '''
    SQL Command
    '''
    if(args['config'] == None):
        print("--config Required")
        sys.exit()
    if(args['user'] == None or args['password'] == None):
        print('Username and Password required')
        sys.exit()
    p = EpicorDatabase(args['config'])
    p.Connect(args['user'], args['password'])
    if (args['csv']):
        p.Sql2CSV(args['sql'], args['csv'])
    else:
        r, cols, table = p.Sql(args['sql'])
        p.Commit()
        print ('\n'.join(cols))
        print ('\n'.join(table))
    p.Close()

if args['backup']:
    '''
    Backup Database
    '''
    if(args['config'] == None):
        print("--config Required")
        sys.exit()
    if args['online']:
        p = EpicorDatabase(args['config'])
        cm, r = p.Backup(args['backup'], True)
    else:
        p = EpicorDatabase(args['config'])
        cm, r = p.Backup(args['backup'], False)

    print(cm + '\n' + r.output)

if args['backupverify']:
    '''
    Backup Verify
    '''
    if(args['config'] == None):
        print("--config Required")
        sys.exit()
    p = EpicorDatabase(args['config'])
    p.BackupVerify(args['backupverify'])


if args['cleantab']:
    '''
    Run Table Analysis
    '''
    if(args['config'] == None):
        print("--config Required")
        sys.exit()
    p = EpicorDatabase(args['config'])
    p.RunTabAnalysis(args['cleantab'])
