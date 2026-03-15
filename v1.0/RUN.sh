docker build -t urbancompasspony/meteo .

docker run -d --name meteo \
--network meteo-macvlan \
--ip 192.168.1.50 \
-v meteo-dados:/dados meteo

MULTIARCH!

docker buildx create --name mybuilder
docker buildx use mybuilder
docker login

docker buildx build --push --platform linux/amd64,linux/arm64 --tag urbancompasspony/meteo .
