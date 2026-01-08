# Stage 1: Build the React Application
FROM node:18-alpine as build

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# Stage 2: Serve with Apache
FROM httpd:2.4-alpine

# Copy built assets from builder stage
COPY --from=build /app/dist/ /usr/local/apache2/htdocs/

# Copy .htaccess for SPA routing
# Ensure AllowOverride All is set in your httpd.conf or via sed if needed.
# For simplicity in alpine httpd, we often replace the config or use a custom one.
# But placing .htaccess is the first step.
COPY --from=build /app/public/.htaccess /usr/local/apache2/htdocs/.htaccess

# Enable mod_rewrite in Apache configuration
RUN sed -i \
    -e 's/#LoadModule rewrite_module/LoadModule rewrite_module/' \
    -e 's/AllowOverride None/AllowOverride All/g' \
    /usr/local/apache2/conf/httpd.conf

EXPOSE 80
