import sys
import os
import time
import commands
import threading
import subprocess
import tempfile
import signal
import time
import pickle
import cookielib
import urllib2
import resource
import types
import StringIO
import logging
import xml.dom.minidom as minidom

from settings import *
import rules
import GPG

class EvaluatorError(Exception):
    def __init__(self, error, value=''):
        self.value = value
        self.error = error

    def __str__(self):
        return 'Error: '+self.error+'\tValue: '+ self.value


class XMLParser:
    """This base class will contain all the functions needed for the XML file
    to be parsed
    NOTE: This class is not to be instantiated
    """
    obj = GPG.GPG()
    logger = logging.getLogger('XML')
    def __init__(self):
        raise NotImplementedError('XMLParser class is not to be instantiated')

    def dos2unix(self, data):
        """Converts text from DOS CRLF to UNIX LF"""
        from string import join, split
        return join(split(data, '\r\n'), '\n')

    def decrypt(self, value):
        """Converts the obtained cipher text into clear text. Decrypting is
        based on the private key of the recipient, so the keyid is not
        required.
        """
        if type(value) == types.ListType:
            ret_val = []
            for val in value:
                ret_val.append(self.obj.decrypt(val, always_trust=True))
            return ret_val
        return self.obj.decrypt(value, always_trust=True).data
    
    def get_val_by_id(self, root, id):
        """This function will get the value of the `id' child node of
        `root' node. `root' should be of type DOM Element. e.g.
        root
        |
        |-- <id>value-to-be-returned</id>"""
        child_node = root.getElementsByTagName(id)
        if not child_node:
            self.logger.critical('Invalid XML file: \n'+root.toxml())
            raise EvaluatorError('Invalid XML file')
        return self.dos2unix(self.decrypt(child_node[0].firstChild.nodeValue))

    def add_node(self, doc, root, child, value):
        """ Used to add a text node 'child' with the value of 'value'(duh..)
        """
        node = doc.createElement(child)
        value = self.obj.encrypt(value, SERVER_KEYID, always_trust=True).data
        node.appendChild(doc.createTextNode(value))
        root.appendChild(node)

    
class Question(XMLParser):
    """Defines the Characteristics of each question in the contest"""
    logger = logging.getLogger('XML.Question')
    def __init__(self, qn, qid):
        input_data = self.get_val_by_id(qn, 'input-data')
        self.input_path = self.save_input_to_disk(input_data, qid)
        self.time_limit = float(self.get_val_by_id(qn, 'time-limit'))
        self.mem_limit = int(self.get_val_by_id(qn, 'mem-limit'))
        self.eval_path = self.save_eval_to_disk(qn, qid)
        self.logger.info('Received New Question: Input Data - %s, Time Limit -' \
                         ' %f, Memory Limit - %d, Evaluator - %s' %
                         (self.input_path, self.time_limit, self.mem_limit,
                          self.eval_path))        
        
    def save_input_to_disk(self, input_data, qid):
        """Saves the input file to disk"""
        inp_path = os.path.join(INPUT_PATH, qid)
        inp_file = open(inp_path, 'w')
        input_data = str(input_data)
        inp_file.write(input_data)
        inp_file.close()
        return inp_path
        
    def save_eval_to_disk(self, qn, qid):
        """This function will unpickle the evaluator, sent from web server and
        save it into a file in the directory `evaluators' in the name of the
        question id"""
        # Save the pickled Evaluator binary to disk
        evaluator = self.decrypt(qn.getElementsByTagName('evaluator')[0].firstChild.nodeValue)
        eval_file_path = os.path.join(EVALUATOR_PATH, qid)
        ev = StringIO.StringIO()
        ev.write(evaluator)
        ev.seek(0)
        eval_file = open(eval_file_path, 'w')
        eval_file.close()
        os.chmod(eval_file_path, 0700) # set executable permission for
                                       # code checker
        return eval_file_path

    
