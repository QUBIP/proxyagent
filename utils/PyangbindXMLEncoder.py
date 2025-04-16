from pyangbind.lib.serialise import pybindIETFXMLEncoder
from pyangbind.lib.serialise import make_generate_ietf_tree
from pyangbind.lib.serialise import XmlYangDataSerialiser
from lxml import objectify, etree

class XMLEncoder (pybindIETFXMLEncoder):

    @classmethod
    def serialise(cls, obj, filter=True, pretty_print=True):
        """return the complete XML document, as pretty-printed string"""
        doc = cls.encode(obj, filter=filter)
        return etree.tostring(doc, pretty_print=pretty_print).decode("utf8")

    @classmethod
    def encode(cls, obj, filter=True):
        """return the lxml objectify tree for the pybind object"""
        ietf_tree_xml_func = make_generate_ietf_tree(pybindIETFXMLEncoder.yname_ns_func)
        tree = ietf_tree_xml_func(obj, flt=filter)
        preprocessed = XmlYangDataSerialiser().preprocess_element(tree)
        return cls.generate_xml_tree(obj._yang_name, obj._yang_namespace, preprocessed)
