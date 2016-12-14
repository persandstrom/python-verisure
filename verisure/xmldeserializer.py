"""
Help function to deserialize XML
"""

import xml.etree.ElementTree as ET


def deserialize(xml):
    """ Deserialize XML to python structure.

    Args:
        xml (str): XML as string
    """
    root = ET.fromstring(xml.encode('utf8'))
    items = []
    for node in root.findall('./*'):
        items.append(_deserialize_node(node))
    return items


def _deserialize_node(node):
    """ Deserialize XML node

    Args:
        node (element): XML element
    """
    fields = {}
    for element in node.findall('./*'):
        if element.text:
            fields[element.tag] = element.text
        elif not element.findall('./*'):
            fields[element.tag] = None
        else:
            if element.tag not in fields:
                fields[element.tag] = []
            fields[element.tag].append(_deserialize_node(element))
    return type(node.tag, (), fields)
