
import xml.etree.ElementTree as ET

def deserialize(xml):
    root = ET.fromstring(xml.encode('utf8'))
    items = []
    for node in root.findall('./*'):
        items.append(deserialize_node(node))
    return items

def deserialize_node(node, depth=0):
    fields = {}
    for element in node.findall('./*'):
        if element.text:
            fields[element.tag] = element.text
        elif not element.findall('./*'):
            fields[element.tag] = None
        else:
            if not element.tag in fields:
                fields[element.tag] = []
            fields[element.tag].append(deserialize_node(element, depth + 1))
    return type(node.tag, (), fields)
