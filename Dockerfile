# Use the official Debian 12.7 base image
FROM python:3.11-slim-trixie

# Set the default shell and working directory
WORKDIR /ProxyAgent

# Since python dependencies (pip) are updated more often, we install them separately
COPY requirements.txt /ProxyAgent
RUN pip install -r requirements.txt

# Now that everything is downloaded, we copy the rest of the repository
# This is made this way so that we don't have to download everything every time we update the code
RUN mkdir logs
COPY src src

# Set the entrypoint to the script
ARG CFGFILE
COPY $CFGFILE config/config.json

ARG PUBLIC_NODE_INFO
COPY $PUBLIC_NODE_INFO config/public_node_info.json

CMD [ "python3", "src/proxy_agent/main.py", "config/config.json"]