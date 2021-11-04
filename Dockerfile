FROM continuumio/anaconda3

RUN apt-get update && apt-get install -y 

RUN apt-get install libgomp1 -y 

RUN /opt/conda/bin/conda update -n base -c defaults conda && \
    /opt/conda/bin/conda install python=3.6 && \
    /opt/conda/bin/conda install anaconda-client && \
    /opt/conda/bin/conda install jupyter -y && \
    /opt/conda/bin/conda install --channel https://conda.anaconda.org/menpo opencv3 -y && \
    /opt/conda/bin/conda install numpy pandas scikit-learn matplotlib seaborn pyyaml h5py keras -y && \
    /opt/conda/bin/conda upgrade dask \

WORKDIR /home/alphapept/
COPY . .

RUN conda install requirements.txt

RUN cp  /usr/local/lib/python3.8/dist-packages/alphapept/ext/bruker/FF/linux64/libtbb.so.2 /usr/lib/libtbb.so.2
RUN chmod 555 -R  /usr/local/lib/python3.8/dist-packages/alphapept/ext/bruker/FF/linux64/uff-cmdline2
CMD ["bash"]
