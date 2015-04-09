PYTHON_SRC = 	${HOME}/download/Python-2.3.4

MKHOWTO =	$(PYTHON_SRC)/Doc/tools/mkhowto

.PHONY: html

PAPER =		a4

DOCFILES = blobstore.tex copyright.tex installation.tex soomarray.tex \
	storage.tex soom.tex soomfunc.tex

FIGURES = storage.pdf

all:	pdf

pdf:	$(DOCFILES) $(FIGURES)
	$(MKHOWTO) --pdf --$(PAPER) soom.tex

ps:	pdf
	acroread -toPostScript -size $(PAPER) -fast -level2 -pairs soom.pdf soom.ps

booklet: ps
	cat soom.ps | psbook | psnup -2 | pstumble > soom-booklet.ps

html:	$(DOCFILES) $(FIGURES)
	$(MKHOWTO) --html soom.tex
	mkdir -p soom/icons
	cp $(PYTHON_SRC)/Doc/html/icons/* soom/icons/
	rm soom/soom.how
# the iconserver option of mkhowto is broken since it writes
# it to the end if the init_file where they aren't useful anymore,
# so we work around it:
	for f in `find soom`; do \
	  cat $$f | sed s/\.\.\\/icons/icons/g > $${f}2; \
	  mv $${f}2 $$f; \
	done
	rm soom/soom2
	rm soom/icons/icons2

# convert .dia images to .eps and then to .pdf
%.pdf: %.dia
	dia --nosplash --export-to-format=eps-builtin \
		--export=$(subst .dia,.eps,$<) $<
	epstopdf $(subst .dia,.eps,$<)

clean:
	rm -f *~ *.aux *.idx *.ilg *.ind *.log *.toc *.bkm *.syn *.pla api.tex

# HTML in the doc directory
dist: html
	rm -rf ../doc
	mv soom ../doc
