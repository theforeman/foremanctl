NAME := foremanctl
VERSION := $(shell git describe)
REQUIREMENTS_YML := $(firstword $(wildcard src/requirements-lock.yml src/requirements.yml))

dist: $(NAME)-$(VERSION).tar.gz

$(NAME)-$(VERSION).tar.gz: build/collections/foremanctl build/collections/forge
	git archive --prefix $(NAME)-$(VERSION)/ --output $(NAME)-$(VERSION).tar HEAD
	tar --append --file $(NAME)-$(VERSION).tar --transform='s#^#$(NAME)-$(VERSION)/#' --exclude='build/collections/foremanctl/ansible_collections/*/*/tests/*' build/collections/foremanctl
	tar --append --file $(NAME)-$(VERSION).tar --transform='s#^#$(NAME)-$(VERSION)/#' --exclude='build/collections/forge/ansible_collections/*/*/tests/*' build/collections/forge
	gzip $(NAME)-$(VERSION).tar

build/collections/foremanctl: $(REQUIREMENTS_YML)
	ANSIBLE_COLLECTIONS_PATH=$@ ANSIBLE_COLLECTIONS_SCAN_SYS_PATH=false ansible-galaxy install -r $(REQUIREMENTS_YML)

build/collections/forge: development/requirements.yml
	ANSIBLE_COLLECTIONS_PATH=$@ ANSIBLE_COLLECTIONS_SCAN_SYS_PATH=false ansible-galaxy install -r development/requirements.yml

clean-var:
	rm -rf .var
