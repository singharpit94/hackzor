from hackzor.server.models import *
from hackzor import settings
import xml.dom.minidom as minidom
import xml.dom.ext as ext
import os, pickle, tempfile
import hackzor.evaluator.GPG as GPG
import types
import StringIO

def queue_not_empty ():
    """ Checks if the ToBeEvaluated queue is empty or not """
    if ToBeEvaluated.objects.count > 0:
        return True
    return False

def encrypt(value, keyid):
    global obj
    return obj.encrypt(value, keyid, always_trust=True).data
    
def add_node (doc, root, child, value, keyid):
    """ Used to add a text node 'child' with the value of 'value' (duh..) """
    node = doc.createElement(child)
    try:
        value = encrypt(value, keyid)
    except:
        print 'Could not encrypt value'
        value = ''
    node.appendChild(doc.createTextNode(value))
    root.appendChild(node)
    
def convert_attempt_to_xml (attempt, keyid):
    """ Converts an attempt into an equivalent XML file """
    doc = minidom.Document()
    root = doc.createElementNS('http://code.google.com/p/hackzor', 'attempt')
    doc.appendChild(root)
    if not attempt:
        return ext.Print (doc)
    add_node(doc, root, 'qid', str(attempt.question.id), keyid)
    add_node(doc, root, 'aid', str(attempt.id), keyid) # aid = Attempt id
    add_node(doc, root, 'code', str(attempt.code), keyid)
    add_node(doc, root, 'lang', str(attempt.language.compiler), keyid)
    add_node(doc, root, 'file-name', str(attempt.file_name), keyid)
    # return ext.Print (doc) # use ext.PrettyPrint when debugging
    return doc.toxml()
    
def dequeue_attempts(keyid):
    """ Returns an attempt from the ToBeEvaluated queue based on priority
    algorithms or return None if queue is empty """
    try:
        attempt = ToBeEvaluated.objects.all()[0]
        to_be_eval = BeingEvaluated(attempt=attempt.attempt)
        to_be_eval.save()
        # TODO: The attempt exists in both queues at this point of
        # time. Rectify.
        attempt.delete()
        return convert_attempt_to_xml(to_be_eval.attempt, keyid)
    except IndexError:
        return None

def get_attempt_as_xml(keyid):
    if queue_not_empty():
        return dequeue_attempts(keyid)
    else:
        print "Attempt Queue Empty"
        return None

def get_question_set_as_xml(keyid):
    qn_set = Question.objects.all()
    doc = minidom.Document()
    root = doc.createElementNS('http://code.google.com/p/hackzor',
                               'question-set')
    doc.appendChild(root)
    for qn in qn_set:
        node = doc.createElement('question')
        node.setAttribute('id', str(qn.id))
        root.appendChild(node)
        add_node(doc, node, 'time-limit', str(qn.time_limit), keyid)
        add_node(doc, node, 'mem-limit', str(qn.memory_limit), keyid)
        inp = open(os.path.join(settings.MEDIA_ROOT,qn.test_input), 'r')
        add_node(doc, node, 'input-data', inp.read(), keyid)
        inp.close()
        # Convert evaluator (May be binary) into pickled data and send along
        # with xml
        data = StringIO.StringIO()
        inp = open(os.path.join(settings.MEDIA_ROOT, qn.evaluator_path), 'r')
        inp_data = inp.read()
        inp.close()
        pickle.dump(inp_data, data)
        data.seek(0)
        cdata = doc.createCDATASection(encrypt(data.read(), keyid))
        eval_node = doc.createElement('evaluator')
        node.appendChild(eval_node)
        eval_node.appendChild(cdata)
        del inp_data, inp
    return doc.toxml()

def get_val_by_id (root, id):
    child_node = root.getElementsByTagName(id)
    if not child_node:
        raise EvaluatorError('Invalid XML file')
    return decrypt(child_node[0].firstChild.nodeValue)

def get_result(xmlised_result):
    """Each Attempt XML file is parsed by this class"""
    xml = minidom.parseString(xmlised_result)
    attempt = xml.getElementsByTagName('attempt')
    if not attempt:
        #return error here
        pass
    attempt = attempt[0]
    # print xml.toprettyxml()
    aid = get_val_by_id(attempt, 'aid')
    result = get_val_by_id(attempt, 'result')
    if (int(result) == 0) :
        error_status = get_val_by_id(attempt, 'error')
    else:
        error_status="Accepted"
    return (aid, result, error_status)

def decrypt(data):
    global obj
    data = str(data)
    if type(data) == types.StringType:
        return obj.decrypt(data, always_trust=True).data
    elif type(data) == types.ListType:
        ret_val = []
        for d in data:
            ret_val.append(obj.decrypt(d).data)
        return ret_val
    # catch error. UnExpected Type

obj = GPG.GPG() # created global to avoid creation for each call of
                # encrypt. TODO: Reconsider moving into some module later on
