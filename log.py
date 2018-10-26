import sys

verbose = True
if len(sys.argv) == 2 and sys.argv[1] == '-q':
	verbose = False

def write(*args):
	if verbose:
		print(*args)
