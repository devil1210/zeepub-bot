# pgsentinel build based on pgvector/pgvector:17-pg17 (Debian-based)
FROM pgvector/pgvector:17-pg17 AS builder

# Install build dependencies for Debian (pgvector is based on debian)
RUN apt-get update && apt-get install -y \
    git \
    make \
    gcc \
    postgresql-server-dev-17 \
    libutil-dev \
    libssl-dev \
    zlib1g-dev

# Clone and build pgsentinel
WORKDIR /tmp
RUN git clone https://github.com/pgsentinel/pgsentinel.git && \
    cd pgsentinel/src && \
    make && \
    make install

# Final image
FROM pgvector/pgvector:17-pg17

# Copy the compiled extension files from builder
# Debian-based postgres paths
COPY --from=builder /usr/lib/postgresql/17/lib/pgsentinel.so /usr/lib/postgresql/17/lib/
COPY --from=builder /usr/share/postgresql/17/extension/pgsentinel* /usr/share/postgresql/17/extension/

# Extension requires pg_stat_statements which is already in the official image
