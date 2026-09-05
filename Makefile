.PHONY: default menu help up down restart status logs healthcheck test-load test-alert clean wizard scan add-site telegram scale-node

default: menu

menu:
	python3 scripts/control_center.py

help:
	@echo "NextAura VPS Monitoring & Security Commands:"
	@echo "  make menu        - Launch interactive Master Control Center (Default)"
	@echo "  make wizard      - Run interactive configuration wizard (Step 0)"
	@echo "  make scan        - Scan host for pre-existing services & port conflicts"
	@echo "  make add-site    - Auto-generate Nginx proxy config for your custom service"
	@echo "  make telegram    - 1-Step Telegram alert setup (Token only from @BotFather)"
	@echo "  make scale-node  - Onboard a remote VPS worker node via SSH"
	@echo "  make up          - Start the complete observability stack"
	@echo "  make down        - Stop the observability stack"
	@echo "  make restart     - Restart all containers"
	@echo "  make status      - Check container status"
	@echo "  make logs        - Tail logs from all containers"
	@echo "  make healthcheck - Run end-to-end diagnostic checks"
	@echo "  make test-load   - Run synthetic traffic load test"
	@echo "  make test-alert  - Trigger a test alert to Alertmanager & Telegram"
	@echo "  make clean       - Stop stack and remove volumes"

scan:
	python3 scripts/scanner.py

add-site:
	python3 scripts/nginx_site_generator.py

telegram:
	python3 scripts/telegram_setup.py

scale-node:
	python3 scripts/scale_node.py

wizard:
	python3 scripts/wizard.py






up:
	docker-compose up -d --build

down:
	docker-compose down

restart:
	docker-compose restart

status:
	docker-compose ps

logs:
	docker-compose logs -f --tail=100

healthcheck:
	bash scripts/healthcheck.sh

test-load:
	python3 scripts/load_test.py --duration 30 --rate 20 --simulate-attacks

test-alert:
	bash scripts/test_alert.sh

clean:
	docker-compose down -v
