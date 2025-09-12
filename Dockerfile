# Use the official Debian 12.7 base image
FROM debian:12.7

# Set the default shell and working directory
WORKDIR /ProxyAgent
SHELL ["/bin/bash", "-c"] 

# Install all system packages (apt)
COPY scripts/docker/setup_container.sh /ProxyAgent
RUN chmod +x /ProxyAgent/setup_container.sh
RUN /ProxyAgent/setup_container.sh

# Since python dependencies (pip) are updated more often, we install them separately
COPY scripts/docker/setup_requirements.sh /ProxyAgent
COPY requirements.txt /ProxyAgent
RUN chmod +x /ProxyAgent/setup_requirements.sh
RUN /ProxyAgent/setup_requirements.sh

# Now that everything is downloaded, we copy the rest of the repository
# This is made this way so that we don't have to download everything every time we update the code
COPY . /ProxyAgent

# Make the entrypoint executable
RUN chmod +x /ProxyAgent/scripts/docker/entrypoint.sh

# Set the entrypoint to the script
ARG CFGFILE
ENV CFGFILE=$CFGFILE
ENTRYPOINT ["/ProxyAgent/scripts/docker/entrypoint.sh"]
