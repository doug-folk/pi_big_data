FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
COPY style.css /usr/share/nginx/html/style.css
COPY main.js /usr/share/nginx/html/main.js
COPY images /usr/share/nginx/html/images

# Include any favicon or static assets from public if present
COPY public /usr/share/nginx/html/public
