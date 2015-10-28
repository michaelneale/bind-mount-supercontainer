docker build -t volume . 
docker run -v /var/run/docker.sock:/var/run/docker.sock -v /usr/bin/docker:/usr/bin/docker --privileged -it -v /:/media/host volume 
