

def isMatch(inFileName, outFileName):
	inFile = open(inFileName, 'r')
	outFile	= open(outFileName, 'r') 
	
	ins = inFile.read().strip().split('\n')
	outs = outFile.read().split('\n')

	for i in range(len(ins)):
		[ai, bi] = ins[i].split()
		ci = outs[i]
		if (int(ai) + int(bi) == int(ci)):
			print ai, bi, ci, True
		else:
			print ai, bi, ci, False

if __name__ == '__main__':
	isMatch('../testCases/add.i', '../testCases/add.o')
