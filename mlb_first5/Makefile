# MLB First-5 — Quick Commands Makefile
# One-click operations for common tasks

.PHONY: help predict confirm sync summary

help:
	@echo "MLB First-5 Betting System — Quick Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make predict     — Run daily predictions"
	@echo "  make confirm     — Check lineup confirmation"
	@echo "  make sync        — Sync paper trading log to Google Sheets"
	@echo "  make summary     — Generate executive summary"
	@echo "  make telegram    — Send today's bets to Telegram"
	@echo "  make status      — Show system status"

predict:
	@echo "🎯 Running daily predictions..."
	/root/mlb-env/bin/python /root/noesis-prediction/mlb_first5/daily_predict.py

confirm:
	@echo "✅ Generating lineup confirmation checklists..."
	/root/mlb-env/bin/python /root/noesis-prediction/mlb_first5/bet_confirmation.py

telegram:
	@echo "📱 Preparing Telegram alerts..."
	@if [ -f /tmp/confirmed_bets.json ]; then \
		/root/mlb-env/bin/python /root/noesis-prediction/mlb_first5/telegram_alerts.py --bet-file /tmp/confirmed_bets.json; \
	else \
		echo "No confirmed bets found. Run 'make predict' first."; \
	fi

sync:
	@echo "📊 Syncing paper trading log to Google Sheets..."
	@echo "This requires: gog auth to be configured"
	@if [ -f /root/noesis-prediction/mlb_first5/PAPER_TRADING_LOG.md ]; then \
		echo "Converting log to CSV..."; \
		grep "^|" /root/noesis-prediction/mlb_first5/PAPER_TRADING_LOG.md | head -20 > /tmp/trades.csv; \
		/root/mlb-env/bin/python /root/noesis-prediction/mlb_first5/sheets_sync.py \
			--file /tmp/trades.csv \
			--sheet "Noesis_MLB_Trades" \
			--tab "Paper_Trading"; \
	else \
		echo "No trading log found."; \
	fi

summary:
	@echo "📄 Generating executive summary..."
	cat /root/noesis-prediction/mlb_first5/MLB_Betting_System_Summary.md

status:
	@echo "📊 System Status"
	@echo "==============="
	@echo "Data files:"
	@ls -lh /root/noesis-prediction/mlb_first5/data/processed/*.csv 2>/dev/null | wc -l | xargs echo "  Processed datasets:"
	@echo ""
	@echo "Scripts ready:"
	@ls /root/noesis-prediction/mlb_first5/*.py 2>/dev/null | wc -l | xargs echo "  Python scripts:"
	@echo ""
	@echo "Virtual env: /root/mlb-env"
	@echo "Telegram: Configured ✅"
	@echo "Google: Pending auth setup"