class Questions(XMLParser):
    """Set of all questions in the contest"""
    def __init__(self, xml_file):
        xml = minidom.parseString(xml_file)
        qn_set = xml.getElementsByTagName('question-set')[0]
        if not qn_set:
            pass # TODO: return error here
        self.questions = {}
        for qn in qn_set.getElementsByTagName('question'):
            qid = str(qn.getAttribute('id').strip())
            self.questions[qid] = Question(qn, qid)
                        

class Attempt(XMLParser):
    """Each Attempt XML file is parsed by this class"""
    logger = logging.getLogger('XML.Attempt')
    def __init__(self, xml_file):
        xml = minidom.parseString(xml_file)
        attempt = xml.getElementsByTagName('attempt')
        if not attempt:
            pass # TODO: return error here
        attempt = attempt[0]
        self.aid = self.get_val_by_id(attempt, 'aid')
        self.qid = self.get_val_by_id(attempt, 'qid')
        self.code = self.get_val_by_id(attempt, 'code')
        self.lang = self.get_val_by_id(attempt, 'lang')
        self.file_name = self.get_val_by_id(attempt, 'file-name')
        self.logger.info('Obtained an attempt: AID - %s, QID - %s, LANG - %s,'\
                         ' FILENAME - %s' % (self.aid, self.qid, self.lang,
                                             self.file_name))

    def convert_to_result(self, result, msg):
        """Converts an attempt into a corresponding XML file to notify result"""
        doc = minidom.Document()
        root = doc.createElementNS('http://code.google.com/p/hackzor',
                                   'attempt')
        
        doc.appendChild(root)
        self.add_node(doc, root, 'aid', self.aid)
        self.add_node(doc, root, 'result', str(result))
        if int(result) in rules.rules.keys():
            msg = rules.rules[int(result)]
        self.add_node(doc, root, 'error', msg)
        self.logger.info('Attempt %s evaluated to \'%s\' with return value %s' %
                         (self.aid, msg, result))
        print msg
        return doc.toxml()
        

