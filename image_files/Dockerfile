FROM BASE-IMAGE-PLACE-HOLDER

LABEL com.ibm.si.app.origin=SDK

ARG APP_USER_ID
ARG APP_GROUP_ID
ARG APP_USER_NAME=appuser
ARG APP_GROUP_NAME=appuser

ENV APP_ROOT /opt/app-root
ENV APP_USER_ID $APP_USER_ID
ENV APP_GROUP_ID $APP_GROUP_ID
ENV PATH $APP_ROOT/bin:$PATH

COPY / $APP_ROOT

RUN groupadd -o -g $APP_GROUP_ID $APP_GROUP_NAME && \
useradd -l -u $APP_USER_ID -g $APP_GROUP_ID $APP_USER_NAME && \
mkdir -p /etc/supervisord.d && \
if [ -f $APP_ROOT/init/supervisord.conf ]; then mv $APP_ROOT/init/supervisord.conf /etc; fi && \
rm -rf $APP_ROOT/init/* && \
if [ -d $APP_ROOT/bin ]; then chmod -R 755 $APP_ROOT/bin; fi && \
if [ -d $APP_ROOT/container/build ]; then chmod -R 755 $APP_ROOT/container/build; fi && \
if [ -d $APP_ROOT/container/run ]; then chmod -R 755 $APP_ROOT/container/run; fi && \
if [ -d $APP_ROOT/container/clean ]; then chmod -R 755 $APP_ROOT/container/clean; fi && \
if [ -d $APP_ROOT/container/service ]; then chmod -R 755 $APP_ROOT/container/service; fi && \
if [ -d $APP_ROOT/startup.d ]; then chmod -R 755 $APP_ROOT/startup.d; fi && \
if [ -d $APP_ROOT/container/conf/supervisord.d ]; then mv $APP_ROOT/container/conf/supervisord.d/*.conf /etc/supervisord.d; fi && \
if [ -d /etc/supervisord.d ]; then chmod -R 755 /etc/supervisord.d ; fi && \
echo -e "appuser ALL=(ALL) NOPASSWD:ALL\n" >> /etc/sudoers && \
visudo -cf /etc/sudoers

DEPENDENCIES-PLACE-HOLDER

INIT-PLACE-HOLDER

USER $APP_USER_NAME
ENTRYPOINT ["sh", "/opt/app-root/bin/start.sh"]
