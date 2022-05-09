docker login
docker buildx build --push --platform linux/armhf,linux/amd64 -t nighmared/pidell:testing .
#docker buildx build --push --platform linux/armhf -t nighmared/pidell:latest_arm .
