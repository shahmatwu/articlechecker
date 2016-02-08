""" Provide articlechecker with an interactive shell. """
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cmd
import pageanalytics
import applelookup
import articlevisits
import applistscraper
import os
from datetime import datetime

class CheckerShell(cmd.Cmd):
    INTRO = "\n\033[95mWelcome to the appPicker Article Checker utility.\nType help or ? to list commands.\n\nTYPE 'start' to begin.\n\033[0m"
    PROMPT = "\033[95mChecker> \033[0m"
    MENU_PROMPT = ">> "

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = self.PROMPT
        self.intro = self.INTRO
        self.scrapelists_inputcsv = 'applists.csv'
        self.scrapelistsinputhasheaders = True
        self.scrapelist_outputcsv = 'scrapelists_report.csv'
        self.lookupapple_inputcsv = None # input to lookupapple - by default will be output from scrapelists but we'll ask the user
        self.lookupappleinputhasheaders = True
        self.lookupapple_outputcsv = 'applelookup_report.csv'
        self.googlestats_inputcsv = None
        self.googlestatsinputhasheaders = True
        self.googlestats_outputcsv = 'googlestats_report.csv'
        self.googlestats_fromdate = None
        self.googlestats_todate = None

    # -------- article checker commands --------
    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        print(self._hist)

    def do_help(self, args):
        """Get help on commands\n\n 'help' or '?' with no arguments prints a list of commands for which help is available\n\n 'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion
        self._hist    = []      ## No history yet
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print(" Exiting...")

# ---------- MY COMMANDS ------------
    def do_start(self, line):
        go = 1
        while go:
            go = self.managemenu()

    def getvalidselection(self, maxmenunum):
        """Keep prompting user for valid menu selection. maxmenunum does not include 'x' ('Exit')"""
        answer = input(self.MENU_PROMPT)
        while not answer or (answer not in [str(i) for i in range(0, maxmenunum)] and answer.lower() != 'x'):
            print("Please enter a single number up to {} or 'x' to exit".format(maxmenunum))
            answer = input(self.MENU_PROMPT)
        return answer

    def do_scrapelists(self, line):
        """ 
Scrapes the applists listed in an input CSV that you specify. The scraper produces an output report (also a CSV) containing all the apps and iTunes links found in the specified applists.

Some of the other commands allow you to use this output report as their input. For example, lookupapple can check iTunes for all the apps in the output report.
 
The input CSV must have at least these 4 columns (in the first 4 places):-
    article_id: required
    article_type: must be '2' for applists
    published_at: optional, copied into the output report
    slug: optional - the system reads this value but does not do anything with it

NOTE: If your first 4 columns do not contain these values, then the script may fail or produce nonsensical results. """
        self.scrapelists()

    def do_lookupapple(self, line):
        """
Look up the Apple Search API for each app listed in an input CSV that you specify. The input CSV can be the same output report from scrapelists.

The input CSV must have at least these 5 columns (in the first 5 places):-
    article_id: simply copied into the output report so this can be any value
    article_url: simply copied into the output report so this can be any value
    published_at: simply copied into the output report so this can be any value
    app_id: required - this is used to look up iTunes
    itunes_link: this is the link found on the article but is ignored here so can be any value"""
        self.lookupapple()

    def do_singlescrapelist(self, line):
        """ 
