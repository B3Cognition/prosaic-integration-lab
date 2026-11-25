"""Export only test identities/status; never captured driver or prompt data."""
from pathlib import Path
import xml.etree.ElementTree as ET


def sanitize_junit(path):
    path = Path(path)
    try:
        original = ET.parse(path)
    except ET.ParseError:
        path.unlink()
        raise ValueError('incomplete JUnit export removed') from None
    root = ET.Element('testsuites')
    suite = ET.SubElement(root, 'testsuite', name='owned-acceptance')
    result = {'test_count': 0, 'skipped': 0, 'failed_tests': []}
    for old in original.iter('testcase'):
        result['test_count'] += 1
        case = ET.SubElement(suite, 'testcase', **{name: old.attrib[name]
            for name in ('name', 'classname', 'time') if name in old.attrib})
        for child in old:
            if child.tag not in {'failure', 'error', 'skipped'}:
                continue
            ET.SubElement(case, child.tag).text = 'Required acceptance gate did not pass; reproduce with the owned runner'
            if child.tag == 'skipped':
                result['skipped'] += 1
            else:
                result['failed_tests'].append(old.attrib.get('name', 'unknown_test'))
                if old.attrib.get('name')=='test_large_captured_context_obeys_default_record_capacity':
                    marker='CONTEXT_PACK_CAPACITY '
                    text=child.text or ''
                    if marker in text and len(text)<=16384:
                        try:
                            import json
                            from .context_packs import sanitize_capacity_diagnostic
                            value,_=json.JSONDecoder().raw_decode(text.split(marker,1)[1].lstrip())
                            result['context_pack_diagnostic']=sanitize_capacity_diagnostic(value)
                        except (ValueError,TypeError,RecursionError):
                            result['context_pack_diagnostic']={'status':'unavailable'}
    temporary = path.with_suffix('.sanitized.xml')
    ET.ElementTree(root).write(temporary, encoding='unicode')
    temporary.replace(path)
    return result
