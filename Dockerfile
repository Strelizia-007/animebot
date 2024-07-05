FROM python:3.10-slim-buster

RUN mkdir /bot && chmod 777 /bot
WORKDIR /bot

RUN apt-get update && apt-get upgrade -y
RUN apt-get install git wget pv jq python3-dev mediainfo gcc libsm6 libxext6 libfontconfig1 libxrender1 libgl1-mesa-glx -y

COPY --from=mwader/static-ffmpeg:6.1 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:6.1 /ffprobe /usr/local/bin/

COPY . .
RUN pip3 install --no-cache-dir -U -r requirements.txt

CMD ["bash","run.sh"]
