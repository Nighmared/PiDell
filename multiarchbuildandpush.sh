docker login
docker buildx build --push --platform linux/armhf,linux/amd64 -t nighmared/pidell:latest .
