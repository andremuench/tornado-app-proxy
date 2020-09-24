IMAGE := lua-proxy
NETWORK := local-net

build:
	DOCKERBUILD_KIT=1 docker build -t $(IMAGE) .

run:
	docker run -d \
		-p 80:80 \
		--net $(NETWORK) \
		$(IMAGE)
