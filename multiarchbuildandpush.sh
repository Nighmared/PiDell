docker login
#docker buildx create --name pidell_builder
docker buildx use pidell_builder
docker buildx inspect --bootstrap
docker buildx build --push --platform linux/arm/v7,linux/amd64 -t nighmared/pidell:latest .
