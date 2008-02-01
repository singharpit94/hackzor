# '%' is not allowed in the compilation string.
# Format Strings:
#     %i    ---  Input File Name
#     %o    ---  Ouput File Name

C_COMPILE_STR = 'gcc -lm -w \'%i\' -o \'%o\''
CPP_COMPILE_STR = 'g++ -lm -w \'%i\' -o \'%o\''
JAVA_COMPILE_STR = 'gcj -c -g -O \'%i\''
JAVA_LINK_STR = 'gcj --main=%i -o %o %i.o'
CSHARP_COMPILE_STR = 'gmcs \'%i\' -out:\'%o\''

WORK_DIR = 'work_files'
TIME_INTERVAL = 5 # Time between poll to web server for attempts (in seconds)
EVALUATOR_PATH = 'evaluators'
INPUT_PATH = 'input'
JAVA_TEMP_DIR = 'java'

CONTEST_URL = 'http://localhost:8000' 
EVALUATOR_KEYID = 'Bleh'
                                      
PS_POLL_INTVL = 0.1 # Time between each poll of the process to check if process
                    # has completed or should be killed
