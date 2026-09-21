import uuid
from xml.etree import ElementTree as ET

SOAP_ENV = "http://www.w3.org/2003/05/soap-envelope"
SOAP_ENV_OLD = "http://schemas.xmlsoap.org/soap/envelope/"
W = "http://www.w3.org/2005/08/addressing"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child(element: ET.Element, name: str) -> ET.Element | None:
    return next((item for item in element.iter() if local_name(item.tag) == name), None)


def children(element: ET.Element, name: str) -> list[ET.Element]:
    return [item for item in element.iter() if local_name(item.tag) == name]


def text(element: ET.Element | None, name: str) -> str | None:
    if element is None:
        return None
    found = child(element, name)
    value = (found.text or "").strip() if found is not None else ""
    return value or None


def request(action: str, body_name: str, body_xml: str, security: bytes = b"") -> bytes:
    envelope = ET.Element(f"{{{SOAP_ENV}}}Envelope")
    header = ET.SubElement(envelope, f"{{{SOAP_ENV}}}Header")
    if security:
        header.append(ET.fromstring(security))
    action_element = ET.SubElement(header, f"{{{W}}}Action")
    action_element.text = action
    message_id = ET.SubElement(header, f"{{{W}}}MessageID")
    message_id.text = f"urn:uuid:{uuid.uuid4()}"
    body = ET.SubElement(envelope, f"{{{SOAP_ENV}}}Body")
    operation = ET.SubElement(body, body_name)
    if body_xml:
        fragment = ET.fromstring(f"<Fragment>{body_xml}</Fragment>")
        operation.extend(list(fragment))
    return ET.tostring(envelope, encoding="utf-8", xml_declaration=True)


def parse_response(payload: bytes) -> ET.Element:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError("invalid XML response") from exc
    fault = child(root, "Fault")
    if fault is not None:
        reason = text(fault, "Text") or text(fault, "Reason") or "ONVIF SOAP fault"
        raise RuntimeError(reason)
    body = child(root, "Body")
    if body is None:
        raise ValueError("SOAP response did not contain a body")
    return body
