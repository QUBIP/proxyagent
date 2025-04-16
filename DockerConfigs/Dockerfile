# Use the official Debian 12.7 base image
# FROM debian:12.7
FROM proxyagent:V1

# Set the default working directory and copy the proxy_agent module
WORKDIR /ProxyAgent
COPY ProxyAgent /ProxyAgent

# Make the script executable
COPY /ProxyAgent/entrypoint.sh /ProxyAgent
RUN chmod +x /ProxyAgent/entrypoint.sh

COPY /ProxyAgent/FullScript.sh /ProxyAgent
# Due to we run an image preinstalled, it is not necessary to rerun the fullscript again.
RUN chmod +x /ProxyAgent/FullScript.sh

COPY /ProxyAgent/requirements.txt /ProxyAgent
COPY /ProxyAgent/ProxyAgent_requirements.txt /ProxyAgent

# Make the entrypoint script executable
# RUN chmod +x /ProxyAgent/entrypoint.sh

# Set the entrypoint to the script
ARG CFGFILE
ENV CFGFILE $CFGFILE
ENTRYPOINT ["/ProxyAgent/entrypoint.sh"]
