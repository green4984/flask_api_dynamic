all:


test:
	@python run_test.py

clean:
	@find . -name "*.pyc" -exec rm {} +
