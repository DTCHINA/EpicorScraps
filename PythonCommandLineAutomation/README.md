		-- OpenEpiGear --

Python class & command line tool to make Epicor automation much easier.



		*** SETUP & WARNINGS ***

This tool is limited for use by Progress installations. Sorry SQL users.

First off, you MUST review and modify the OEG.ini file to fit your environment! If
you don't have an OEG.ini or if it has become corrupted, simply run the command
line tool with the --resetdefaults parameter.

You must have ODBC drivers setup correctly. If you plan on using any of the appserver
or backup functions, OEG must be run on the machine containing your AppServer &
Progress installation.

Included in the EpicorDatabase class is a helper function, VerifyConfig(ConfigName)
which will check paths and make sure your .ini file is correct. You can also run
this from the commandline tool with OEG --config EpicorPilot --verify


		*** NOTES ON USE ***

If you want to avoid using your ODBC password with the command line tool, you can
create a text file with NO EXTENSION called "correcthorse". Put your password in
that file and SET FILE PERMISSIONS on it so only you and your task processes can
access it. Once you've done that you can omit the --password argument and the
OEG tool will pull your password from that by default. Use this at your own risk,
of course.

This was built for Python 3.3. It will not run in Python 2.7 without some editing.


		*** DEPENDENCIES ***

I've included and use the pypyodbc.py by Michele Petrazzo. It's a great library
for easy and native ODBC functions.


		*** FINALLY ***

I am not a programmer by trade. Some of this is sloppy, some if it is awfully
hack-ish. This tool was born out of several python scripts I've had to automate
things in my own environment and I thought others might get some use out of it,
so I cleaned it up and made it easier to port environments. Much of this was done
on my own time so the only compensation I get from it is knowing it's useful to you.
If you do end up using this, send me an email to let me know, I'd love to hear it.
(jeff.johnson@acti.aero)


----------------------------------------------------------------------------------
Example Script Snippet (OpenEpiGear.py):
----------------------------------------------------------------------------------

from getpass import getpass
from OpenEpiGear import EpicorDatabase


p = EpicorDatabase("EpicorPilot")
p.Connect(input("ODBC Username:"), getpass('ODBC Password:'))

if p.TestConnection():
    print('Connected!')
else:
    print('Not Connected! Are your username & password correct?')
    raise SystemExit

print(p.VerifyConfig())

r, table = p.Sql('select partnum, ium from pub.part where inactive=1')
print ('\n'.join(table))
p.Close()


----------------------------------------------------------------------------------
Example Commands
----------------------------------------------------------------------------------
For a full list of commands, use: OEG --help

OEG --config EpicorTest --user jeffj --verify

OEG --config EpicorTest --shutdownapps
OEG --config EpicorTest --shutdowndb

OEG --config EpicorTest --user jeffj --sql "SELECT PartNum, IUM, PUM FROM PUB.Part WHERE TypeCode = 'P'" --csv "Parts.csv"


----------------------------------------------------------------------------------
Useful Features (OpenEpiGear.py)
----------------------------------------------------------------------------------

EpicorDatabase.RunTabAnalysis(outputfile)
	This will run a Progress Table Analysis on the selected database and converts it
	to a formatted 	CSV file (outputfile). It strips the size indicators (B,M,GB,etc)
	and replaces them with the 	correct amount of zeros for easier sorting.

EpicorDatabase.ShutdownAppservers()
EpicorDatabase.StartupAppservers()
EpicorDatabase.ShutdownDB()
EpicorDatabase.StartupDB()
	Shuts down and starts up appservers/db, will wait as comes back online.


EpicorDatabase.UpdateAgent()
    Resets SystemAgent config to whatever is specified in the OEG.ini and clears the
    TaskList. Useful     for prepping a Pilot or Live database after a restore.


EpicorDatabase.Backup(destination, online=False)
	Starts a ProBkup on the selected database to (destination). Specifiy online=True if
	the db is online.
