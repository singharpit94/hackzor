# '%' is not allowed in the compilation string.
# Format Strings:
#     %i    ---  Input File Name
#     %o    ---  Ouput File Name
#     %u    ---  User Name (who submitted the code)
#     %q    ---  Question Name


C_COMPILE_STR = 'gcc -lm -w \'%i\' -o \'%o\''
CPP_COMPILE_STR = 'g++ -lm -w \'%i\' -o \'%o\''
JAVA_COMPILE_STR = 'javac \'%i\' -d \'%o\''

WORK_DIR = 'evaluator/work_files'
TIME_INTERVAL = 2 # Time between poll to web server for attempts (in seconds)
