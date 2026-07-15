# ==========================================
# STAGE 1: Build the Angular application
# ==========================================
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files first to leverage Docker layer caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest of the application code
COPY . .

# Build the app for production (adjust the output path if necessary)
RUN npm run build -- --configuration production

# ==========================================
# STAGE 2: Serve using Nginx
# ==========================================
FROM nginx:stable-alpine

# Copy the built files from the build stage to Nginx's web directory
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

# Copy a custom Nginx configuration (we will create this in Step 2)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3015

CMD ["nginx", "-g", "daemon off;"]