docker run -d --name=lab4 -p 0:8080 lab4-img:v4
port=$(docker inspect lab4 | jq '.[].NetworkSettings.Ports."8080/tcp"[].HostPort' | sed 's/\"//g')
echo "URL is http://localhost:$port"