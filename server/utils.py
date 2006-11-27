from hackzor.server.models import *
import xml.dom.minidom as minidom
import xml.dom.ext as ext

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
    add_node (doc, root, 'qid', attempt.question.id)
    add_node (doc, root, 'aid', attempt.id) # aid = Attempt id
    add_node (doc, root, 'code', attempt.code)
    add_node (doc, root, 'lang', attempt.language)
    add_node (doc, root, 'file-name', attempt.file_name)
    return ext.Print (doc) # use ext.PrettyPrint when debugging
    
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

def get_attempt ():
    if (queue_not_empty()):
        return convert_to_xml(None)
    else:
        return dequeue_attempt()

