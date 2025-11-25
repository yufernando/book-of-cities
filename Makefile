.PHONY: docker shell token tests run concatenate
docker:
	@docker run -d --rm -p 8888:8888 -v "/Users/fer/Documents/Aretian/book-of-cities":"/home/jovyan/work" -e JUPYTER_ENABLE_LAB=yes -e GRANT_SUDO=yes --user root --name cities yufernando/jupyterlab
	@sleep 2
	@/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --new-window --app="http://localhost:8888" > /dev/null
	@$(MAKE) token

shell:
	@docker exec -it cities zsh

token:
	@echo "Token:"
	@docker exec cities jupyter server list 2>&1 | grep -oE 'token=[a-zA-Z0-9]+' | cut -d'=' -f2

tests:
	pytest morpho/tests

run:
	docker exec -it -w /home/jovyan/work/code cities python run.py $(cmd)

concatenate:
	python concatenate.py
