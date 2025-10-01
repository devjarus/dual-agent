.PHONY: setup start stop dev test clean health logs

setup:
	@./scripts/setup.sh

start:
	@./scripts/start.sh

stop:
	@./scripts/stop.sh

dev:
	@./scripts/dev.sh

test:
	@./scripts/test.sh

health:
	@./scripts/health-check.sh

clean:
	@echo "🧹 Cleaning..."
	@rm -rf backend/venv
	@rm -rf frontend/node_modules
	@rm -rf frontend/.next
	@rm -rf data/chroma
	@rm -rf logs/*.log
	@rm -rf logs/*.pid
	@echo "✅ Cleaned"

logs:
	@tail -f logs/*.log
