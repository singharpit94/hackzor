import sys
import os
import time
import commands
import threading
import subprocess
import tempfile
import signal
import time
try:
    from hackzor.evaluator.settings import *
    from hackzor.settings import MEDIA_ROOT
    from server.models import Attempt, ToBeEvaluated, BeingEvaluated
except ImportError:
    C_COMPILE_STR = 'gcc -lm -w \'%i\' -o \'%o\''
    CPP_COMPILE_STR = 'g++ -lm -w \%i\' -o \'%o\''
    JAVA_COMPILE_STR = 'javac \'%i\' -d \'%o\''
    WORK_DIR = 'evaluator/work_files'


class EvaluatorError (Exception):
    def __init__ (self, error, value=''):
        self.value = value
        self.error = error

    def __str__ (self):
        return 'Error: '+self.error+'\tValue: '+ self.value


class Evaluator:
    def __str__ (self):
        raise NotImplementedError ('Must be Overridden')

    def compile (self, code_file, input_file):
        raise NotImplementedError ('Must be Overridden')

    def get_run_cmd (self, exec_file):
        raise NotImplementedError ('Must be Overridden')

    def run (self, cmd, input_file):
        output_file = tempfile.NamedTemporaryFile ()
        input_file = os.path.join (MEDIA_ROOT,input_file)
        print 'Input File: ',input_file
        print 'Output File: ',output_file.name
        # cmd = cmd + ' < ' + input_file + ' > ' + output_file.name
        inp_file = open (input_file,'r')
        kws = {'shell':True, 'stdin':inp_file, 'stdout':output_file.file}
        start_time = time.time()
        p = subprocess.Popen (cmd, **kws)
        while True:
            if time.time() - start_time >= 5:
                # os.kill (pid, signal.SIGTERM)
                os.system ('pkill -P '+str(p.pid)) # Try to implement pkill -P internally
                print 'Killed Process Tree: '+str(p.pid)
                raise EvaluatorError ('Time Limit Expired')
            elif p.poll() != None:
                break
            time.sleep (0.5)
        if p.returncode != 0:
            raise EvaluatorError ('Run-Time Error')
        else:
            output_file.file.flush ()
            output_file.file.seek (0)
            output = output_file.file.read ()
            output_file.close ()
        return output

    def save_file (self, file_path, contents):
        """ Save the contents in the file given by file_path relative inside
        the WORK_DIR directory. It works like `mkdir -p ' in the sense that all
        non existent directories in the path are created"""
        try:
            if not os.path.exists (WORK_DIR):
                os.mkdir (WORK_DIR)
            path_cont = []
            path_split = lambda (x): x != '' and \
                         path_split(os.path.split(x)[0]) or \
                         path_cont.append (os.path.basename(x))
            # This obfuscated piece of shit takes in a path and returns a list
            # of path components i.e. say feed it tmp/abc/def/cde it will
            # return ['tmp', 'abc', 'def', 'cde'] in that order
            # *Defenitely* needs a rewrite
            
            path_split (file_path)
            path_cont = path_cont[1:-1]
            path = WORK_DIR
            for cont in path_cont:
                path = os.path.join (path, cont)
                if not os.path.exists (path):
                    os.mkdir (path)
                    
            open_file = open (os.path.join (WORK_DIR, file_path), 'w')
            open_file.write (contents)
            open_file.close()
        except OSError, IOError:
            raise 
        return os.path.join (WORK_DIR, file_path)

    def evaluate (self, attempt):
        # Save the File
        save_loc = os.path.join (attempt.user.user.username, attempt.file_name)
        code_file = self.save_file (save_loc, attempt.code)

        # Compile the File
        exec_file = self.compile (code_file)

        cmd = self.get_run_cmd (exec_file)
        
        # Execute the file for preset input
        output = self.run (cmd, attempt.question.test_input)

        # Match the output to expected output
        return self.check (attempt, output)

    def check (self, attempt, output):
        eval_path = os.path.join (MEDIA_ROOT, attempt.question.evaluator_path)
        if eval_path[-3:] != '.py':
            raise EvaluatorError ('Evalutor Not Supported')
        eval_path = eval_path[:-3]
        compare = __import__ (eval_path)
        result =  compare.compare (output)
        return result


