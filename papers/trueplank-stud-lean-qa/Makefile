# Optional PDF later. Markdown is the draft of record.
# A TeX engine and pandoc are not required to read or review this paper.
#
# From this directory, when pandoc is installed:
#   pandoc draft/paper.md --metadata-file=draft/header.yaml \
#     --citeproc --bibliography=references.bib -s -o draft/paper.pdf
#
# header.yaml repeats the H1 title for pandoc. No Automation in Construction
# or ISPRS class file is included. Do not treat a local PDF as a submission.

.PHONY: pdf note

note:
	@echo "Draft of record: draft/paper.md"
	@echo "Pandoc metadata: draft/header.yaml"
	@echo "Bibliography:    references.bib"
	@echo "PDF is optional. No journal class is bundled."

pdf:
	pandoc draft/paper.md --metadata-file=draft/header.yaml \
		--citeproc --bibliography=references.bib -s -o draft/paper.pdf
