from hackzor.server.models import *
from hackzor import settings
import xml.dom.minidom as minidom
import os, pickle, tempfile
import types
import StringIO, sys

def queue_not_empty ():
    """ Checks if the ToBeEvaluated queue is empty or not """
    if ToBeEvaluated.objects.count() > 0:
        return True
    return False

def add_node (doc, root, child, value):
    """ Used to add a text node 'child' with the value of 'value' (duh..) """
    node = doc.createElement(child)
    node.appendChild(doc.createTextNode(value))
    root.appendChild(node)
    
def convert_attempt_to_xml (attempt):
    """ Converts an attempt into an equivalent XML file """
    doc = minidom.Document()
    root = doc.createElementNS('http://code.google.com/p/hackzor', 'attempt')
    doc.appendChild(root)
    if not attempt:
        return ext.Print (doc)
    add_node(doc, root, 'qid', str(attempt.question.id))
    add_node(doc, root, 'aid', str(attempt.id)) # aid = Attempt id
    add_node(doc, root, 'code', str(attempt.code))
    add_node(doc, root, 'lang', str(attempt.language.compiler))
    add_node(doc, root, 'file-name', str(attempt.file_name))
    # return ext.Print (doc) # use ext.PrettyPrint when debugging
    return doc.toxml()
    
def dequeue_attempts():
    """ Returns an attempt from the ToBeEvaluated queue based on priority
    algorithms or return None if queue is empty """

    try:
        # Couldn't use order_by since django had a bug in order_by when doing cross table lookups
        attempt = ToBeEvaluated.objects.select_related().order_by('server_attempt.time_of_submit')[0]
        to_be_eval = BeingEvaluated(attempt=attempt.attempt)
        to_be_eval.save()
        # TODO: The attempt exists in both queues at this point of
        # time. Rectify.
        attempt.delete()
        return convert_attempt_to_xml(to_be_eval.attempt)
    except IndexError:
        return None

def get_attempt_as_xml():
    if queue_not_empty():
        return dequeue_attempts()
    else:
        print "Attempt Queue Empty"
        return None

def get_question_set_as_xml():
    qn_set = Question.objects.all()
    doc = minidom.Document()
    root = doc.createElementNS('http://code.google.com/p/hackzor',
                               'question-set')
    doc.appendChild(root)
    for qn in qn_set:
        node = doc.createElement('question')
        node.setAttribute('id', str(qn.id))
        root.appendChild(node)
        add_node(doc, node, 'time-limit', str(qn.time_limit))
        add_node(doc, node, 'mem-limit', str(qn.memory_limit))
        inp = open(os.path.join(settings.MEDIA_ROOT,qn.test_input), 'r')
        add_node(doc, node, 'input-data', inp.read())
        inp.close()
        # Convert evaluator (May be binary) into pickled data and send along
        # with xml
        data = StringIO.StringIO()
        inp = open(os.path.join(settings.MEDIA_ROOT, qn.judge_path), 'r')
        inp_data = inp.read()
        inp.close()
        pickle.dump(inp_data, data)
        data.seek(0)
        cdata = doc.createCDATASection(data.read())
        eval_node = doc.createElement('evaluator')
        node.appendChild(eval_node)
        eval_node.appendChild(cdata)
        del inp_data, inp
    return doc.toxml()

def get_val_by_id (root, id):
    child_node = root.getElementsByTagName(id)
    if not child_node:
        print 'Invalid XML file'
        raise EvaluatorError('Invalid XML file')
    return child_node[0].firstChild.nodeValue

def get_result(xmlised_result):
    """Each Attempt XML file is parsed by this class"""
    xml = minidom.parseString(xmlised_result)
    attempt = xml.getElementsByTagName('attempt')
    if not attempt:
        print "Warning! Empty Attempt recieved."
        return #TODO: Temporary
        #return error here
        #pass
    attempt = attempt[0]
    #print xml.toprettyxml()
    aid = get_val_by_id(attempt, 'aid')
    result = get_val_by_id(attempt, 'result')
    if (int(result) != 0) :
        error_status = get_val_by_id(attempt, 'error')
    else:
        error_status="Accepted"
    return (aid, result, error_status)
