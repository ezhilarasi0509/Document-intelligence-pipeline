.PHONY: setup test data check run-a run-b run-c eval report serve docker
setup:   ; uv sync --extra dev && cp -n .env.example .env || true
test:    ; uv run pytest -q
data:    ; uv run docintel download --n 40
check:   ; uv run docintel inspect-labels
run-a:   ; uv run docintel run --parser pymupdf --run-id pymupdf_groq
run-b:   ; uv run docintel run --parser docling --run-id docling_groq
run-c:   ; uv run docintel run --parser gemini_direct --run-id gemini_direct
eval:    ; for r in pymupdf_groq docling_groq gemini_direct; do [ -d data/predictions/$$r ] && uv run docintel evaluate --run-id $$r; done
report:  ; uv run docintel report
serve:   ; uv run docintel serve
docker:  ; docker build -t docintel . && docker run --rm -p 7860:7860 --env-file .env docintel
