from hackzor.server.models import *
from hackzor import settings
import xml.dom.minidom as minidom
import xml.dom.ext as ext
import os, pickle, tempfile

def queue_not_empty ():
    """ Checks if the ToBeEvaluated queue is empty or not """
    if ToBeEvaluated.objects.count > 0:
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
    add_node (doc, root, 'qid', str(attempt.question.id))
    add_node (doc, root, 'aid', str(attempt.id)) # aid = Attempt id
    add_node (doc, root, 'code', str(attempt.code))
    add_node (doc, root, 'lang', str(attempt.language.compiler))
    add_node (doc, root, 'file-name', str(attempt.file_name))
    #return ext.Print (doc) # use ext.PrettyPrint when debugging
    return doc.toxml()
    
def dequeue_attempts ():
    """ Returns an attempt from the ToBeEvaluated queue based on priority
    algorithms or return None if queue is empty """
    try:
        attempt = ToBeEvaluated.objects.all()[0]
        to_be_eval = BeingEvaluated(attempt=attempt.attempt)
        to_be_eval.save()
        # TODO: The attempt exists in both queues at this point of
        # time. Rectify.
        attempt.delete()
        return convert_attempt_to_xml(to_be_eval.attempt)
    except IndexError:
        return None

def get_attempt_as_xml ():
    if (queue_not_empty()):
        return dequeue_attempts()
    else:
        return convert_attempt_to_xml(None)

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
    inp = open( os.path.join(settings.MEDIA_ROOT,qn.test_input), 'r')
    add_node(doc, node, 'input-data', inp.read())
    inp.close()

    # Convert evaluator (May be binary into pickled data) and send along
    # with xml
    inp = open(os.path.join(settings.MEDIA_ROOT, qn.evaluator_path), 'r')
    inp_data = inp.read()
    inp.close()
    inp = tempfile.NamedTemporaryFile()
    pickle.dump(inp_data, inp.file)
    inp.flush()
    temp = open(inp.name, 'r').read()
    inp.close()
    cdata = doc.createCDATASection(temp)
    eval_node = doc.createElement('evaluator')
    node.appendChild(eval_node)
    eval_node.appendChild(cdata)
    del inp_data, inp
    return doc.toxml()
