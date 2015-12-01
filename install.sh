#!/bin/bash
BASE_ETC_DEFAULT=etc/default
ROOT_ETC_DEFAULT=/$BASE_ETC
for x in $BASE_ETC_DEFAULT/*; do
    if [[ ! -e /$x ]]; then
        cp $x $ROOT_ETC_DEFAULT
    fi
done
chown pi:pi $ROOT_ETC_DEFAULT/raspimon_auth
chmod 600 $ROOT_ETC_DEFAULT/raspimon_auth
echo "Remember to configure $ROOT_ETC_DEFAULT/raspimon_auth with your MongoDB credentials"



BASE_HOSTS=etc/hosts
ROOT_HOSTS=/$BASE_HOSTS
SERVER_NAME=$(cat $BASE_HOSTS | cut -d' ' -f 2)
if ! grep -Fxq "$SERVER_NAME" $ROOT_HOSTS
then
    cat etc/hosts >> /etc/hosts
fi
echo "Remember to write your raspimondbserver IP at $ROOT_HOSTS"



BASE_MAIL_CREDENTIALS=etc/mail_credentials.json
ROOT_MAIL_CREDENTIALS=/$BASE_MAIL_CREDENTIALS
if [[ ! -e $ROOT_MAIL_CREDENTIALS ]]; then
    cp $BASE_MAIL_CREDENTIALS $ROOT_MAIL_CREDENTIALS
    chown pi:pi $ROOT_MAIL_CREDENTIALS
    chmod 600 $ROOT_MAIL_CREDENTIALS
fi
echo "Remember to configure your mail crendentials at $ROOT_MAIL_CREDENTIALS"



BASE_RASPIMON_SERVICE=etc/systemd/system/raspimon.service
ROOT_RASPIMON_SERVICE=/$BASE_RASPIMON_SERVICE
if [[ ! -e $ROOT_RASPIMON_SERVICE ]]; then
    cp $BASE_RASPIMON_SERVICE $ROOT_RASPIMON_SERVICE
    systemctl daemon-reload
    systemctl enable raspimon
fi
