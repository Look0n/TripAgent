FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY css/ /usr/share/nginx/html/css/

COPY templates/search.html /usr/share/nginx/html/search.html
COPY templates/manage.html /usr/share/nginx/html/manage.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
