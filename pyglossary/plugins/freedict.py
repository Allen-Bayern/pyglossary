# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.xml_utils import xml_escape
from typing import List, Union, Callable
from lxml import etree as ET
from io import BytesIO

enable = True
format = "FreeDict"
description = "FreeDict (tei)"
extensions = [".tei"]
optionsProp = {
	"resources": BoolOption(),
}
depends = {}

tei = "{http://www.tei-c.org/ns/1.0}"

class Reader(object):
	ns = {
		None: "http://www.tei-c.org/ns/1.0",
	}

	def to_string(self, el):
		return ET.tostring(el, method="html", pretty_print=True).decode("utf-8")

	def make_list(
		self,
		hf: ET.htmlfile,
		input_elements: List[ET.Element],
		processor: Callable,
		single_prefix=None,
		skip_single=True
	):
		""" Wrap elements into <ol> if more than one element """
		if len(input_elements) == 0:
			return

		if len(input_elements) == 1:
			hf.write(single_prefix)
			processor(hf, input_elements[0])
			return

		with hf.element("ol"):
			for el in input_elements:
				with hf.element("li"):
					processor(hf, el)

	def process_sense(self, hf: ET.htmlfile, sense: ET.Element):
		# translations
		hf.write(", ".join(
			el.text
			for el in sense.findall("cit/quote", self.ns)
			if el.text is not None
		))

		self.make_list(
			hf,
			sense.findall("sense/def", self.ns),
			lambda hf, el: hf.write(el.text),
			single_prefix=" — ",
		)

	def get_entry_html(self, entry):
		keywords = []
		f = BytesIO()
		with ET.htmlfile(f) as hf:
			with hf.element("div"):
				for form in entry.findall("form/orth", self.ns):
					keywords.append(form.text)
					with hf.element("b"):
						hf.write(form.text)
				hf.write(" ")
				for pos in entry.findall("gramGrp/pos", self.ns):
					with hf.element("i"):
						hf.write(pos.text)
				hf.write(ET.Element("br"))
				hf.write("\n")

				self.make_list(
					hf,
					entry.findall("sense", self.ns),
					self.process_sense,
				)

		return keywords, f.getvalue().decode("utf-8")

	def set_word_count(self, header):
		extent_elem = header.find(".//extent", self.ns)
		if extent_elem is None:
			log.warn(
				"did not find 'extent' tag in metedata"
				", progress bar will not word"
			)
			return
		extent = extent_elem.text
		if not extent.endswith(" headwords"):
			log.warn(f"unexpected extent={extent}")
			return
		try:
			self._wordCount = int(extent.split(" ")[0])
		except Exception:
			log.exception(f"unexpected extent={extent}")

	def strip_tag_p_elem(self, elem: "ET.Element") -> str:
		text = self.to_string(elem).strip()
		prefix = '<p xmlns="http://www.tei-c.org/ns/1.0">'
		if text.startswith(prefix) and text.endswith("</p>"):
			text = text[len(prefix):-4].strip()
		elif text.startswith("<p>") and text.endswith("</p>"):
			text = text[3:-4].strip()
		return text

	def strip_tag_p(self, elems: List["ET.Element"]) -> str:
		lines = []
		for elem in elems:
			for line in self.strip_tag_p_elem(elem).split("\n"):
				line = line.strip()
				if not line:
					continue
				lines.append(line)
		return "\n".join(lines)

	def set_copyright(self, header):
		elems = header.findall(".//availability//p", self.ns)
		if not elems:
			log.warn("did not find copyright")
			return
		copyright = self.strip_tag_p(elems)
		self._glos.setInfo("copyright", copyright)
		log.info(f"Copyright: {copyright!r}")

	def set_publisher(self, header):
		elem = header.find(".//publisher", self.ns)
		if elem is None:
			log.warn("did not find publisher (author)")
			return
		self._glos.setInfo("author", elem.text)

	def set_publication_date(self, header):
		elem = header.find(".//publicationStmt/date", self.ns)
		if elem is None:
			return
		self._glos.setInfo("creationTime", elem.text)

	def set_description(self, header):
		elems = []
		for tag in ("sourceDesc", "projectDesc"):
			elems += header.findall(f".//{tag}//p", self.ns)
		description = self.strip_tag_p(elems)
		if description:
			self._glos.setInfo("description", description)
			log.info(
				"------------ Description: ------------\n"
				f"{description}\n"
				"--------------------------------------"
			)

	def set_metadata(self, header):
		self.set_word_count(header)
		self._glos.setInfo("title", header.find(".//title", self.ns).text)
		self._glos.setInfo("edition", header.find(".//edition", self.ns).text)

		self.set_copyright(header)
		self.set_publisher(header)
		self.set_publication_date(header)
		self.set_description(header)

	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._wordCount = 0

	def __len__(self) -> int:
		return self._wordCount

	def close(self) -> None:
		pass

	def open(self, filename: str):
		self._filename = filename

		context = ET.iterparse(filename, events=("end",))
		for action, elem in context:
			if elem.tag == f"{tei}teiHeader":
				self.set_metadata(elem)
				return

	def __iter__(self) -> Iterator[BaseEntry]:
		context = ET.iterparse(self._filename, events=("end",))
		for action, elem in context:
			if elem.tag == f"{tei}entry":
				words, defi = self.get_entry_html(elem)
				yield self._glos.newEntry(words, defi)
				# clean up preceding siblings to save memory
				while elem.getprevious() is not None:
					del elem.getparent()[0]



def write(
	glos: GlossaryType,
	filename: str,
	resources: bool = True,
):
	fp = open(filename, "w", encoding="utf-8")
	title = glos.getInfo("title")
	publisher = glos.getInfo("author")
	copyright = glos.getInfo("copyright")
	creationTime = glos.getInfo("creationTime")

	fp.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE TEI.2 PUBLIC "-//TEI P3//DTD Main Document Type//EN"
"/usr/share/sgml/tei-3/tei2.dtd" [
<!ENTITY %% TEI.dictionaries "INCLUDE" > ]>
<tei.2>
<teiHeader>
<fileDesc>
<titleStmt>
	<title>{title}</title>
	<respStmt><resp>converted with</resp><name>PyGlossary</name></respStmt>
</titleStmt>
<publicationStmt>
	<publisher>{publisher}</publisher>
	<availability><p>{copyright}</p></availability>
	<date>{creationTime}</date>
</publicationStmt>
<sourceDesc><p>{filename}</p></sourceDesc>
</fileDesc>
</teiHeader>
<text><body>""")

	for entry in glos:
		if entry.isData():
			if resources:
				entry.save(filename + "_res")
			continue
		word = xml_escape(entry.getWord())
		defi = xml_escape(entry.getDefi())
		fp.write(f"""<entry>
<form><orth>{word}</orth></form>
<trans><tr>{defi}</tr></trans>
</entry>""")
	fp.write("</body></text></tei.2>")
	fp.close()
