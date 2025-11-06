SHELL := /bin/bash

export:
	docker compose run --rm ml python ml/scripts/1_export_es_to_jsonl.py

prepare:
	docker compose run --rm ml python ml/scripts/2_prepare_dataset.py

split:
	docker compose run --rm ml python ml/scripts/3_split_dataset.py

train:
	docker compose run --rm ml python ml/scripts/4_train_baseline.py

predict:
	docker compose run --rm ml python ml/scripts/5_predict.py "$(TEXT)"
