IMAGE := redis:6
CONTAINER := redis-app-store

run:
	docker run -d \
		--net local-net \
		--name $(CONTAINER) \
		$(IMAGE)


rm:
	docker rm -f $(CONTAINER)
