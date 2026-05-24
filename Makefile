.PHONY: validate-agentic-docs compile-streamlit test-streamlit lint-streamlit validate-streamlit docker-streamlit validate-all

validate-agentic-docs:
	@echo "Validate required agentic documentation manually against docs/specs/customer-experience-streamlit-azure.validation.md"

compile-streamlit:
	python -m compileall streamlit_app

test-streamlit:
	python -m pytest streamlit_app/tests

lint-streamlit:
	ruff check streamlit_app

validate-streamlit: compile-streamlit test-streamlit lint-streamlit

docker-streamlit:
	docker build -f streamlit_app/Dockerfile .

validate-all: validate-agentic-docs validate-streamlit
