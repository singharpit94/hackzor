#!/usr/bin/env python

import sys
import resource
import os
import commands
mem_limit = int(sys.argv[1])
resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
# TODO: Correct the Maximum No of open Files! Currently not working
no_of_files = 3
#resource.setrlimit(resource.RLIMIT_NOFILE, (no_of_files, no_of_files))
cmd = sys.argv[2]

#args = ''
# try:
    
#     #sys.exit()
# except:
#     for x in sys.exc_info():
#         print x
#     sys.exit(1)

#os.system(os.path.join(os.getcwd(), cmd))
#sys.exit(os.system(cmd))
#status, op = commands.getstatusoutput(cmd)
os.execv(cmd,[])
print op