class Evaluator:
    """Provides the base functions for evaluating an attempt.
    NOTE: This class is not to be instantiated"""
    logger = logging.getLogger('XML.Attempt')

    def compile(self, code_file, input_file):
        raise NotImplementedError('Must be Overridden')

    def get_run_cmd(self, exec_file):
        raise NotImplementedError('Must be Overridden')

    def is_compiled(self):
        raise NotImplementedError('Must be Overridden')

    def get_additional_time(self):
        """In the case that a particular language is to be awarded extra
        execution time over ride this function. The return value in seconds
        will be the amount of extra execution time awarded to the program
        """
        return 0 # Defaults to no additional time

    def get_additional_mem(self):
        """In the case that a particular language is to be awarded extra
        memory over ride this function. The return value in bytes will be the
        amount of extra execution time awarded to the program
        """
        return 0 # Defaults to no additional memory

    def run(self, cmd, quest):
        """Execute the command `cmd' and returns the execution output file
        descriptor in a tempfile.NamedTemporaryFile() object.
        """
        input_file = quest.input_path
        output_file = tempfile.NamedTemporaryFile()
        # subprocess will not accept StringIO objects
        inp = open (input_file, 'r')
        kws = {'shell':True, 'stdin':inp, 'stdout':output_file.file}
        start_time = time.time()
        mem_limit = quest.mem_limit + self.get_additional_mem()
        time_limit = quest.time_limit + self.get_additional_time()
        # TODO: Convert all these print statements in logging files
        print 'Running: ', cmd
        print 'Memory limit: ', mem_limit
        print 'Time limit: ', time_limit
        self.logger.info('Executing command: ' + cmd)
        # TODO: pass the input file as a parameter to exec.py too
        p = subprocess.Popen('./exec.py '+str(quest.mem_limit)+' '+cmd, **kws)
        while True:
            if time.time() - start_time >= quest.time_limit:
                inp.close()
                # TODO: Try to execute the KILL code internall with no
                # dependancies
                self.logger.info('pgreping for '+os.path.basename(cmd))
                status, psid = commands.getstatusoutput('pgrep -f '+os.path.basename(cmd))

                psid = psid.splitlines()
                if os.getpid() in psid:
                    psid.remove(os.getpid()) # do not kill evaluator itself in
                                        # case of a python TLE
                if psid == '':
                    print 'oO Problems of problems. Kill manually'
                    self.logger.critical('No Process ID to be killed. Look into '\
                                         'this manually')
                    psid = [p.pid]
                for proc in psid:
                    self.logger.info('Killing psid '+proc)
                    try:
                        os.kill (int(proc), signal.SIGKILL)
                    except OSError:
                        pass # process does not exist
                self.logger.info('Killed Process Tree: %d' % p.pid)
                raise EvaluatorError('Time Limit Expired')
            elif p.poll() != None:
                break
            time.sleep(PS_POLL_INTVL)
        if p.returncode == 139:
            raise EvaluatorError('Run-Time Error. Received SIGSEGV')
        elif p.returncode == 137:
            raise EvaluatorError('Run-Time Error. Received SIGTERM')
        elif p.returncode == 143:
            raise EvaluatorError('Run-Time Error. Received SIGKILL')
        elif p.returncode != 0 :
            raise EvaluatorError('Run-Time Error. Unknown Error')
        else:
            output_file.file.flush()
            output_file.file.seek(0)
        return output_file

    def save_file(self, file_path, contents):
        """ Save the contents in the file given by file_path relative inside
        the WORK_DIR directory"""
        if not os.path.exists(WORK_DIR):
            os.mkdir(WORK_DIR)
        file_path = os.path.join(WORK_DIR, file_path)
        open_file = open(file_path, 'w')
        open_file.write(contents)
        open_file.close()
        return file_path

    def evaluate(self, attempt, quest):
        """Evaluate the attempt and serve the ruling"""
        # Save the File
        save_loc = attempt.aid + '-' + attempt.qid + '-' + attempt.file_name
        code_file = self.save_file(save_loc, attempt.code)
        # Java has this dirty requirement that the file name be the same as the
        # main class name. So having a workaround. The attempts are saved
        #(for archival purposes only) and java files are also saved in a
        # temporary directory called java
        if attempt.lang.lower() == 'java':
            save_loc = os.path.join(JAVA_TEMP_DIR, attempt.file_name)
            self.logger.info('Java Submission. Saving file with original name '\
                             'to ' + save_loc)
            code_file = self.save_file(save_loc, attempt.code)

        # Compile the File
        self.logger.info('Compiling Attempt ' + attempt.aid)
        exec_file = self.compile(code_file)
        cmd = self.get_run_cmd(exec_file)
        # Execute the file for preset input
        try: 
            output = self.run(cmd, quest)
        except:
            if self.is_compiled():
                self.logger.info('Removing Object File: ' + exec_file)
                os.remove(exec_file)
            raise
        if self.is_compiled():
            self.logger.info('Removing Object File: ' + exec_file)
            os.remove(exec_file)
        self.logger.info('Running Output Checker')
        return self.check(attempt, output, quest.eval_path)

    def check(self, attempt, output, eval_path):
        """This receives a tempfile.NamedTemporaryFile object which contains
        the output of the user program
        """
        output.seek(0)
        kws = {'shell':True, 'stdin':output.file}
        p = subprocess.Popen(eval_path, **kws)
        p.wait()
        output.close()
        return str(p.returncode)


