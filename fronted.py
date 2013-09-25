import synonymer
import printer
import completer
import readline
import os
import sys

CONFIG_FILE    = "configs.json"

__version__    = "0.1"
__author__     = "venam"
__maintainer__ = "venam"
__email__      = "patrick at unixhub.net"
__status__     = "more or less working"

def init_completion():
	comp = completer.Completer()
	readline.set_completer_delims(' \t\n;')
	readline.parse_and_bind("tab:complete")
	readline.set_completer(comp.complete)

def take_file():
	access = False
	print "\n"
	while access == False:
		txt_file = raw_input(printer.INFO+"Enter the file you want to convert"+printer.PROMPT)
		access   = os.access(txt_file,os.R_OK)
	return txt_file

def main():
	init_completion()
	if len(sys.argv)>1:
		sys.argv.reverse()
		sys.argv.pop()
		for a in sys.argv:
			print "\n"+printer.INFO + "File "+a+" :"
			print "\n"
			if os.access(a,os.R_OK):
				my_syn = synonymer.synonymer(a,CONFIG_FILE)
				my_syn.procedure()
	else:
		txt_file = take_file() 
		my_syn   = synonymer.synonymer(txt_file, CONFIG_FILE)
		my_syn.procedure()

if __name__ == "__main__":
	main()

