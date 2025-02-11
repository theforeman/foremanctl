IMAGE_NAME=quay.io/evgeni/foreman-proxy-rpm
IMAGE_TAG=nightly

build:
	podman build -t ${IMAGE_NAME}:${IMAGE_TAG} .

push:
	podman push ${IMAGE_NAME}:${IMAGE_TAG}