class C_Evaluator (Evaluator):
    def __init__ (self):
        self.compile_cmd = C_COMPILE_STR
        
    def __str__ (self):
        return 'C Evaluator'

    def get_run_cmd (self, exec_file):
        return exec_file

    def compile (self, code_file):
        output_file = code_file # Change this value to change output file name
        # replace the code with the object file
        cmd = self.compile_cmd.replace ('%i',code_file).replace('%o',output_file)

        (status, output) = commands.getstatusoutput (cmd)
        if status != 0:
            raise EvaluatorError ('Compiler Error', output)
        else:
            return output_file


class CPP_Evaluator (C_Evaluator):
    def __init__ (self):
        self.compile_cmd = CPP_COMPILE_STR

    def __str__ (self):
        return 'C++ Evaluator'
    

class Java_Evaluator (Evaluator):
    def __str__ (self):
        return 'Java Evaluator'

    def __init__ (self):
        self.compile_cmd = JAVA_COMPILE_STR

    def get_run_cmd (self, exec_file):
        return 'java '+exec_file

    def compile (self, code_file):
        output_dir, file_name = os.path.split (code_file)
        cmd = self.compile_cmd.replace ('%i',code_file).replace('%o',
                                                                output_dir)
        if file_name [-5:] != '.java':
            raise EvaluatorError ('Compiler Error', 'Not a Java File')
        file_name = file_name [:-5]
        (status, output) = commands.getstatusoutput (cmd)
        if status != 0:
            raise EvaluatorError ('Compiler Error', output)
        else:
            return file_name


class Python_Evaluator (Evaluator):
    def __str__ (self):
        return 'Python Evaluator'

    def compile (self, code_file):
        """ Nothing to Compile in the case of Python. Aha *Magic*!"""
        return code_file

    def get_run_cmd (self, exec_file):
        return 'python '+exec_file
    

class Client (threading.Thread):
    """ The Evaluator will evaluate and update the status """
    evaluators = {'c':C_Evaluator, 'c++':CPP_Evaluator,
                  'java':Java_Evaluator, 'python':Python_Evaluator}
    
    def __init__ (self):
        threading.Thread.__init__ (self)

    def queue_not_empty (self):
        """ Checks if the ToBeEvaluated queue is empty or not """
        if ToBeEvaluated.objects.count > 0:
            return True
        return False

    def dequeue_attempts (self):
        """ Returns an attempt from the ToBeEvaluated queue based on priority
        algorithms or return None if queue is empty """
        try:
            attempt = ToBeEvaluated.objects.all()[0]
            to_be_eval = BeingEvaluated(attempt=attempt.attempt)
            to_be_eval.save()
            # TODO: The attempt exists in both queues at this point of
            # time. Rectify.
            attempt.delete()
            return to_be_eval
        except IndexError:
            return None
    
    def get_attempt (self):
        """ Keep polling the ToBeEvaluated queue until an attempt to be
        evaluated is obtained """
        while True:
            if (self.queue_not_empty()):
                return self.dequeue_attempts()
            time.sleep (1)

    def score (self, result, score):
        """Apply a function on the result to generate the score.. in case you
        want to have step wise scoring"""
        if result == True:
            return score
        else:
            return 0

    def evaluate (self, attempt):
        """ Evaluate the attempt and return the ruling :-) """
        lang = attempt.language.compiler.lower()
        # first list special case languages whose names cannot be used for
        # function names in python
        try:
            evaluator = self.evaluators[lang]()
            result = evaluator.evaluate(attempt)
            attempt.user.score += self.score (result, attempt.question.score)
            attempt.user.save()
            return result
        except KeyError:
            raise NotImplementedError ('Language '+lang+' not supported')
        
    def run (self):
        print 'Evaluator Started'
        attempt = self.get_attempt ()
        if attempt == None:
            return
        # evalute the attempt
        try:
            return_value = self.evaluate (attempt.attempt)
        except EvaluatorError:
            print 'EvaluatorError: '
            print sys.exc_info()[1].error
            return_value = False
        attempt.attempt.result = return_value
        attempt.attempt.save()
        # The Attempt continues to remain in the DB. In case you want to delete
        # the attempt from the DB (for scalability purposes perhaps?) then
        # uncomment the next line.
        # attempt.attempt.delete()        
        attempt.delete()
        print 'Final Result: ', return_value
        return return_value
