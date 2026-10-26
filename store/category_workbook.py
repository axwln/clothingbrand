"""Read source cell text without normalizing spelling, case, blanks or whitespace."""
import posixpath
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def read_source(path):
    with ZipFile(path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(t.text or '' for t in node.findall('.//s:t', NS))
                       for node in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        relations = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        sheets = ET.fromstring(archive.read('xl/workbook.xml')).findall('s:sheets/s:sheet', NS)
        names = {s.attrib['name']: s for s in sheets}
        sheet = names.get('Working')
        original = sheet is not None
        if sheet is None:
            sheet = names.get('Original 108 Rows')
        if sheet is None:
            raise ValueError('Expected Working or Original 108 Rows sheet.')
        name = sheet.attrib['name']
        target = relations[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
        result = []
        for row in ET.fromstring(archive.read(target)).findall('s:sheetData/s:row', NS):
            number = int(row.attrib['r'])
            if number == 1:
                continue
            values = {}
            for cell in row.findall('s:c', NS):
                kind = cell.attrib.get('t')
                value = cell.find('s:v', NS)
                if kind == 'inlineStr':
                    text = ''.join(t.text or '' for t in cell.findall('.//s:t', NS))
                elif value is None:
                    text = ''
                elif kind == 's':
                    text = strings[int(value.text)]
                else:
                    text = value.text or ''
                values[''.join(c for c in cell.attrib['r'] if c.isalpha())] = text
            label, description = values.get('B', ''), values.get('C', '')
            if not label and not description:
                continue
            if not label:
                raise ValueError(f'Populated row {number} has no category label; review manually.')
            result.append({'sheet_name': name, 'sheet_row': number,
                           'original_excel_row': number if original else int(values['A']),
                           'original_label': label, 'original_description': description})
        if not result:
            raise ValueError('No populated category rows found.')
        return result
