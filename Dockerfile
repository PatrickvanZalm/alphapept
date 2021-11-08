FROM ubuntu:20.04

#Set up location. One of packages requires it
ENV DEBIAN_FRONTEND=noninteractive 


RUN apt-get update \
  && apt-get install -y \
    ca-certificates \
    gnupg \
  && rm -rf /var/lib/apt/lists/*

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
  && echo "deb https://download.mono-project.com/repo/ubuntu stable-bionic main" > /etc/apt/sources.list.d/mono-official-stable.list

RUN apt-get update \
  && apt-get install -y \
    mono-devel \
    nuget \
    tzdata \
  && rm -rf /var/lib/apt/lists/*

RUN \
	apt-get update && \
	apt-get -y upgrade && \
	apt-get install -y libgomp1 && \
	apt-get install -y python3.8 && \
	apt-get install -y python3-pip && \
    apt-get install build-essential -y 

#Set workdir, copy all from git into container
WORKDIR /home/alphapept/
COPY . .

#upgrade pip
RUN pip install pip --upgrade
RUN pip install setuptools --upgrade 

# Set up .NET stuff...
RUN pip install pycparser \
  && pip install pythonnet==2.5.2

#install packages
RUN pip install -r requirements.txt

#copy some stuff to libgompfiles
#RUN cp /usr/local/lib/python3.8/dist-packages/alphapept/ext/bruker/FF/linux64/libtbb.so.2 /usr/lib/libtbb.so.2

#Give rights
#RUN chmod 555 -R  /usr/local/lib/python3.8/dist-packages/alphapept/ext/bruker/FF/linux64/uff-cmdline2

#make container accessible
CMD ["bash"]