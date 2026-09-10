.PHONY: default menu help install prereqs up down restart status logs healthcheck test-load test-alert clean clean-disk enable-autoclean wizard scan monitor-api telegram scale-node view nginx purge destroy

AURA ?= ./aura

default: menu

menu:
	$(AURA) menu

help:
	$(AURA) help

install:
	bash install.sh

prereqs:
	bash scripts/install_prereqs.sh

up:
	$(AURA) up

down:
	$(AURA) down

restart:
	$(AURA) restart

status:
	$(AURA) status

view:
	$(AURA) view

logs:
	$(AURA) logs

healthcheck:
	$(AURA) health

scan:
	$(AURA) scan

monitor-api:
	$(AURA) monitor-api

nginx:
	$(AURA) nginx

telegram:
	$(AURA) telegram

scale-node:
	$(AURA) scale-node

test-load:
	$(AURA) test-load

test-alert:
	$(AURA) test-alert

clean-disk:
	$(AURA) clean-disk

enable-autoclean:
	bash scripts/auto_cleaner.sh --install-cron

clean:
	$(AURA) down -v

purge:
	$(AURA) purge

destroy:
	$(AURA) destroy -y
