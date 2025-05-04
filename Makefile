WHISPER_MODEL_PATH ?= $(HOME)/.cache/whisper

.PHONY: download-whisper clean prod

download-whisper:
	@echo "📦 Ensuring Whisper model is installed..."
	@if [ ! -d "$(WHISPER_MODEL_PATH)/models--Systran--faster-whisper-medium" ]; then \
		pip3 install hf_xet && \
		sudo mkdir -p $(WHISPER_MODEL_PATH) && \
		sudo chown -R $$(whoami):$$(whoami) $(WHISPER_MODEL_PATH) && \
		sudo chmod -R u+w $(WHISPER_MODEL_PATH) && \
		python3 -c "from faster_whisper import WhisperModel; WhisperModel('medium', compute_type='int8', download_root='$(WHISPER_MODEL_PATH)')"; \
	else \
		echo "✅ Whisper model already present at $(WHISPER_MODEL_PATH)/models--Systran--faster-whisper-medium"; \
	fi

clean:
	@echo "🧹 Cleaning Docker containers and volumes..."
	docker compose down --volumes
	docker system prune -f

prod: download-whisper clean
	@echo "🚀 Building and starting production..."
	docker compose -f compose.yaml up --build -d

down:
	docker compose down

up: download-whisper
	docker compose -f compose.yaml up --build -d