# '%' is not allowed in the compilation string.
# Format Strings:
#     %i    ---  Input File Name
#     %o    ---  Ouput File Name
#     %u    ---  User Name (who submitted the code)
#     %q    ---  Question Name


C_COMPILE_STR = '/usr/bin/gcc -lm \'%i\' -o \'%o\''
CPP_COMPILE_STR = 'g++ -lm \%i\' -o \'%o\''
JAVA_COMPILE_STR = 'javac \'%i\''

WORK_DIR = 'evaluator/work_files'