class C_Evaluator(Evaluator):
    def __init__(self):
        self.compile_cmd = C_COMPILE_STR
        
    def __str__(self):
        return 'C Evaluator'

    def get_run_cmd(self, exec_file):
        return os.path.join('.', exec_file)

    def is_compiled(self):
        return True

    def compile(self, code_file):
        output_file = code_file # Change this value to change output file name
        # replace the code with the object file
        code_file = code_file.replace('\'','\\\'').replace('\"','\\\"')
        cmd = self.compile_cmd.replace('%i',code_file).replace('%o',output_file)
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            raise EvaluatorError('Compiler Error', output)
        else:
            return output_file


class CPP_Evaluator(C_Evaluator):
    def __init__(self):
        self.compile_cmd = CPP_COMPILE_STR

    def __str__(self):
        return 'C++ Evaluator'
    

class CSharp_Evaluator(C_Evaluator):
    """NOTE: No of processes should not be limited to 0 for the CSharp Eval to
    work. It usually forks about 15-20 times on initialising
    """
    def __init__(self):
        self.compile_cmd = CSHARP_COMPILE_STR

    def __str__(self):
        return 'CSharp Evaluator'

    def get_additional_mem(self):
        return 15*1024*1024

    def compile(self, code_file):
        return C_Evaluator.compile(self, code_file)+'.exe'


class Java_Evaluator(Evaluator):
    def __str__(self):
        return 'Java Evaluator'

    def __init__(self):
        self.compile_cmd = JAVA_COMPILE_STR
        self.link_cmd = JAVA_LINK_STR

    def get_run_cmd(self, exec_file):
        return exec_file

    def is_compiled(self):
        return True
    
    def get_additional_mem(self):
        return 20*1024*1024
    
    def get_additional_time(self):
        return 2.0

    def compile(self, code_file):
        """When we use GCJ to convert the java file to native binary, it goes
        through two phases, the compiling phase and the linking phase
        """
        output_dir, file_name = os.path.split(code_file)
        code_file = code_file.replace('\'','\\\'')
        cmd = self.compile_cmd.replace('%i',code_file)
        if file_name [-5:] != '.java':
            raise EvaluatorError('Compiler Error', 'Not a Java File')
        file_name = file_name [:-5]
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            raise EvaluatorError('Compiler Error', output)
        out = os.path.join(WORK_DIR, file_name)
        cmd = self.link_cmd.replace('%i', file_name).replace('%o', out)
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            raise EvaluatorError('Compiler Error', output)
        else:
            return out

class Interpreted_Language(Evaluator):
    def compile(self, code_file):
        """ Nothing to Compile. Aha *Magic*!"""
        os.chmod(code_file,0700)
        return code_file

    def get_run_cmd(self, exec_file):
        return os.path.join('.', exec_file)
    # SHEBANG line is very very important for this to work.!
    # python = /usr/bin/env python
    # ruby = /usr/bin/ruby
    # perl = /usr/bin/perl
    # PHP = /usr/bin/php
    
    def is_compiled(self):
        return False

    def get_additional_mem(self):
        return 20*1024*1024

    def get_additional_time(self):
        return 2.0


class Python_Evaluator(Interpreted_Language):
    def __str__(self):
        return 'Python Evaluator'

class Ruby_Evaluator(Interpreted_Language):
    def __str__(self):
        return 'Ruby Evaluator'
    
class Perl_Evaluator(Interpreted_Language):
    def __str__(self):
        return 'Perl Evaluator'

    def get_additional_mem(self):
        return 10*1024*1024 # Perl is much more light weight compared to the
                            # other interpreted languages


class PHP_Evaluator(Interpreted_Language):
    def __str__(self):
        return 'PHP Evaluator'


