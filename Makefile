NAME := foremanctl
VERSION := $(shell cat VERSION)
REQUIREMENTS_YML := $(firstword $(wildcard src/requirements-lock.yml src/requirements.yml))

dist: $(NAME)-$(VERSION).tar.gz

$(NAME)-$(VERSION).tar.gz: build/collections/foremanctl
	git archive --prefix $(NAME)-$(VERSION)/ --output $(NAME)-$(VERSION).tar HEAD
	tar --append --file $(NAME)-$(VERSION).tar --transform='s#^#$(NAME)-$(VERSION)/#' build/collections/foremanctl
	gzip $(NAME)-$(VERSION).tar


build/collections/foremanctl:
	ANSIBLE_COLLECTIONS_PATH=$@ ANSIBLE_COLLECTIONS_SCAN_SYS_PATH=false ansible-galaxy install -r $(REQUIREMENTS_YML)
