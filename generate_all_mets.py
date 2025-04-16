import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from collections import defaultdict

# === FUNKCJA: generuj jeden plik METS dla folderu ===
def generate_mets_for_folder(folder: Path):
    grouped_files = defaultdict(dict)
    supported_ext = {"pdf", "tiff", "tif", "jp2", "j2k", "xml"}

    for file in sorted(folder.iterdir()):
        if not file.is_file():
            continue
        name, ext = os.path.splitext(file.name)
        ext = ext.lstrip(".").lower()
        if ext not in supported_ext:
            continue
        key = re.sub(r"[ _]?1$", "", name)
        grouped_files[key][ext] = file.name

    if not grouped_files:
        print(f"⚠️  Pomijam pusty lub niekompletny folder: {folder.name}")
        return

    mets = ET.Element("mets", {
        "xmlns": "http://www.loc.gov/METS/",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd",
        "ID": folder.name
    })

    ET.SubElement(mets, "metsHdr", CREATEDATE="2025-04-07T00:00:00")

    # dmdSec z pierwszym plikiem ALTO
    dmdSec = ET.SubElement(mets, "dmdSec", ID="dmd1")
    mdWrap = ET.SubElement(dmdSec, "mdWrap", MDTYPE="OTHER", OTHERMDTYPE="ALTO")
    xmlData = ET.SubElement(mdWrap, "xmlData")
    for base in grouped_files:
        if "xml" in grouped_files[base]:
            ET.SubElement(xmlData, "altoFile").text = grouped_files[base]["xml"]
            break

    # FileSec
    fileSec = ET.SubElement(mets, "fileSec")
    fileGrp = ET.SubElement(fileSec, "fileGrp", USE="master")
    mimetypes = {
        "pdf": "application/pdf",
        "tif": "image/tiff",
        "tiff": "image/tiff",
        "j2k": "image/jp2",
        "jp2": "image/jp2",
        "xml": "text/xml"
    }

    for base, files in grouped_files.items():
        for ext, fname in files.items():
            file_id = f"f_{base.replace(' ', '_')}_{ext}"
            file_el = ET.SubElement(fileGrp, "file", {
                "ID": file_id,
                "MIMETYPE": mimetypes.get(ext, "application/octet-stream")
            })
            ET.SubElement(file_el, "FLocat", {
                "LOCTYPE": "URL",
                "xlink:href": fname
            })

    # StructMap
    structMap = ET.SubElement(mets, "structMap", TYPE="physical")
    div_volume = ET.SubElement(structMap, "div", TYPE="volume", LABEL=folder.name)

    for base in sorted(grouped_files):
        page_div = ET.SubElement(div_volume, "div", TYPE="page", LABEL=base)
        for ext in grouped_files[base]:
            file_id = f"f_{base.replace(' ', '_')}_{ext}"
            ET.SubElement(page_div, "fptr", FILEID=file_id)

    # Zapis do pliku
    output_path = folder / f"{folder.name}.mets.xml"
    xml_string = ET.tostring(mets, encoding="utf-8")
    pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    print(f"✅ METS zapisany: {output_path}")

# === GŁÓWNA CZĘŚĆ: skanuj wszystkie podkatalogi ===
base_dir = Path.cwd()

print(f"📁 Skrypt uruchomiony w katalogu nadrzędnym: {base_dir}\n")

for subfolder in sorted(base_dir.iterdir()):
    if subfolder.is_dir():
        generate_mets_for_folder(subfolder)

print("\n🏁 Zakończono generowanie plików METS.")