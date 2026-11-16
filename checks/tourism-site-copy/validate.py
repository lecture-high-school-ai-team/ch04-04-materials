"""Verify the unchanged website, its ZIP and the appended distribution guide."""
from html.parser import HTMLParser
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
from urllib.parse import urlsplit


class Structure(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.links=[];self.scripts=0;self.reviews=0

    def handle_starttag(self,tag,attributes):
        attributes=dict(attributes)
        if 'id' in attributes:self.ids.append(attributes['id'])
        for key in ['href','src']:
            if key in attributes:self.links.append(attributes[key])
        if tag=='script':self.scripts+=1
        if 'review' in attributes.get('class','').split():self.reviews+=1


def validate(root):
    record_path=Path('checks/tourism-site-copy/copy-record.json')
    record=json.loads((root/record_path).read_text())
    assert record['source_commit']=='3db25752a837e1603bb5216a13b0080564666808'
    assert {x['source_path'] for x in record['files']}=={'README.md','index.html','style.css'}
    additional={str(record_path),record['archive']['path'],*record['support_paths']}
    assert all(p.startswith('checks/tourism-site-copy/') for p in record['support_paths'])
    for item in record['files']:
        assert item['path']=='site/'+item['source_path']
        data=(root/item['path']).read_bytes()
        assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
        additional.add(item['path'])
    archive=root/record['archive']['path'];raw=archive.read_bytes()
    assert len(raw)==record['archive']['bytes'] and hashlib.sha256(raw).hexdigest()==record['archive']['sha256']
    with ZipFile(archive) as z:
        assert set(z.namelist())=={'README.md','index.html','style.css'}
        for item in record['files']:assert z.read(item['source_path'])==(root/item['path']).read_bytes()
    guide=(root/'README.md').read_bytes();old=record['original_readme'];prefix=guide[:old['bytes']]
    assert hashlib.sha256(prefix).hexdigest()==old['sha256']
    assert guide[old['bytes']:].startswith(record['readme_append_heading'].encode())
    parser=Structure();parser.feed((root/'site/index.html').read_text())
    assert len(parser.ids)==len(set(parser.ids))
    assert parser.scripts==0 and parser.reviews==91
    assert len([i for i in parser.ids if i.startswith('mt-spot-')])==8
    for target in parser.links:
        parsed=urlsplit(target)
        assert not parsed.scheme and not parsed.netloc,'External resource: '+target
        if target.startswith('#'):assert target[1:] in parser.ids,target
        else:assert (root/'site'/parsed.path).is_file(),target
    for path in additional:assert (root/path).is_file(),path
    return additional


if __name__=='__main__':
    result=validate(Path(__file__).resolve().parents[2])
    print('Validated original 3 website files, ZIP, 8 places, 91 reviews, anchors and appended guide.')
