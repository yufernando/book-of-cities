.PHONY: jupyter
jupyter:
	@docker run -d --rm -p 8888:8888 -v "/Users/fer/aretian-drive/Research/Book of Cities":"/home/jovyan/work" -e JUPYTER_ENABLE_LAB=yes -e GRANT_SUDO=yes --user root --name cities yufernando/jupyterlab:geo
	@sleep 2
	@/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --new-window --app="http://localhost:8888" > /dev/null
	@docker exec cities jupyter server list

shell:
	@docker exec -it cities zsh
