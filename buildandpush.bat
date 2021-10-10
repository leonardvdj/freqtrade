docker build -t freqtrade:develop .
docker buildx build -f docker/Dockerfile.armhf --platform linux/arm64/v8 -t freqtrade:develop .
docker tag freqtrade:develop leonardvdj/freqtrade:develop
docker push leonardvdj/freqtrade:develop


docker build -t leonardvdj/freqtrade:develop_amd64 .
docker push leonardvdj/freqtrade:develop_amd64
docker buildx build -f docker/Dockerfile.armhf --platform linux/arm/v7 -t leonardvdj/freqtrade:develop_armv7 .
docker push leonardvdj/freqtrade:develop_armv7
docker buildx build -f docker/Dockerfile.armhf --platform linux/arm64/v8 -t leonardvdj/freqtrade:develop_arm64v8 .

docker buildx build --push --platform linux/amd64,linux/arm64/v8 -t leonardvdj/freqtrade:develop .