Scrapes a single applist for an article ID that you specify. The scraper produces the same output report that scrapelists() (menu item #1) does, containing all the apps and iTunes links found.

Some of the other commands allow you to use this output report as their input. For example, lookupapple can check iTunes for all the apps in the output report."""
        self.singlescrapelist()

    def do_googlestats(self, line):
        """ 
Look up Google Analytics stats for articles listed in an input CSV that you specify. The input CSV can be the same one as used for menu item #1, except that ANY article type is supported here. Type 'help scrapelists' for input file requirements.

The report is saved to a CSV."""
        self.googlestats()

# ---------- END MY COMMANDS ------------

# ---------- MY PRIVATE FUNCTIONS ------------
    def managemenu(self):
        """Present a menu of commands"""
        sels = {'1':self.scrapelists, '2':self.singlescrapelist, '3':self.lookupapple, '4':self.googlestats}

        print("\033[0m\n===== MAIN MENU =====")
        print("\033[0m\nWhat would you like to do?\n")
        print("1. Scrape all the apps off a list of applists. This also gets the published iTunes links.")
        print("2. Get all the apps off a single article by article ID")
        print("3. Look up iTunes for a list of apps (prerequires output from #1 or #2")
        print("4. Look up Google Analytics for a list of articles (any type)")
        print("X. eXit")
        print("\nPlease make your selection now.\n")
        sel = self.getvalidselection(5)
        if sel == 'x':
            return 0
        else:
            sels[sel]()
            return 1


    def scrapelists(self):

        inputcsv = self.scrapelists_inputcsv
        hasHeaders = self.scrapelistsinputhasheaders
        outputcsv = self.scrapelist_outputcsv

        self.showutilitywelcome('the applists scraper utility')
        inputcsv = self.getinputfilename(inputcsv)
        hasHeaders = self.getinputfilehasheaders(hasHeaders)
        outputcsv = self.getoutputfilename(outputcsv)
        answer = self.confirmIPOsettings(inputcsv, hasHeaders, outputcsv, 'N/A', 'N/A')

        if answer[0].lower() == 'n':
            return

        # remember the settings as the new defaults
        self.scrapelists_inputcsv = inputcsv
        self.scrapelistsinputhasheaders = hasHeaders
        self.scrapelist_outputcsv = outputcsv

        if not self.checkfilelocn(inputcsv):
            print("\n \033[93mInput file not found: {}\033[0m".format(inputcsv))
            print("\n Exiting now. Maybe the file is in a different folder? e.g. C:\\My Work Folder\\applists.csv")
            print(" If you don't specify the folder, I assume you meant: {}\033[0m".format(os.getcwd()))
            input(" Please press ENTER to continue... ")
            return

        if self.checkfilelocn(outputcsv):
            print(" \033[93mWarning: output file ({}) already exists!".format(outputcsv))
            answer = input(" Overwrite [y/n]?\033[96m ")
            while not answer or answer[0].lower() not in ('y', 'n'):
                answer = input(" \033[93mOverwrite (y/n)?\033[96m ")
            if answer[0].lower() == 'n': return
            print("\033[0m")
        #try:
        #    # finally, call the scraper!
        #    applistscraper.main(inputcsv, hasHeaders, outputcsv)

        #except Exception as e:
        #    print(e.__class__, ":", e)
        
        applistscraper.main(inputcsv, hasHeaders, outputcsv)

        print("Done! :)")
        print("Reminder: your report is in {}".format(outputcsv))
        return

    def lookupapple(self):
        if self.lookupapple_inputcsv:
            inputcsv = self.lookupapple_inputcsv
        else:
            inputcsv = self.scrapelist_outputcsv
        hasHeaders = self.lookupappleinputhasheaders
        outputcsv = self.lookupapple_outputcsv

        self.showutilitywelcome('the Apple iTunes lookup utility')
        inputcsv = self.getinputfilename(inputcsv)
        hasHeaders = self.getinputfilehasheaders(hasHeaders)
        outputcsv = self.getoutputfilename(outputcsv)
        answer = self.confirmIPOsettings(inputcsv, hasHeaders, outputcsv, 'N/A', 'N/A')

        if answer[0].lower() == 'n':
            return

        # remember the settings as the new defaults
        self.lookupapple_inputcsv = inputcsv
        self.lookupappleinputhasheaders = hasHeaders
        self.lookupapple_outputcsv = outputcsv

        if not self.checkfilelocn(inputcsv):
            print("\n \033[93mInput file not found: {}\033[0m".format(inputcsv))
            print("\n Exiting now. Maybe the file is in a different folder? e.g. C:\\My Work Folder\\applists.csv")
            print(" If you don't specify the folder, I assume you meant: {}\033[0m".format(os.getcwd()))
            input(" Please press ENTER to continue... ")
            return

        if self.checkfilelocn(outputcsv):
            print(" \033[93mWarning: output file ({}) already exists!".format(outputcsv))
            answer = input(" Overwrite [y/n]?\033[96m ")
            while not answer or answer[0].lower() not in ('y', 'n'):
                answer = input(" \033[93mOverwrite (y/n)?\033[96m ")
            if answer[0].lower() == 'n': return
            print("\033[0m")
        try:
            # finally, call the apple lookup!
            applelookup.main(inputcsv, hasHeaders, outputcsv)

        except Exception as e:
            print(e.__class__, ":", e)

        print("Done! :)")
        print("Reminder: your report is in {}".format(outputcsv))
        return

    def singlescrapelist(self):
        outputcsv = self.scrapelist_outputcsv

        self.showutilitywelcome('the single applist scraper utility')

        # prompt for article id of applist to scrape
        answer = input(" What is the article ID of the applist you want to scrape? \033[96m")
        while not answer or not answer.isdigit():
            answer = input(" \033[0mSorry, please enter just the article ID, which is just a positive integer (e.g. 12345): \033[96m")
        article_id = answer
        
        # prompt output csv
        outputcsv = self.getoutputfilename(outputcsv)

        answer = self.confirmIPOsettings(article_id, 'N/A', outputcsv, 'N/A', 'N/A')

        if answer[0].lower() == 'n':
            return

        # remember the output file as the new default
        self.scrapelist_outputcsv = outputcsv

        if self.checkfilelocn(outputcsv):
            print(" \033[93mWarning: output file ({}) already exists!".format(outputcsv))
            answer = input(" Overwrite [y/n]?\033[96m ")
            while not answer or answer[0].lower() not in ('y', 'n'):
                answer = input(" \033[93mOverwrite (y/n)?\033[96m ")
            if answer[0].lower() == 'n': return
            print("\033[0m")

        applistscraper.single(article_id, outputcsv)

        print("Done! :)")
        print("Reminder: your report is in {}".format(outputcsv))
        return

    def googlestats(self):
        if self.googlestats_inputcsv:
            inputcsv = self.googlestats_inputcsv
        else:
            inputcsv = self.scrapelists_inputcsv
        hasHeaders = self.lookupappleinputhasheaders
        outputcsv = self.googlestats_outputcsv
        fromdate = self.googlestats_fromdate
        todate = self.googlestats_todate

        self.showutilitywelcome('the Google Analytics utility')
        inputcsv = self.getinputfilename(inputcsv)
        hasHeaders = self.getinputfilehasheaders(hasHeaders)
        outputcsv = self.getoutputfilename(outputcsv)
        fromdate, todate = self.getdaterange(fromdate, todate)

        answer = self.confirmIPOsettings(inputcsv, hasHeaders, outputcsv, fromdate, todate)

        if answer[0].lower() == 'n':
            return

        # remember the settings as the new defaults
        self.googlestats_inputcsv = inputcsv
        self.googlestatsinputhasheaders = hasHeaders
        self.googlestats_outputcsv = outputcsv

        if not self.checkfilelocn(inputcsv):
            print("\n \033[93mInput file not found: {}\033[0m".format(inputcsv))
            print("\n Exiting now. Maybe the file is in a different folder? e.g. C:\\My Work Folder\\applists.csv")
            print(" If you don't specify the folder, I assume you meant: {}\033[0m".format(os.getcwd()))
            input(" Please press ENTER to continue... ")
            return
        if self.checkfilelocn(outputcsv):
            print(" \033[93mWarning: output file ({}) already exists!".format(outputcsv))
            answer = input(" Overwrite [y/n]?\033[96m ")
            while not answer or answer[0].lower() not in ('y', 'n'):
                answer = input(" \033[93mOverwrite (y/n)?\033[96m ")
            if answer[0].lower() == 'n': return
            print("\033[0m")

        # finally, call google api!
        articlevisits.google.main(inputcsv, outputcsv, fromdate, todate)

        print("Done! :)")
        print("Reminder: your report is in {}".format(outputcsv))
        return

    def showutilitywelcome(self, utilityname:str):
        print("\n\033[95mWelcome to {}!\033[0m\n".format(utilityname))
        print("I'll now guide you...")
        return

    def getinputfilename(self, defaultinputcsv:str):
        """Manage dialog for getting the name and location of the desired input file"""
        inputcsv = defaultinputcsv
        print("\n Are the applists in a CSV called \"{}\" ?".format(inputcsv))
        answer = input(" Press ENTER to confirm or type in a different filename\n(you can include the full folder path): \033[96m")
        if answer: inputcsv = answer
        print("\n \033[96mInput file: {}\n\033[0m".format(inputcsv))

        return inputcsv

    def getinputfilehasheaders(self, defaultinputhasheaders:bool):
        """Manage dialog for finding out if the input CSV has column headers"""
        hasHeaders = defaultinputhasheaders
        answer = input(" \033[0mDoes the input file contain column headers [Y/n]?\033[96m ")
        if not answer: answer = 'y'
        while answer[0].lower() not in ('y', 'n'):
            print(" \033[0mSorry, I didn't understand that. Please enter either 'y'(es) or 'n'(o).")
            answer = input(" \033[0mDoes the input file contain column headers [y/n]?\033[96m ")
            if not answer: answer = 'y'
        if answer[0].lower() == 'n':
            hasHeaders = False # hasHeader was initialized to True so change only if not true
        print("\n \033[96mInput file has column headers: {}\n\033[0m".format(hasHeaders))

        return hasHeaders

    def getoutputfilename(self, defaultoutputcsv:str):
        """Manage dialog for getting the name and location of the desired output file"""
        outputcsv = defaultoutputcsv
        print(" \033[0mDo you want the report to go to a file called \"{}\" ?".format(outputcsv))
        answer = input(" Press ENTER to confirm or type in a different filename\n(you can include the full folder path):\033[96m ")
        if answer: outputcsv = answer
        print("\n \033[96mOutput file: {}\n\033[0m".format(outputcsv))

        return outputcsv

    def getdaterange(self, defaultfromdate, defaulttodate):
        """Manage dialog for getting from and to dates"""
        fromdate = defaultfromdate
        todate = defaulttodate

        if not fromdate:
            answer = input(" \033[0mWhat is the start/from date ('yyyy/mm/dd')? \033[96m")
        else:
            print(" \033[0mStart/from date is {}?".format(fromdate))
            answer = input("Press ENTER to confirm or type in a different date ('yyyy/mm/dd'):\033[96m ")
        
        datevalid = False
        while not datevalid:
            try:
                datetime.strptime(answer, '%Y-%m-%d')
                datevalid = True
            except ValueError:
                try:
                    datetime.strptime(answer, '%Y/%m/%d')
                    datevalid = True
                except ValueError:
                    answer = input(" \033[0mSorry, that doesn't appear to be a valid date. Please enter a date in the format 'yyyy/mm/dd/': \033[96m")
                    datevalid = False

        fromdate = answer

        if not todate:
            answer = input(" \033[0mWhat is the end/to date ('yyyy/mm/dd')? \033[96m")
        else:
            print(" \033[0mStart/from date is {}?".format(fromdate))
            answer = input("Press ENTER to confirm or type in a different date ('yyyy/mm/dd'):\033[96m ")

        datevalid = False
        while not datevalid:
            try:
                datetime.strptime(answer, '%Y/%m/%d')
                datevalid = True
            except ValueError:
                try:
                    datetime.strptime(answer, '%Y-%m-%d')
                    datevalid = True
                except ValueError:
                    answer = input(" \033[0mSorry, that doesn't appear to be a valid date. Please enter a date in the format 'yyyy/mm/dd/': \033[96m")
                    datevalid = False

        todate = answer
        
        if fromdate > todate:
            print(" \033[96mHey, the from date is later than the to date. I guess you know what you're doing but I thought I better mention it anyway.\033[0m")
        print("\n \033[96mFrom {} to {}\n\033[0m".format(fromdate, todate))

        return fromdate, todate

    def confirmIPOsettings(self, inputname, hasHeaders, outputname, fromdate, todate):
        """Summarize Input-Process-Output settings and get confirmation from the user"""
        print("\033[0m This is what you selected -\n   \033[96mInput: {}\n   Input contains headers: {}\n   Output: {}\n   Dates from {} to {}\033[0m".format(inputname, hasHeaders, outputname, fromdate, todate))
        answer = input("\033[0m\n Shall we continue [y/n]?\033[96m ")
        while not answer or answer[0].lower() not in ('y', 'n'):
            answer = input("\033[0m Continue [y/n]?\033[96m ")

        return answer

    def checkfilelocn(self, filepath):
        return os.path.isfile(filepath)
# ---------- END MY FUNCTIONS ------------

    def do_exit(self, arg):
        """ Exits from the console """
        return -1

    def precmd(self, line):
        """This method is called after the line has been input but before it has been interpreted. If you want to modifdy the input line before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):    
        """Do nothing on empty input line"""
        pass

    def default(self, line):       
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        try:
            exec(line) in self._locals, self._globals
        except Exception as e:
            print(e.__class__, ":", e)

if __name__ == '__main__':
    console = CheckerShell()
    console.cmdloop()