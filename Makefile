IMAGE := tornado_app_proxy
CNT := app-proxy
NETWORK := local-net


build:
	DOCKERBUILDKIT=1 docker build -t $(IMAGE) .

run:
	docker run -d \
		--name $(CNT) \
		--net $(NETWORK) \
		-v /var/run/docker.sock:/var/run/docker.sock \
		$(IMAGE) python3 main.py
