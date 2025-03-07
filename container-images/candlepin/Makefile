IMAGE_NAME=quay.io/ehelms/candlepin
IMAGE_TAG=4.4.14

build:
	podman build -t ${IMAGE_NAME}:${IMAGE_TAG} .

push:
	podman push ${IMAGE_NAME}:${IMAGE_TAG}
