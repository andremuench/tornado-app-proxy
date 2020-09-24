FROM openresty/openresty:xenial

EXPOSE 80

RUN apt-get update && apt-get -y install libssl-dev

RUN luarocks install base64
RUN luarocks install luaossl

COPY app-proxy.conf /etc/nginx/conf.d/default.conf
COPY parse_request.lua /usr/local/openresty/lualib/parse_request.lua

