
PYTHON = python
YAPPSDIR = ../yapps2

.PHONY: soomparse
.DELETE_ON_ERROR:

soomparse: soomparse.py yappsrt.py

# create the soomparse.py module to parse DatasetFilter expressions
soomparse.py:	soomparse.g $(YAPPSDIR)/yapps2.py $(YAPPSDIR)/yappsrt.py
	$(PYTHON) $(YAPPSDIR)/yapps2.py soomparse.g

# Merge yapps2 LICENSE into yappsrt.py source
yappsrt.py: $(YAPPSDIR)/yappsrt.py $(YAPPSDIR)/LICENSE
	(sed -e '/^$$/q' $(YAPPSDIR)/yappsrt.py && \
	 echo '# Copyright 2004 Amit J. Patel' && \
	 echo '# see: http://theory.standford.edu/~amitp/Yapps/' && \
	 echo '#' && \
	 sed -e 's/^/# /' $(YAPPSDIR)/LICENSE && \
	 sed -ne '/^$$/,$$p' $(YAPPSDIR)/yappsrt.py) > $@

clean:
	rm -f *.pyc soomparse.py

