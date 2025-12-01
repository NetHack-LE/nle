# Docker images for NLE

This directory -- i.e., `docker/` -- contains some dockerfiles to 
create NLE images.  They are based on the NVDIA Ubuntu images and
so include CUDA support. However, you don't need any GPUs to make
and run containers from the images.

Docker now provides multi-architecture support so whether you are
using an x86_64, amd64 or arm64 CPU you can use the same image to 
run an NLE container.

# Building Images Locally

To build and run an image (e.g. `Dockerfile-jammy`) for your local 
architecture do:

```bash
$ git clone https://github.com/NetHack-LE/nle
$ cd nle
$ docker build --file docker/Dockerfile-jammy . --tag nle
$ docker run -it --gpus all --rm --name nle nle
# or alternatively if you don't have GPUs
$ docker run -it --name nle nle
```

# Building Multi-Architecture Images

To build an image on your machine that can be deployed on multiple
architectures (e.g. x86_64, amd64 or arm64), use the following docker 
command. Run it from the nle directory.

```bash
$ docker buildx build --platform linux/amd64,linux/arm64 -t nle -f docker/Dockerfile-jammy .
```

The run instructions are as before. Docker will load the correct
binaries for the architecture you are running the container on.