class Client:
    """ The Evaluator will evaluate and update the status """
    evaluators = {'c':C_Evaluator, 'c++':CPP_Evaluator,
                  'java':Java_Evaluator, 'python':Python_Evaluator,
                  'ruby':Ruby_Evaluator, 'php':PHP_Evaluator,
                  'perl':Perl_Evaluator, 'csharp':CSharp_Evaluator}
    obj = GPG.GPG()
    def __init__(self):
        fpr = self.obj.fingerprints()[0]
        for key in self.obj.list_keys():
            if key['fingerprint'] == fpr:
                key_id = key['keyid']
        root_url = CONTEST_URL + '/opc/evaluator/'+key_id
        self.get_attempt_url = root_url + '/getattempt/'
        self.submit_attempt_url = root_url + '/submitattempt/'
        self.get_qns = root_url + '/getquestionset/'
        self.get_pub_key = root_url + '/getpubkey/'
        self.question_set = Questions(self.read_page(self.get_qns))
        # TODO: Get Pub Key automatically from the server
#         global SERVER_KEYID
#         server_key = self.read_page(self.get_pub_key)
#         SERVER_KEYID = self.import_key(server_key)

# Uncomment the below region when automatic retreival of Public key is implemented
#     def import_key(self, key):
#         """This will import the Server's public key to the local PGP keyring"""
#         try:
#             imp = self.obj.import_key(key)
#         except KeyError:
#             print 'Unable to import'
#             return # TODO: Should it fail here?
#         for keys in self.obj.list_keys():
#             if keys['fingerprint'] == imp['fingerprint']:
#                 return keys['keyid']
    def __del__(self):
        logging.shutdown()
    
    def read_page(self, website):
        cj = cookielib.CookieJar()
        cookie_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(cookie_opener)
        req = urllib2.Request(website, None)
        data = urllib2.urlopen(req)
        data = data.read()
        return data
    
    def get_attempt(self):
        """ Keep polling the server until an attempt to be evaluated is
        obtained
        """
        req = urllib2.Request(self.get_attempt_url, None)
        req = urllib2.urlopen(req)
        return Attempt(req.read())

    def evaluate(self, attempt, quest):
        """ Evaluate the attempt and return the ruling :-) 
            attempt : An instance of the Attempt Class
            return value : Boolean, the result of the evaluation.
        """
        lang = attempt.lang.lower()
        # first list special case languages whose names cannot be used for
        # function names in python
        try:
            evaluator = self.evaluators[lang]()
            return evaluator.evaluate(attempt, quest)
        except KeyError:
            raise NotImplementedError('Language '+lang+' not supported')
        except EvaluatorError:
            raise
            
    def submit_attempt(self, attempt_xml):
        """This will submit the XML file containing the result of the attempt
        back to the server
        """
        host = CONTEST_URL
        selector = self.submit_attempt_url
        attempt_xml = self.obj.sign(attempt_xml).data
        headers = {'Content-Type': 'application/xml',
                   'Content-Length': str(len(attempt_xml))}
        r = urllib2.Request(self.submit_attempt_url, data=attempt_xml, headers=headers)
        return urllib2.urlopen(r).read()
        
    def start(self):
        logger = logging.getLogger('Client')
        logger.info('Evaluator Started')
        logger.info('Waiting for attempts from '+CONTEST_URL)
        print 'Evaluator Started'
        while True:
            try:
                logger.info('Waiting for Attempt')
                attempt = self.get_attempt()
            except urllib2.HTTPError:
                attempt = None  # No attempts in web server queue to evaluate
                time.sleep(TIME_INTERVAL)
                continue
            # Evaluate the attempt
            logger.info('Obtained an Attempt. Starting Evaluation')
            try:
                return_value = self.evaluate(attempt, self.question_set.questions[str(attempt.qid)])
                msg = ''
            except EvaluatorError:
                print 'EvaluatorError: '
                msg = sys.exc_info()[1].error
                return_value = 3
                logger.exception('Exception Occured. Return Value is 3')
            print 'Final Result: ', return_value, msg
            print self.submit_attempt(attempt.convert_to_result(return_value, msg))
        return return_value
if __name__ == '__main__':
    if len(sys.argv) >= 2:
        log_file = sys.argv[1]
    else:
        log_file = 'hackzor.log'
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename=log_file,
                        filemode='w')
    Client().start()
